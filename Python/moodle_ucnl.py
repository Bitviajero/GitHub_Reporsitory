"""Aplicacion local para exportar cursos y recursos de Moodle UCNL."""

from __future__ import annotations

import json
import logging
import mimetypes
import os
import re
import secrets
import shutil
import tempfile
import zipfile
from collections import deque
from dataclasses import asdict, dataclass, field
from email.message import Message
from pathlib import Path
from threading import Event, Lock, Thread
from typing import Callable
from unicodedata import combining, normalize
from urllib.parse import parse_qs, quote, unquote, urljoin, urlsplit

import requests
from bs4 import BeautifulSoup
from bs4.element import Tag
from flask import (
    Flask,
    Response,
    abort,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)


BASE_URL = "https://licenciatura.ucnl.edu.mx"
COURSES_URL = f"{BASE_URL}/my/courses.php"
PROGRAM_PAGE_ID = "809871"
MAX_ACTIVITY_PAGES_PER_COURSE = 20
MOODLE_ACTIVITY_PATH = re.compile(
    r"^/mod/[a-zA-Z0-9_-]+/view\.php$"
)
FILE_EXTENSIONS = {
    ".7z", ".avi", ".c", ".class", ".cpp", ".cs", ".csv", ".doc", ".docx",
    ".gif", ".go", ".gz", ".h", ".html", ".ipynb", ".java", ".jpeg", ".jpg",
    ".js", ".json", ".kt", ".m4v", ".mkv", ".mov", ".mp3", ".mp4", ".mpeg",
    ".mpg", ".odp", ".ods", ".odt", ".pdf", ".php", ".png", ".ppt", ".pptx",
    ".py", ".r", ".rar", ".rb", ".rtf", ".sh", ".sql", ".svg", ".swift",
    ".tar", ".ts", ".tsx", ".txt", ".wav", ".webm", ".xls", ".xlsx", ".xml",
    ".zip",
}
VIDEO_EXTENSIONS = {".avi", ".m4v", ".mkv", ".mov", ".mp4", ".mpeg", ".mpg", ".webm"}
TUTOR_PATTERN = re.compile(
    r"(?:tutor(?:a)?|docente|profesor(?:a)?|teacher)\s*[:\-]\s*([^\n|;]+)",
    re.IGNORECASE,
)
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

app = Flask(__name__)


def flask_secret_key() -> bytes:
    configured = os.environ.get("MOODLE_UCNL_SECRET_KEY")
    if configured:
        return configured.encode("utf-8")
    local_app_data_value = os.environ.get("LOCALAPPDATA")
    local_app_data = (
        Path(local_app_data_value)
        if local_app_data_value
        else Path.home() / "AppData" / "Local"
    )
    key_path = local_app_data / "UCNLMoodleExporter" / "session.key"
    key_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with key_path.open("xb") as key_file:
            key_file.write(secrets.token_bytes(32))
    except FileExistsError:
        pass
    return key_path.read_bytes()


app.secret_key = flask_secret_key()
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    MAX_CONTENT_LENGTH=16 * 1024,
)

# Moodle cookies live only in memory and are removed when the local session ends.
MOODLE_SESSIONS: dict[str, requests.Session] = {}
EXPORT_JOBS: dict[str, "ExportJob"] = {}
EXPORT_JOBS_LOCK = Lock()


@dataclass
class Course:
    course_id: str
    name: str
    url: str


@dataclass
class Resource:
    title: str
    url: str
    kind: str
    status: str = "enlace"
    section: str = ""


@dataclass
class Section:
    name: str
    description: str
    activities: list[dict[str, str]] = field(default_factory=list)


@dataclass
class ExportJob:
    job_id: str
    client: requests.Session
    directory: Path
    status: str = "starting"
    stage: str = "Preparando la exportación"
    current_course: str = ""
    current_resource: str = ""
    course_count: int = 0
    completed_courses: int = 0
    resource_count: int = 0
    completed_resources: int = 0
    ready_archive: Path | None = None
    ready_name: str = ""
    error: str = ""
    cancel_event: Event = field(default_factory=Event)
    download_event: Event = field(default_factory=Event)
    lock: Lock = field(default_factory=Lock)

    def update(self, **values) -> None:
        with self.lock:
            for key, value in values.items():
                setattr(self, key, value)

    def snapshot(self) -> dict:
        with self.lock:
            return {
                "status": self.status,
                "stage": self.stage,
                "current_course": self.current_course,
                "current_resource": self.current_resource,
                "course_count": self.course_count,
                "completed_courses": self.completed_courses,
                "resource_count": self.resource_count,
                "completed_resources": self.completed_resources,
                "ready": self.ready_archive is not None,
                "ready_name": self.ready_name,
                "error": self.error,
            }


class ExportCancelled(Exception):
    pass


