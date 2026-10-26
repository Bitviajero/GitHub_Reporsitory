import io
import json
import shutil
import tempfile
import time
import unittest
import zipfile
from pathlib import Path
from threading import Thread
from unittest.mock import patch
import requests

import moodle_ucnl
from moodle_ucnl import (
    Course,
    create_tematario,
    course_list_from_html,
    courses_from_ajax_response,
    discover_activity_resources,
    extract_course_content,
    resource_kind,
    safe_name,
    should_crawl_activity,
)


class MoodleExportTests(unittest.TestCase):
    def test_flask_secret_key_uses_configured_stable_value(self):
        with patch.dict("os.environ", {"MOODLE_UCNL_SECRET_KEY": "stable-test-secret"}):
            self.assertEqual(moodle_ucnl.flask_secret_key(), b"stable-test-secret")
            self.assertEqual(moodle_ucnl.flask_secret_key(), b"stable-test-secret")

    def test_flask_secret_key_persists_in_local_app_data(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict("os.environ", {"LOCALAPPDATA": directory}, clear=True):
                first_key = moodle_ucnl.flask_secret_key()
                self.assertEqual(moodle_ucnl.flask_secret_key(), first_key)
                self.assertEqual(
                    (Path(directory) / "UCNLMoodleExporter" / "session.key").read_bytes(),
                    first_key,
                )

    def test_course_list_deduplicates_course_links(self):
        courses = course_list_from_html(
            """
            <div class="coursebox"><h3>Álgebra I</h3>
              <a href="/course/view.php?id=12">Álgebra I</a>
              <a href="/course/view.php?id=12">Entrar</a>
            </div>
            <a href="/course/view.php?id=34">Bases de datos</a>
            """
        )
        self.assertEqual([course.course_id for course in courses], ["12", "34"])
        self.assertEqual(courses[0].name, "Álgebra I")

    def test_moodle_ajax_response_converts_course_records(self):
        courses = courses_from_ajax_response(
            {
                "courses": [
                    {"id": 23, "fullname": "Historia", "viewurl": "/course/view.php?id=23"},
                    {"id": 24, "displayname": "Matemáticas"},
                    {"id": "not-an-id", "fullname": "Ignorar"},
                    {"id": 25, "fullname": "Enlace externo", "viewurl": "https://example.org"},
                ]
            }
        )
        self.assertEqual(
            [(course.course_id, course.name) for course in courses],
            [("23", "Historia"), ("24", "Matemáticas")],
        )

    def test_deep_scan_avoids_forums_and_only_crawls_content_pages(self):
        self.assertTrue(
            should_crawl_activity("https://licenciatura.ucnl.edu.mx/mod/page/view.php?id=10")
        )
        self.assertTrue(
            should_crawl_activity("https://licenciatura.ucnl.edu.mx/mod/book/view.php?id=11")
        )
        self.assertFalse(
            should_crawl_activity("https://licenciatura.ucnl.edu.mx/mod/forum/view.php?id=12")
        )
        self.assertFalse(should_crawl_activity("https://example.org/mod/page/view.php?id=10"))

    def test_course_pages_uses_ajax_when_course_cards_are_not_in_html(self):
        class FakeResponse:
            url = moodle_ucnl.COURSES_URL
            text = '<script>M.cfg = {"sesskey":"valid-session-key"};</script>'

            @staticmethod
            def raise_for_status():
                pass

        client = requests.Session()
        with (
            patch.object(client, "get", return_value=FakeResponse()),
            patch.object(
                moodle_ucnl,
                "courses_from_moodle_ajax",
                return_value=[
                    Course("23", "Historia", "https://licenciatura.ucnl.edu.mx/course/view.php?id=23")
                ],
            ) as ajax_courses,
        ):
            result = moodle_ucnl.course_pages(client)
        self.assertEqual([course.name for course in result], ["Historia"])
        ajax_courses.assert_called_once_with(
            client, moodle_ucnl.COURSES_URL, "valid-session-key"
        )

    def test_course_ajax_fetches_all_pages(self):
        class FakeResponse:
            def __init__(self, data):
                self.data = data

            @staticmethod
            def raise_for_status():
                pass

            def json(self):
                return [{"error": False, "data": self.data}]

        client = requests.Session()
        responses = [
            FakeResponse(
                {"courses": [{"id": 1, "fullname": "Curso 1"}], "nextoffset": 1}
            ),
            FakeResponse(
                {"courses": [{"id": 2, "fullname": "Curso 2"}], "nextoffset": -1}
            ),
        ]
        with patch.object(client, "post", side_effect=responses) as post:
            courses = moodle_ucnl.courses_from_moodle_ajax(
                client, moodle_ucnl.COURSES_URL, "valid-session-key"
            )
        self.assertEqual([course.course_id for course in courses], ["1", "2"])
        self.assertEqual(post.call_count, 2)

    def test_course_pages_reports_missing_course_markup_and_sesskey(self):
        class FakeResponse:
            url = moodle_ucnl.COURSES_URL
            text = "<html><body>My courses</body></html>"

            @staticmethod
            def raise_for_status():
                pass

        client = requests.Session()
        with patch.object(client, "get", return_value=FakeResponse()):
            with self.assertRaisesRegex(RuntimeError, "no mostró cursos"):
                moodle_ucnl.course_pages(client)

    def test_course_content_includes_sections_activities_and_tutor(self):
        course = Course("12", "Álgebra I", "https://licenciatura.ucnl.edu.mx/course/view.php?id=12")
        sections, resources, tutors = extract_course_content(
            """
            <div class="teachers">Tutor: Ana Pérez</div>
            <ul class="topics">
              <li class="section" id="section-1" data-sectionid="1">
                <h3 class="sectionname">Unidad 1: Ecuaciones</h3>
                <div class="summary">Conceptos iniciales</div>
                <div class="activity">
                  <a href="/pluginfile.php/12/mod_resource/content/2/guia.pdf">
                    <span class="instancename">Guía de ejercicios</span>
                  </a>
                </div>
              </li>
            </ul>
            """,
            course,
        )
        self.assertEqual(sections[0].name, "Unidad 1: Ecuaciones")
        self.assertEqual(sections[0].description, "Conceptos iniciales")
        self.assertEqual(sections[0].activities[0]["title"], "Guía de ejercicios")
        self.assertEqual(resources[0].kind, "PDF")
        self.assertEqual(tutors, ["Ana Pérez"])

    def test_presentation_section_only_keeps_the_program_page(self):
        course = Course(
            "12",
            "Álgebra I",
            "https://licenciatura.ucnl.edu.mx/course/view.php?id=12",
        )
        sections, resources, _ = extract_course_content(
            """
            <li class="section" data-sectionid="0">
              <h3 class="sectionname">Presentación</h3>
              <div class="activity">
                <a href="/mod/forum/view.php?id=11">Foro de presentación</a>
                <a href="/mod/page/view.php?id=809871">Programa de la materia</a>
              </div>
            </li>
            <li class="section" data-sectionid="1">
              <h3 class="sectionname">Unidad 1</h3>
              <div class="activity"><a href="/mod/page/view.php?id=90">Tema 1</a></div>
            </li>
            """,
            course,
        )
        self.assertEqual(
            [activity["url"] for activity in sections[0].activities],
            ["https://licenciatura.ucnl.edu.mx/mod/page/view.php?id=809871"],
        )
        self.assertEqual(
            [resource.url for resource in resources if resource.section == "Presentación"],
            [sections[0].activities[0]["url"]],
        )

    def test_program_page_downloads_its_images_without_following_forum_links(self):
        program_url = "https://licenciatura.ucnl.edu.mx/mod/page/view.php?id=809871"
        program = moodle_ucnl.Resource(
            "Programa", program_url, "actividad", section="Presentación"
        )

        class FakeResponse:
            url = program_url
            text = """
              <div id="region-main">
                <div class="no-overflow">
                  <img src="/pluginfile.php/4/page/content/3/programa.jpg" alt="Programa">
                  <a href="/mod/forum/view.php?id=99">Foro de presentación</a>
                </div>
              </div>
            """

            @staticmethod
            def raise_for_status():
                pass

        client = requests.Session()
        with patch.object(client, "get", return_value=FakeResponse()) as get:
            resources = discover_activity_resources(client, Course("4", "Curso", ""), [program])
        self.assertEqual(
            [(resource.kind, resource.section) for resource in resources],
            [("actividad", "Presentación"), ("imagen", "Presentación")],
        )
        get.assert_called_once_with(program_url, timeout=(10, 20))

    def test_unit_activity_scan_follows_nested_pages_and_collects_images_and_files(self):
        root_url = "https://licenciatura.ucnl.edu.mx/mod/page/view.php?id=100"
        nested_url = "https://licenciatura.ucnl.edu.mx/mod/page/view.php?id=101"
        pages = {
            root_url: """
              <nav><a href="/mod/page/view.php?id=102">Enlace del menú</a></nav>
              <div id="region-main">
                <div class="no-overflow">
                  <img src="/pluginfile.php/4/page/content/3/portada.png" alt="Tutor del curso">
                  <a href="/mod/page/view.php?id=101">Subtema 1.1</a>
                  <a href="/pluginfile.php/4/resource/content/2/lectura.pdf">Lectura</a>
                  <a href="https://example.org/externo.pdf">Externo</a>
                </div>
              </div>
            """,
            nested_url: """
              <div id="region-main">
                <div class="no-overflow">
                  <img src="/pluginfile.php/4/page/content/4/diagrama.png" alt="Diagrama">
                </div>
              </div>
            """,
        }

        class FakeResponse:
            def __init__(self, url):
                self.url = url
                self.text = pages[url]

            @staticmethod
            def raise_for_status():
                pass

        client = requests.Session()
        progress_updates = []
        with patch.object(
            client, "get", side_effect=lambda url, **_kwargs: FakeResponse(url)
        ) as get:
            resources = discover_activity_resources(
                client,
                Course("4", "Curso", "https://licenciatura.ucnl.edu.mx/course/view.php?id=4"),
                [moodle_ucnl.Resource("Tema 1", root_url, "actividad", section="Unidad 1")],
                progress_updates.append,
            )
        self.assertEqual(get.call_count, 2)
        self.assertEqual(
            progress_updates,
            ["Explorando página 1: Tema 1", "Explorando página 2: Subtema 1.1"],
        )
        self.assertEqual(
            {(resource.kind, resource.title) for resource in resources},
            {
                ("actividad", "Tema 1"),
                ("imagen", "Tutor del curso"),
                ("actividad", "Subtema 1.1"),
                ("PDF", "Lectura"),
                ("imagen", "Diagrama"),
            },
        )

    def test_unit_scan_does_not_crawl_forum_or_follow_forum_posts(self):
        root_url = "https://licenciatura.ucnl.edu.mx/mod/page/view.php?id=100"
        forum_url = "https://licenciatura.ucnl.edu.mx/mod/forum/view.php?id=101"
        pages = {
            root_url: """
                <nav><a href="/mod/page/view.php?id=102">Enlace del menú</a></nav>
                <div id="region-main">
                  <a href="/mod/forum/view.php?id=101">Foro de la unidad</a>
                </div>
            """,
            forum_url: '<a href="/mod/forum/discuss.php?d=5">Publicación</a>',
        }

        class FakeResponse:
            def __init__(self, url):
                self.url = url
                self.text = pages[url]

            @staticmethod
            def raise_for_status():
                pass

        client = requests.Session()
        with patch.object(
            client, "get", side_effect=lambda url, **_kwargs: FakeResponse(url)
        ) as get:
            resources = discover_activity_resources(
                client,
                Course("4", "Curso", "https://licenciatura.ucnl.edu.mx/course/view.php?id=4"),
                [moodle_ucnl.Resource("Tema", root_url, "actividad", section="Unidad 1")],
            )
        get.assert_called_once_with(root_url, timeout=(10, 20))
        self.assertIn(
            forum_url,
            [resource.url for resource in resources if resource.kind == "actividad"],
        )

    def test_activity_scan_stops_at_page_limit_and_reports_it(self):
        root_url = "https://licenciatura.ucnl.edu.mx/mod/page/view.php?id=100"
        nested_url = "https://licenciatura.ucnl.edu.mx/mod/page/view.php?id=101"

        class FakeResponse:
            url = root_url
            text = '<div id="region-main"><a href="/mod/page/view.php?id=101">Subtema</a></div>'

            @staticmethod
            def raise_for_status():
                pass

        report = {"warnings": []}
        client = requests.Session()
        with (
            patch.object(moodle_ucnl, "MAX_ACTIVITY_PAGES_PER_COURSE", 1),
            patch.object(client, "get", return_value=FakeResponse()) as get,
        ):
            resources = discover_activity_resources(
                client,
                Course("4", "Curso", "https://licenciatura.ucnl.edu.mx/course/view.php?id=4"),
                [moodle_ucnl.Resource("Tema", root_url, "actividad", section="Unidad 1")],
                report=report,
            )

        get.assert_called_once_with(root_url, timeout=(10, 20))
        self.assertIn(nested_url, [resource.url for resource in resources])
        self.assertEqual(
            report["warnings"],
            ["Curso: se detuvo el rastreo al alcanzar el límite de 1 páginas Moodle."],
        )

    def test_export_downloads_unit_images_and_links_them_in_tematario(self):
        course = Course(
            "4",
            "Curso",
            "https://licenciatura.ucnl.edu.mx/course/view.php?id=4",
        )
        nested_pages = {
            "https://licenciatura.ucnl.edu.mx/mod/page/view.php?id=50": """
              <div class="no-overflow">
                <a href="/mod/page/view.php?id=51">Subtema 1.1</a>
                <img src="/pluginfile.php/4/page/content/3/subtema.png" alt="Imagen del subtema">
              </div>
            """,
            "https://licenciatura.ucnl.edu.mx/mod/page/view.php?id=51": """
              <div class="no-overflow">
                <img src="/pluginfile.php/4/page/content/3/detalle.png" alt="Detalle">
              </div>
            """,
        }

        class FakeResponse:
            def __init__(self, url, text="", content_type="text/html"):
                self.url = url
                self.text = text
                self.headers = {"Content-Type": content_type}

            @staticmethod
            def raise_for_status():
                pass

            @staticmethod
            def iter_content(chunk_size):
                yield b"image-data"

            @staticmethod
            def close():
                pass

        def fake_get(url, **_kwargs):
            if url == course.url:
                return FakeResponse(
                    url,
                    """
                    <li class="section" data-sectionid="1">
                      <h3 class="sectionname">Unidad 1</h3>
                      <img src="/pluginfile.php/4/page/content/3/tutor.png"
                           alt="Imagen del tutor">
                      <div class="activity">
                        <a href="/mod/page/view.php?id=50">Tema 1</a>
                      </div>
                    </li>
                    """,
                )
            if url in nested_pages:
                return FakeResponse(url, nested_pages[url])
            return FakeResponse(url, content_type="image/png")

        with tempfile.TemporaryDirectory() as directory:
            with (
                patch.object(moodle_ucnl, "course_pages", return_value=[course]),
                patch.object(requests.Session, "get", side_effect=fake_get),
            ):
                report = moodle_ucnl.make_export(requests.Session(), Path(directory))
            course_dir = Path(directory) / "Curso [4]"
            image_path = course_dir / "Recursos" / "Unidad 1" / "tutor.png"
            metadata = json.loads((course_dir / "curso.json").read_text(encoding="utf-8"))
            temario = (course_dir / "TEMARIO.md").read_text(encoding="utf-8")
            self.assertTrue(image_path.is_file())
            self.assertEqual(image_path.read_bytes(), b"image-data")
            self.assertIn(
                "Recursos/Unidad 1/tutor.png",
                [resource.get("archivo") for resource in metadata["recursos"]],
            )
            self.assertIn(
                "https://licenciatura.ucnl.edu.mx/mod/page/view.php?id=51",
                [activity["url"] for activity in metadata["secciones"][0]["activities"]],
            )
            self.assertIn("![Imagen del tutor](Recursos/Unidad%201/tutor.png)", temario)
            self.assertIn("Subtema 1.1", temario)
            self.assertEqual(report["downloaded"], 3)

    def test_tematario_does_not_invent_missing_tutor(self):
        course = Course("7", "Introducción", "https://licenciatura.ucnl.edu.mx/course/view.php?id=7")
        result = create_tematario(course, [], [])
        self.assertIn("No identificado en el curso.", result)
        self.assertIn("No se encontraron secciones", result)

    def test_safe_name_removes_paths_and_invalid_characters(self):
        self.assertEqual(safe_name("../../unidad: 1"), "unidad- 1")

    def test_moodle_php_activity_is_not_misclassified_as_a_php_download(self):
        self.assertEqual(
            resource_kind("https://licenciatura.ucnl.edu.mx/mod/page/view.php?id=809871"),
            "actividad",
        )

    def test_login_page_issues_csrf_and_password_is_not_saved_in_session(self):
        client = moodle_ucnl.app.test_client()
        response = client.get("/")
        self.assertEqual(response.status_code, 200)
        with client.session_transaction() as browser_session:
            token = browser_session["csrf_token"]

        with (
            patch.object(moodle_ucnl, "authenticate", return_value=requests.Session()),
            patch.object(moodle_ucnl, "course_pages", return_value=[]),
        ):
            response = client.post(
                "/login",
                data={
                    "csrf_token": token,
                    "username": "estudiante",
                    "password": "no-guardar",
                },
            )
        self.assertEqual(response.status_code, 302)
        with client.session_transaction() as browser_session:
            self.assertNotIn("username", browser_session)
            self.assertNotIn("password", browser_session)
            self.assertIn("moodle_session_id", browser_session)
            session_id = browser_session["moodle_session_id"]
        moodle_ucnl.MOODLE_SESSIONS.pop(session_id).close()

    def test_login_rejects_invalid_csrf_token(self):
        response = moodle_ucnl.app.test_client().post(
            "/login", data={"csrf_token": "invalid", "username": "user", "password": "pass"}
        )
        self.assertEqual(response.status_code, 400)

    def test_logged_in_page_renders_progress_cancel_and_course_download_controls(self):
        client = moodle_ucnl.app.test_client()
        moodle_ucnl.MOODLE_SESSIONS["ui-test-session"] = requests.Session()
        with client.session_transaction() as browser_session:
            browser_session["moodle_session_id"] = "ui-test-session"
        course = Course(
            "12",
            "Álgebra",
            "https://licenciatura.ucnl.edu.mx/course/view.php?id=12",
        )
        try:
            with patch.object(moodle_ucnl, "course_pages", return_value=[course]):
                response = client.get("/")
            self.assertEqual(response.status_code, 200)
            html = response.get_data(as_text=True)
            self.assertIn("id=\"export-bar\"", html)
            self.assertIn("Cancelar exportación", html)
            self.assertIn("Preparar descargas por curso", html)
        finally:
            moodle_ucnl.MOODLE_SESSIONS.pop("ui-test-session").close()

    def test_export_route_starts_background_job_and_reports_progress(self):
        client = moodle_ucnl.app.test_client()
        with tempfile.TemporaryDirectory() as parent:
            temporary_dir = Path(parent) / "export"
            with client.session_transaction() as browser_session:
                browser_session["csrf_token"] = "valid-token"
                browser_session["moodle_session_id"] = "test-session"
            moodle_ucnl.MOODLE_SESSIONS["test-session"] = requests.Session()
            with (
                patch.object(moodle_ucnl.tempfile, "mkdtemp", return_value=str(temporary_dir)),
                patch.object(moodle_ucnl, "Thread") as background_thread,
            ):
                response = client.post("/export", data={"csrf_token": "valid-token"})
            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            self.assertIn("job_id", data)
            background_thread.return_value.start.assert_called_once()
            with client.session_transaction() as browser_session:
                self.assertEqual(browser_session["export_job_id"], data["job_id"])
            response = client.get(data["status_url"])
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.get_json()["status"], "starting")
            with patch.object(moodle_ucnl, "Thread"):
                response = client.post(
                    f"/export/{data['job_id']}/cancel",
                    data={"csrf_token": "valid-token"},
                )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.get_json()["status"], "cancelling")
            with moodle_ucnl.EXPORT_JOBS_LOCK:
                job = moodle_ucnl.EXPORT_JOBS.pop(data["job_id"])
            moodle_ucnl.MOODLE_SESSIONS.pop("test-session").close()
            shutil.rmtree(temporary_dir, ignore_errors=True)

    def test_course_download_stream_releases_worker_only_after_delivery(self):
        client = moodle_ucnl.app.test_client()
        with tempfile.TemporaryDirectory() as parent:
            directory = Path(parent) / "job"
            directory.mkdir()
            archive_path = directory / "Curso [12].zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("TEMARIO.md", "# Curso\n")
            job = moodle_ucnl.ExportJob(
                job_id="ready-job",
                client=requests.Session(),
                directory=directory,
                status="running",
                ready_archive=archive_path,
                ready_name=archive_path.name,
            )
            with moodle_ucnl.EXPORT_JOBS_LOCK:
                moodle_ucnl.EXPORT_JOBS[job.job_id] = job
            with client.session_transaction() as browser_session:
                browser_session["export_job_id"] = job.job_id
            response = client.get(f"/export/{job.job_id}/course")
            archive_data = response.get_data()
            response.close()
            self.assertEqual(response.status_code, 200)
            self.assertTrue(job.download_event.is_set())
            with zipfile.ZipFile(io.BytesIO(archive_data)) as archive:
                self.assertIn("TEMARIO.md", archive.namelist())
            with moodle_ucnl.EXPORT_JOBS_LOCK:
                moodle_ucnl.EXPORT_JOBS.pop(job.job_id)

    def test_worker_prepares_and_delivers_each_course_without_a_combined_archive(self):
        client = moodle_ucnl.app.test_client()
        course = Course(
            "12",
            "Álgebra",
            "https://licenciatura.ucnl.edu.mx/course/view.php?id=12",
        )
        with tempfile.TemporaryDirectory() as parent:
            directory = Path(parent) / "job"
            job = moodle_ucnl.ExportJob(
                job_id="worker-job",
                client=requests.Session(),
                directory=directory,
            )
            with moodle_ucnl.EXPORT_JOBS_LOCK:
                moodle_ucnl.EXPORT_JOBS[job.job_id] = job

            def create_course_fixture(_client, item, output_dir, report, progress, _cancel):
                output = output_dir / f"{item.name} [{item.course_id}]"
                output.mkdir(parents=True)
                (output / "TEMARIO.md").write_text("# Álgebra\n", encoding="utf-8")
                report["courses"].append({"name": item.name})
                return output

            with (
                patch.object(moodle_ucnl, "course_pages", return_value=[course]),
                patch.object(moodle_ucnl, "export_course", side_effect=create_course_fixture),
            ):
                worker = Thread(target=moodle_ucnl.run_export_job, args=(job,))
                worker.start()
                for _ in range(200):
                    if job.snapshot()["ready"]:
                        break
                    time.sleep(0.01)
                self.assertTrue(job.snapshot()["ready"])
                with client.session_transaction() as browser_session:
                    browser_session["export_job_id"] = job.job_id
                response = client.get(f"/export/{job.job_id}/course")
                with zipfile.ZipFile(io.BytesIO(response.get_data())) as archive:
                    self.assertEqual(archive.namelist(), ["TEMARIO.md"])
                response.close()
                worker.join(timeout=2)
            self.assertFalse(worker.is_alive())
            self.assertEqual(job.snapshot()["status"], "complete")
            self.assertEqual(job.snapshot()["completed_courses"], 1)
            with moodle_ucnl.EXPORT_JOBS_LOCK:
                moodle_ucnl.EXPORT_JOBS.pop(job.job_id)

    def test_cancel_endpoint_stops_worker_waiting_to_deliver_a_course(self):
        client = moodle_ucnl.app.test_client()
        course = Course(
            "12",
            "Álgebra",
            "https://licenciatura.ucnl.edu.mx/course/view.php?id=12",
        )
        with tempfile.TemporaryDirectory() as parent:
            job = moodle_ucnl.ExportJob(
                job_id="cancel-job",
                client=requests.Session(),
                directory=Path(parent) / "job",
            )

            def create_course_fixture(_client, item, output_dir, report, progress, _cancel):
                output = output_dir / f"{item.name} [{item.course_id}]"
                output.mkdir(parents=True)
                (output / "TEMARIO.md").write_text("# Álgebra\n", encoding="utf-8")
                report["courses"].append({"name": item.name})
                return output

            with moodle_ucnl.EXPORT_JOBS_LOCK:
                moodle_ucnl.EXPORT_JOBS[job.job_id] = job
            with client.session_transaction() as browser_session:
                browser_session["csrf_token"] = "valid-token"
                browser_session["export_job_id"] = job.job_id
            with (
                patch.object(moodle_ucnl, "course_pages", return_value=[course]),
                patch.object(moodle_ucnl, "export_course", side_effect=create_course_fixture),
            ):
                worker = Thread(target=moodle_ucnl.run_export_job, args=(job,))
                worker.start()
                for _ in range(200):
                    if job.snapshot()["ready"]:
                        break
                    time.sleep(0.01)
                self.assertTrue(job.snapshot()["ready"])
                response = client.post(
                    f"/export/{job.job_id}/cancel",
                    data={"csrf_token": "valid-token"},
                )
                self.assertEqual(response.get_json()["status"], "cancelling")
                worker.join(timeout=2)
            self.assertFalse(worker.is_alive())
            self.assertEqual(job.snapshot()["status"], "cancelled")
            self.assertFalse(job.directory.exists())
            with moodle_ucnl.EXPORT_JOBS_LOCK:
                moodle_ucnl.EXPORT_JOBS.pop(job.job_id)


if __name__ == "__main__":
    unittest.main()