def check_export_cancelled(cancel_event: Event | None) -> None:
    if cancel_event and cancel_event.is_set():
        raise ExportCancelled()


def safe_name(value: str, fallback: str = "archivo") -> str:
    """Return a portable name without path separators or control characters."""
    value = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "-", value).strip(" .-")
    return value[:150] or fallback


def same_site(url: str) -> bool:
    parsed = urlsplit(url)
    return parsed.scheme == "https" and parsed.hostname == urlsplit(BASE_URL).hostname


def csrf_token() -> str:
    token = session.get("csrf_token")
    if token is None:
        token = secrets.token_urlsafe(32)
        session["csrf_token"] = token
    return token


def check_csrf() -> None:
    submitted = request.form.get("csrf_token", "")
    expected = session.get("csrf_token", "")
    if not expected or not secrets.compare_digest(submitted, expected):
        abort(400, description="La solicitud expiró. Recarga la página e inténtalo de nuevo.")


def moodle_error(response: requests.Response) -> str | None:
    soup = BeautifulSoup(response.text, "html.parser")
    error = soup.select_one(
        "#loginerrormessage, .loginerrors, [role='alert'].alert-danger, .alert-danger"
    )
    if error:
        return error.get_text(" ", strip=True)
    if urlsplit(response.url).path.rstrip("/") == "/login/index.php":
        return "Moodle no aceptó el acceso. Revisa tu usuario y contraseña."
    return None


def authenticate(username: str, password: str) -> requests.Session:
    client = requests.Session()
    client.headers.update({"User-Agent": "UCNL-Moodle-Exporter/1.0"})
    response = client.get(f"{BASE_URL}/login/index.php", timeout=(10, 30))
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    form = soup.select_one("form#login") or soup.select_one("form.login-form")
    if form is None:
        raise RuntimeError("No se encontró el formulario de acceso de Moodle.")
    action = urljoin(response.url, form.get("action") or response.url)
    if not same_site(action):
        raise RuntimeError("El formulario de acceso redirige a un sitio inesperado.")
    payload = {
        element.get("name"): element.get("value", "")
        for element in form.select("input[name]")
        if element.get("type", "").lower() == "hidden"
    }
    payload.update({"username": username, "password": password})
    result = client.post(action, data=payload, timeout=(10, 30), allow_redirects=True)
    result.raise_for_status()
    error = moodle_error(result)
    if error:
        raise RuntimeError(error)
    return client


def course_list_from_html(markup: str, page_url: str = COURSES_URL) -> list[Course]:
    soup = BeautifulSoup(markup, "html.parser")
    found: dict[str, Course] = {}
    for anchor in soup.select("a[href]"):
        url = urljoin(page_url, anchor.get("href", ""))
        parsed = urlsplit(url)
        course_id = parse_qs(parsed.query).get("id", [""])[0]
        if parsed.path.rstrip("/") != "/course/view.php" or not course_id.isdigit():
            continue
        title = anchor.get_text(" ", strip=True)
        if not title or title.lower() in {"view", "ver", "more"}:
            card = anchor.find_parent(
                class_=re.compile(r"(course-listitem|coursebox|course-card|course-info-container)")
            )
            heading = card.select_one("h2, h3, .coursename") if card else None
            title = heading.get_text(" ", strip=True) if heading else f"Curso {course_id}"
        found.setdefault(course_id, Course(course_id, title, url))
    return list(found.values())


def _sesskey_from_html(markup: str) -> str | None:
    soup = BeautifulSoup(markup, "html.parser")
    input_element = soup.select_one("input[name='sesskey']")
    if input_element and input_element.get("value"):
        return input_element["value"]
    for script in soup.select("script"):
        match = re.search(r'"sesskey"\s*:\s*"([^"]+)"', script.string or script.get_text())
        if match:
            return match.group(1)
    return None


def courses_from_ajax_response(data: dict) -> list[Course]:
    courses = []
    for item in data.get("courses", []):
        course_id = str(item.get("id", ""))
        title = item.get("fullname") or item.get("displayname")
        if not course_id.isdigit() or not title:
            continue
        url = item.get("viewurl") or f"{BASE_URL}/course/view.php?id={course_id}"
        absolute_url = urljoin(BASE_URL, url)
        if same_site(absolute_url):
            courses.append(Course(course_id, title, absolute_url))
    return courses


def courses_from_moodle_ajax(
    client: requests.Session, page_url: str, sesskey: str
) -> list[Course]:
    endpoint = f"{BASE_URL}/lib/ajax/service.php"
    courses: dict[str, Course] = {}
    offset = 0
    limit = 50
    while True:
        body = [
            {
                "index": 0,
                "methodname": "core_course_get_enrolled_courses_by_timeline_classification",
                "args": {
                    "offset": offset,
                    "limit": limit,
                    "classification": "all",
                    "sort": "fullname",
                    "customfieldname": "",
                    "customfieldvalue": "",
                    "searchvalue": "",
                },
            }
        ]
        response = client.post(
            endpoint,
            params={"sesskey": sesskey},
            json=body,
            headers={
                "Accept": "application/json",
                "Referer": page_url,
                "X-Requested-With": "XMLHttpRequest",
            },
            timeout=(10, 30),
        )
        response.raise_for_status()
        try:
            result = response.json()
        except requests.exceptions.JSONDecodeError as error:
            raise RuntimeError("Moodle devolvió una respuesta inesperada al cargar cursos.") from error
        if not isinstance(result, list) or not result:
            raise RuntimeError("Moodle no devolvió la lista de cursos esperada.")
        first = result[0]
        if not isinstance(first, dict):
            raise RuntimeError("Moodle devolvió una respuesta de cursos no válida.")
        if first.get("error"):
            exception = first.get("exception")
            message = exception.get("message", "") if isinstance(exception, dict) else ""
            raise RuntimeError(
                f"Moodle no permitió consultar la lista de cursos: {message or 'sesión no válida'}."
            )
        data = first.get("data", {})
        if not isinstance(data, dict):
            raise RuntimeError("Moodle devolvió datos de cursos en un formato inesperado.")
        for course in courses_from_ajax_response(data):
            courses.setdefault(course.course_id, course)
        next_offset = data.get("nextoffset")
        if next_offset is None:
            if len(data.get("courses", [])) < limit:
                break
            offset += limit
        elif not isinstance(next_offset, int) or next_offset < 0 or next_offset <= offset:
            break
        else:
            offset = next_offset
    return list(courses.values())


def course_pages(client: requests.Session) -> list[Course]:
    courses: dict[str, Course] = {}
    visited: set[str] = set()
    sesskey = None
    first_page_url = None
    next_url: str | None = COURSES_URL
    while next_url and next_url not in visited:
        visited.add(next_url)
        first_page_url = first_page_url or next_url
        response = client.get(next_url, timeout=(10, 30))
        response.raise_for_status()
        if urlsplit(response.url).path.rstrip("/") == "/login/index.php":
            raise RuntimeError("La sesión de Moodle expiró. Inicia sesión de nuevo.")
        if sesskey is None:
            sesskey = _sesskey_from_html(response.text)
        for course in course_list_from_html(response.text, response.url):
            courses.setdefault(course.course_id, course)
        soup = BeautifulSoup(response.text, "html.parser")
        next_link = soup.select_one(
            ".pagination a[rel='next'], nav a[rel='next'], a[aria-label='Siguiente']"
        )
        next_url = urljoin(response.url, next_link["href"]) if next_link else None
        if next_url and not same_site(next_url):
            raise RuntimeError("La paginación de cursos apunta a un sitio inesperado.")
    if not courses and sesskey and first_page_url:
        for course in courses_from_moodle_ajax(client, first_page_url, sesskey):
            courses.setdefault(course.course_id, course)
    elif not courses:
        raise RuntimeError(
            "Moodle no mostró cursos ni el token necesario para consultar la lista. "
            "Verifica que el acceso siga activo e inténtalo de nuevo."
        )
    return list(courses.values())


def _section_elements(soup: BeautifulSoup) -> list:
    sections = soup.select("li.section, .course-section")
    if sections:
        return sections
    return soup.select("[data-sectionid]")


def _activity_title(anchor) -> str:
    container = anchor.find_parent(class_=re.compile(r"activity"))
    if container:
        title = container.select_one(
            ".instancename, .activityname, .activity-name, .aalink"
        )
        if title:
            return title.get_text(" ", strip=True)
    return anchor.get_text(" ", strip=True) or "Recurso sin título"


def _is_presentation_section(name: str) -> bool:
    normalized = normalize("NFKD", name)
    normalized = "".join(character for character in normalized if not combining(character))
    return normalized.strip().casefold().startswith("presentacion")


def _is_program_page(url: str) -> bool:
    parsed = urlsplit(url)
    return (
        parsed.path.rstrip("/") == "/mod/page/view.php"
        and parse_qs(parsed.query).get("id") == [PROGRAM_PAGE_ID]
    )


def _image_resources(markup: BeautifulSoup, page_url: str, section: str) -> list[Resource]:
    images = []
    seen = set()
    for element in markup.select("img[src], img[data-src]"):
        source = element.get("src") or element.get("data-src")
        if not source:
            continue
        url = urljoin(page_url, source)
        parsed = urlsplit(url)
        if not same_site(url) or url in seen:
            continue
        path = unquote(parsed.path).lower()
        if any(excluded in path for excluded in ("/theme/", "/pix/", "/user/", "/flags/")):
            continue
        seen.add(url)
        images.append(
            Resource(
                element.get("alt") or element.get("title") or Path(path).name or "Imagen del curso",
                url,
                "imagen",
                section=section,
            )
        )
    return images


def _activity_content(soup: BeautifulSoup) -> Tag | BeautifulSoup:
    return soup.select_one("#region-main, [role='main'], main") or soup


def extract_course_content(
    markup: str, course: Course
) -> tuple[list[Section], list[Resource], list[str]]:
    soup = BeautifulSoup(markup, "html.parser")
    sections: list[Section] = []
    activities: list[Resource] = []
    for element in _section_elements(soup):
        title_element = element.select_one(
            ".sectionname, .sectionname a, h3, h4, [data-region='section-title']"
        )
        section_name = title_element.get_text(" ", strip=True) if title_element else ""
        section_id = element.get("data-sectionid") or element.get("id", "").rsplit("-", 1)[-1]
        section_name = section_name or (
            "Presentación" if section_id == "0" else f"Unidad {section_id or len(sections) + 1}"
        )
        presentation = _is_presentation_section(section_name)
        description_element = None if presentation else element.select_one(
            ".summary, .section-summary, .content, .section_availability"
        )
        description = (
            description_element.get_text(" ", strip=True) if description_element else ""
        )
        section_activities = []
        if not presentation:
            activities.extend(_image_resources(element, course.url, section_name))
        for anchor in element.select("a[href]"):
            url = urljoin(course.url, anchor.get("href", ""))
            parsed = urlsplit(url)
            if not same_site(url) or parsed.path.rstrip("/") == "/course/view.php":
                continue
            if presentation and not _is_program_page(url):
                continue
            title = _activity_title(anchor)
            section_activities.append({"title": title, "url": url})
            if (
                parsed.path.rstrip("/") == "/pluginfile.php"
                or parsed.path.rstrip("/") == "/file.php"
                or MOODLE_ACTIVITY_PATH.match(parsed.path)
                or Path(unquote(parsed.path)).suffix.lower() in FILE_EXTENSIONS
            ):
                activities.append(
                    Resource(title, url, resource_kind(url), section=section_name)
                )
        sections.append(Section(section_name, description, section_activities))

    for selector in (
        ".course-summary img",
        ".course-summary-item img",
        ".course-summary-content img",
        ".course-header img",
        "[data-region='course-summary'] img",
    ):
        for image in soup.select(selector):
            image_markup = BeautifulSoup(str(image), "html.parser")
            activities.extend(_image_resources(image_markup, course.url, "Información del curso"))

    tutors = find_tutors(soup)
    seen: set[tuple[str, str]] = set()
    resources = []
    for resource in activities:
        key = (resource.url, resource.section)
        if key not in seen:
            seen.add(key)
            resources.append(resource)
    return sections, resources, tutors


def find_tutors(soup: BeautifulSoup) -> list[str]:
    selectors = (
        ".teachers", ".course-contacts", ".coursecontact", ".course-contact",
        "[data-region='course-contacts']", ".teacher",
    )
    names: list[str] = []
    for selector in selectors:
        for element in soup.select(selector):
            text = element.get_text(" ", strip=True)
            text = re.sub(
                r"^(?:(?:profesores?|docentes?|tutor(?:es)?|teachers?)\s*:?\s*)",
                "",
                text,
                flags=re.I,
            )
            if text and len(text) < 250:
                names.extend(part.strip() for part in re.split(r"[,;|]", text) if part.strip())
    if not names:
        plain_text = soup.get_text("\n", strip=True)
        names.extend(match.group(1).strip() for match in TUTOR_PATTERN.finditer(plain_text))
    return list(dict.fromkeys(names))


def resource_kind(url: str) -> str:
    path = unquote(urlsplit(url).path).lower()
    if MOODLE_ACTIVITY_PATH.match(urlsplit(url).path):
        return "actividad"
    extension = Path(path).suffix
    if extension in VIDEO_EXTENSIONS:
        return "video"
    if extension == ".pdf":
        return "PDF"
    if extension in FILE_EXTENSIONS:
        return "archivo"
    if path.rstrip("/") == "/file.php":
        return "archivo"
    if "/pluginfile.php/" in path or path.rstrip("/") == "/pluginfile.php":
        return "archivo"
    return "enlace"


def should_crawl_activity(url: str) -> bool:
    parsed = urlsplit(url)
    return (
        same_site(url)
        and parsed.path.rstrip("/")
        in {
            "/mod/book/view.php",
            "/mod/page/view.php",
            "/mod/resource/view.php",
            "/mod/url/view.php",
        }
    )


def discover_activity_resources(
    client: requests.Session,
    course: Course,
    resources: list[Resource],
    progress: Callable[[str], None] | None = None,
    cancel_event: Event | None = None,
    report: dict | None = None,
) -> list[Resource]:
    discovered = list(resources)
    queue = deque(
        resource for resource in resources
        if resource.kind == "actividad" and should_crawl_activity(resource.url)
    )
    visited: set[tuple[str, str]] = set()
    crawled_pages = 0
    while queue:
        check_export_cancelled(cancel_event)
        if crawled_pages >= MAX_ACTIVITY_PAGES_PER_COURSE:
            if report is not None:
                report["warnings"].append(
                    f"{course.name}: se detuvo el rastreo al alcanzar el límite de "
                    f"{MAX_ACTIVITY_PAGES_PER_COURSE} páginas Moodle."
                )
            if progress:
                progress(
                    f"Límite de {MAX_ACTIVITY_PAGES_PER_COURSE} páginas alcanzado; "
                    "se omiten más subtemas."
                )
            break
        activity = queue.popleft()
        url = activity.url
        visit_key = (url, activity.section)
        if visit_key in visited:
            continue
        visited.add(visit_key)
        crawled_pages += 1
        parsed = urlsplit(url)
        if not should_crawl_activity(url) or not MOODLE_ACTIVITY_PATH.match(parsed.path):
            continue
        if progress:
            progress(f"Explorando página {len(visited)}: {activity.title}")
        response = client.get(url, timeout=(10, 20))
        response.raise_for_status()
        if urlsplit(response.url).path.rstrip("/") == "/login/index.php":
            raise RuntimeError("La sesión de Moodle expiró. Inicia sesión de nuevo.")
        soup = _activity_content(BeautifulSoup(response.text, "html.parser"))
        if _is_program_page(url):
            discovered.extend(_image_resources(soup, response.url, activity.section))
            continue

        discovered.extend(_image_resources(soup, response.url, activity.section))
        for anchor in soup.select("a[href], video[src], source[src], iframe[src]"):
            href = anchor.get("href") or anchor.get("src")
            if not href:
                continue
            linked_url = urljoin(response.url, href)
            if not same_site(linked_url):
                continue
            kind = resource_kind(linked_url)
            title = (
                anchor.get_text(" ", strip=True)
                or anchor.get("title")
                or anchor.get("alt")
                or Path(unquote(urlsplit(linked_url).path)).name
                or "Recurso"
            )
            if MOODLE_ACTIVITY_PATH.match(urlsplit(linked_url).path):
                nested = Resource(title, linked_url, "actividad", section=activity.section)
                discovered.append(nested)
                if (
                    should_crawl_activity(linked_url)
                    and (linked_url, activity.section) not in visited
                ):
                    queue.append(nested)
            elif kind in {"PDF", "video", "archivo"}:
                discovered.append(
                    Resource(title, linked_url, kind, section=activity.section)
                )
    unique: dict[tuple[str, str], Resource] = {}
    for resource in discovered:
        unique.setdefault((resource.url, resource.section), resource)
    return list(unique.values())


def filename_from_response(response: requests.Response, resource: Resource) -> str:
    disposition = Message()
    disposition["content-disposition"] = response.headers.get("Content-Disposition", "")
    filename = disposition.get_filename()
    if not filename:
        filename = unquote(Path(urlsplit(response.url).path).name)
    if not filename or filename in {".", ".."}:
        filename = resource.title
    filename = safe_name(filename, "recurso")
    if not Path(filename).suffix:
        extension = mimetypes.guess_extension(
            response.headers.get("Content-Type", "").split(";", 1)[0].strip()
        )
        if extension:
            filename += extension
    return filename


def download_resource(
    client: requests.Session,
    resource: Resource,
    destination: Path,
    cancel_event: Event | None = None,
) -> tuple[str, str]:
    response = client.get(resource.url, stream=True, timeout=(10, 90))
    response.raise_for_status()
    if urlsplit(response.url).path.rstrip("/") == "/login/index.php":
        response.close()
        return "requiere inicio de sesión", ""
    content_type = response.headers.get("Content-Type", "").lower()
    if "text/html" in content_type and resource.kind != "video":
        response.close()
        return "no es un archivo descargable", ""
    filename = filename_from_response(response, resource)
    target = destination / filename
    suffix = 2
    while target.exists():
        target = destination / f"{Path(filename).stem} ({suffix}){Path(filename).suffix}"
        suffix += 1
    completed = False
    try:
        with target.open("wb") as output:
            for chunk in response.iter_content(chunk_size=128 * 1024):
                check_export_cancelled(cancel_event)
                if chunk:
                    output.write(chunk)
        completed = True
    finally:
        response.close()
        if not completed:
            target.unlink(missing_ok=True)
    return "descargado", target.name


def create_tematario(
    course: Course,
    sections: list[Section],
    tutors: list[str],
    downloaded_resources: list[tuple[Resource, str]] | None = None,
) -> str:
    lines = [f"# {course.name}", "", f"**Tutor(es):** {', '.join(tutors) if tutors else 'No identificado en el curso.'}", "", "## Temario", ""]
    for resource, filename in downloaded_resources or []:
        if resource.section == "Información del curso" and resource.kind == "imagen":
            local_path = quote(filename.replace("\\", "/"), safe="/")
            lines.extend([f"![{resource.title}]({local_path})", ""])
    if not sections:
        lines.append("No se encontraron secciones en la página del curso.")
    for index, section in enumerate(sections, start=1):
        lines.extend([f"### {index}. {section.name}", ""])
        if section.description:
            lines.extend([section.description, ""])
        if section.activities:
            lines.extend(
                f"- [{activity['title']}]({activity['url']})"
                for activity in section.activities
            )
        else:
            lines.append("- Sin actividades identificadas.")
        section_resources = [
            (resource, filename)
            for resource, filename in downloaded_resources or []
            if resource.section == section.name
        ]
        for resource, filename in section_resources:
            local_path = quote(filename.replace("\\", "/"), safe="/")
            if resource.kind == "imagen":
                lines.extend(["", f"![{resource.title}]({local_path})"])
            else:
                lines.append(f"- [Descargado: {resource.title}]({local_path})")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def export_course(
    client: requests.Session,
    course: Course,
    output_dir: Path,
    report: dict,
    progress: Callable[..., None] | None = None,
    cancel_event: Event | None = None,
) -> Path:
    check_export_cancelled(cancel_event)
    if progress:
        progress(stage="Leyendo la página del curso", current_resource="")
    response = client.get(course.url, timeout=(10, 45))
    response.raise_for_status()
    if urlsplit(response.url).path.rstrip("/") == "/login/index.php":
        raise RuntimeError("La sesión de Moodle expiró. Inicia sesión de nuevo.")
    sections, resources, tutors = extract_course_content(response.text, course)

    def activity_progress(message: str) -> None:
        if progress:
            progress(stage=message, current_resource=message)

    resources = discover_activity_resources(
        client, course, resources, activity_progress, cancel_event, report
    )
    for section in sections:
        known_urls = {activity["url"] for activity in section.activities}
        for resource in resources:
            if (
                resource.kind == "actividad"
                and resource.section == section.name
                and resource.url not in known_urls
            ):
                section.activities.append({"title": resource.title, "url": resource.url})
                known_urls.add(resource.url)
    course_dir = output_dir / (
        f"{safe_name(course.name, f'curso-{course.course_id}')} [{course.course_id}]"
    )
    resources_dir = course_dir / "Recursos"
    resources_dir.mkdir(parents=True, exist_ok=True)
    resource_records = []
    downloaded_resources = []
    downloadable = [
        resource for resource in resources
        if resource.kind in {"PDF", "video", "archivo", "imagen"}
    ]
    if progress:
        progress(
            stage="Descargando recursos",
            resource_count=len(downloadable),
            completed_resources=0,
            current_resource="",
        )
    completed_resources = 0
    for resource in resources:
        check_export_cancelled(cancel_event)
        record = asdict(resource)
        if resource.kind in {"PDF", "video", "archivo", "imagen"}:
            if progress:
                progress(current_resource=resource.title)
            try:
                resource_dir = resources_dir
                if resource.section:
                    resource_dir /= safe_name(resource.section, "Unidad")
                resource_dir.mkdir(parents=True, exist_ok=True)
                status, filename = download_resource(
                    client, resource, resource_dir, cancel_event
                )
                record["status"] = status
                relative_filename = str(
                    Path("Recursos")
                    / resource_dir.relative_to(resources_dir)
                    / filename
                ).replace("\\", "/")
                record["archivo"] = relative_filename
                if status == "descargado":
                    report["downloaded"] += 1
                    downloaded_resources.append((resource, relative_filename))
                else:
                    report["warnings"].append(
                        f"{course.name}: {resource.title} ({status})"
                    )
            except requests.RequestException as error:
                record["status"] = f"error de descarga: {error}"
                report["warnings"].append(
                    f"{course.name}: no se pudo descargar {resource.title}: {error}"
                )
            completed_resources += 1
            if progress:
                progress(completed_resources=completed_resources)
        elif resource.kind == "actividad":
            record["status"] = "actividad Moodle; consulta su enlace en el temario"
        resource_records.append(record)
    check_export_cancelled(cancel_event)
    (course_dir / "TEMARIO.md").write_text(
        create_tematario(course, sections, tutors, downloaded_resources),
        encoding="utf-8",
    )
    metadata = {
        "id": course.course_id,
        "nombre": course.name,
        "url": course.url,
        "tutores": tutors,
        "secciones": [asdict(section) for section in sections],
        "recursos": resource_records,
    }
    (course_dir / "curso.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    report["courses"].append(
        {"name": course.name, "tutors": tutors, "resources": len(resources)}
    )
    return course_dir


def make_export(client: requests.Session, output_dir: Path) -> dict:
    courses = course_pages(client)
    if not courses:
        raise RuntimeError("No se encontraron cursos en la página de Moodle.")
    report = {"courses": [], "downloaded": 0, "warnings": []}
    for course in courses:
        export_course(client, course, output_dir, report)
    return report


def zip_course(
    course_dir: Path,
    archive_path: Path,
    cancel_event: Event,
    progress: Callable[..., None] | None = None,
) -> None:
    files = [path for path in course_dir.rglob("*") if path.is_file()]
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for index, path in enumerate(files, start=1):
            check_export_cancelled(cancel_event)
            compression = (
                zipfile.ZIP_STORED
                if path.suffix.lower() in VIDEO_EXTENSIONS
                else zipfile.ZIP_DEFLATED
            )
            entry_info = zipfile.ZipInfo(path.relative_to(course_dir).as_posix())
            entry_info.compress_type = compression
            if progress:
                progress(
                    stage=f"Comprimiendo archivo {index} de {len(files)}",
                    current_resource=entry_info.filename,
                    resource_count=len(files),
                    completed_resources=index - 1,
                )
            with path.open("rb") as source, archive.open(
                entry_info, "w", force_zip64=True
            ) as entry:
                while chunk := source.read(1024 * 1024):
                    check_export_cancelled(cancel_event)
                    entry.write(chunk)
            check_export_cancelled(cancel_event)
            if progress:
                progress(completed_resources=index)


def run_export_job(job: ExportJob) -> None:
    try:
        job.update(status="running", stage="Cargando lista de cursos")
        courses = course_pages(job.client)
        if not courses:
            raise RuntimeError("No se encontraron cursos en la página de Moodle.")
        job.update(course_count=len(courses), stage="Preparando cursos")
        report = {"courses": [], "downloaded": 0, "warnings": []}
        for course in courses:
            check_export_cancelled(job.cancel_event)
            job.update(
                current_course=course.name,
                current_resource="",
                resource_count=0,
                completed_resources=0,
                stage="Iniciando curso",
            )
            course_dir = export_course(
                job.client,
                course,
                job.directory / "contenido",
                report,
                job.update,
                job.cancel_event,
            )
            check_export_cancelled(job.cancel_event)
            archive_path = job.directory / f"{course_dir.name}.zip"
            job.update(stage=f"Preparando descarga de {course.name}")
            zip_course(course_dir, archive_path, job.cancel_event, job.update)
            shutil.rmtree(course_dir, ignore_errors=True)
            job.update(
                ready_archive=archive_path,
                ready_name=f"{course_dir.name}.zip",
                stage="Listo para descargar este curso",
            )
            while not job.download_event.wait(0.2):
                check_export_cancelled(job.cancel_event)
            check_export_cancelled(job.cancel_event)
            job.download_event.clear()
            archive_path.unlink(missing_ok=True)
            job.update(
                ready_archive=None,
                ready_name="",
                completed_courses=job.snapshot()["completed_courses"] + 1,
                stage=f"Curso entregado: {course.name}",
            )
        final_status = "cancelled" if job.cancel_event.is_set() else "complete"
        job.update(
            status=final_status,
            stage=(
                "Exportación cancelada"
                if final_status == "cancelled"
                else "Todos los cursos están listos"
            ),
            current_resource="",
        )
    except ExportCancelled:
        job.update(status="cancelled", stage="Exportación cancelada", current_resource="")
    except Exception as error:
        logging.exception("Falló la exportación de Moodle")
        job.update(status="error", stage="La exportación encontró un error", error=str(error))
    finally:
        with job.lock:
            archive_path = job.ready_archive
            job.ready_archive = None
        if archive_path:
            archive_path.unlink(missing_ok=True)
        shutil.rmtree(job.directory / "contenido", ignore_errors=True)
        if job.status in {"cancelled", "error", "complete"}:
            shutil.rmtree(job.directory, ignore_errors=True)


def moodle_client() -> requests.Session:
    identifier = session.get("moodle_session_id")
    client = MOODLE_SESSIONS.get(identifier or "")
    if client is None:
        abort(401, description="Tu sesión local terminó. Inicia sesión de nuevo.")
    return client


def current_export_job(job_id: str) -> ExportJob:
    if session.get("export_job_id") != job_id:
        abort(404)
    with EXPORT_JOBS_LOCK:
        job = EXPORT_JOBS.get(job_id)
    if job is None:
        abort(404, description="La exportación ya no está disponible.")
    return job


@app.get("/")
def index():
    client_id = session.get("moodle_session_id")
    if client_id and client_id in MOODLE_SESSIONS:
        try:
            courses = course_pages(MOODLE_SESSIONS[client_id])
        except (requests.RequestException, RuntimeError) as error:
            return render_template(
                "moodle_ucnl.html",
                csrf=csrf_token(),
                courses=[],
                error=str(error),
                logged_in=True,
                export_job_id=session.get("export_job_id"),
            )
        return render_template(
            "moodle_ucnl.html",
            csrf=csrf_token(),
            courses=courses,
            logged_in=True,
            error=None,
            export_job_id=session.get("export_job_id"),
        )
    return render_template(
        "moodle_ucnl.html",
        csrf=csrf_token(),
        courses=[],
        logged_in=False,
        error=None,
        export_job_id=None,
    )


@app.post("/login")
def login():
    check_csrf()
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    if not username or not password:
        flash("Escribe tu usuario y contraseña de Moodle.", "error")
        return redirect(url_for("index"))
    try:
        client = authenticate(username, password)
        courses = course_pages(client)
    except (requests.RequestException, RuntimeError) as error:
        logging.warning("Falló el inicio de sesión o la lectura de cursos: %s", error)
        flash(str(error), "error")
        return redirect(url_for("index"))
    old_identifier = session.get("moodle_session_id")
    if old_identifier:
        MOODLE_SESSIONS.pop(old_identifier, None)
    identifier = secrets.token_urlsafe(32)
    MOODLE_SESSIONS[identifier] = client
    session["moodle_session_id"] = identifier
    session.pop("csrf_token", None)
    flash(f"Sesión iniciada. Se encontraron {len(courses)} cursos.", "success")
    return redirect(url_for("index"))


@app.post("/export")
def export():
    check_csrf()
    client = moodle_client()
    existing_id = session.get("export_job_id")
    if existing_id:
        with EXPORT_JOBS_LOCK:
            existing_job = EXPORT_JOBS.get(existing_id)
        if existing_job and existing_job.status in {"starting", "running", "cancelling"}:
            return jsonify({"error": "Ya hay una exportación en curso."}), 409
        if existing_job:
            with EXPORT_JOBS_LOCK:
                EXPORT_JOBS.pop(existing_id, None)
    job_id = secrets.token_urlsafe(24)
    job = ExportJob(
        job_id=job_id,
        client=client,
        directory=Path(tempfile.mkdtemp(prefix="moodle_ucnl_")),
    )
    with EXPORT_JOBS_LOCK:
        EXPORT_JOBS[job_id] = job
    session["export_job_id"] = job_id
    Thread(target=run_export_job, args=(job,), daemon=True).start()
    return jsonify({"job_id": job_id, "status_url": url_for("export_status", job_id=job_id)})


@app.get("/export/<job_id>/status")
def export_status(job_id: str):
    return jsonify(current_export_job(job_id).snapshot())


@app.post("/export/<job_id>/cancel")
def cancel_export(job_id: str):
    check_csrf()
    job = current_export_job(job_id)
    if job.status in {"starting", "running"}:
        job.update(status="cancelling", stage="Cancelando; esperando que termine la solicitud actual")
        job.cancel_event.set()
        job.download_event.set()
    return jsonify(job.snapshot())


@app.get("/export/<job_id>/course")
def download_export_course(job_id: str):
    job = current_export_job(job_id)
    snapshot = job.snapshot()
    with job.lock:
        archive_path = job.ready_archive
        archive_name = job.ready_name
    if not snapshot["ready"] or archive_path is None:
        abort(409, description="El curso todavía se está preparando.")
    complete = False

    def stream_archive():
        nonlocal complete
        try:
            with archive_path.open("rb") as archive:
                while chunk := archive.read(1024 * 1024):
                    yield chunk
            complete = True
        finally:
            if complete:
                job.download_event.set()

    response = Response(
        stream_archive(),
        mimetype="application/zip",
        headers={"Cache-Control": "no-store"},
    )
    response.headers.set("Content-Disposition", "attachment", filename=archive_name)
    response.call_on_close(response.response.close)
    return response


@app.post("/export/<job_id>/dismiss")
def dismiss_export(job_id: str):
    check_csrf()
    job = current_export_job(job_id)
    if job.status not in {"complete", "cancelled", "error"}:
        abort(409, description="La exportación todavía está activa.")
    with EXPORT_JOBS_LOCK:
        EXPORT_JOBS.pop(job_id, None)
    session.pop("export_job_id", None)
    return jsonify({"status": "dismissed"})


@app.post("/logout")
def logout():
    check_csrf()
    export_job_id = session.pop("export_job_id", None)
    if export_job_id:
        with EXPORT_JOBS_LOCK:
            job = EXPORT_JOBS.get(export_job_id)
        if job and job.status in {"starting", "running"}:
            job.cancel_event.set()
            job.download_event.set()
    identifier = session.pop("moodle_session_id", None)
    client = MOODLE_SESSIONS.pop(identifier or "", None)
    if client:
        client.close()
    session.clear()
    flash("Sesión cerrada; la sesión de Moodle se eliminó de la memoria.", "success")
    return redirect(url_for("index"))


if __name__ == "__main__":
    print("Abre http://127.0.0.1:5000 en tu navegador.")
    app.run(host="127.0.0.1", port=5000, debug=False)
