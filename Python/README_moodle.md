# Exportador de cursos UCNL

Aplicación local para iniciar sesión en Moodle, enumerar los cursos visibles en
`/my/courses.php` y descargar un ZIP con la información y los recursos disponibles.

## Requisitos

- Python 3.10 o posterior
- Acceso válido a Moodle UCNL
- Las dependencias listadas en `requirements_moodle.txt`

Desde la carpeta `Python`, instala y ejecuta:

```powershell
py -m pip install -r requirements_moodle.txt
py moodle_ucnl.py
```

Abre <http://127.0.0.1:5000>, inicia sesión y elige **Preparar descargas por curso**.
La aplicación muestra el curso y recurso que procesa, el progreso de descarga y
ofrece un archivo ZIP por materia cuando queda listo. Puedes descargar cada materia
sin esperar a que terminen las demás y cancelar la exportación en cualquier momento.
La cancelación se aplica al terminar la solicitud HTTP que Moodle está atendiendo;
la interfaz indica cuando está esperando que esa solicitud concluya.
Al explorar subtemas, el estado indica el número de página que se está leyendo.
La exploración usa el área principal del contenido para no seguir los enlaces de
menús y navegación del tema.
Para evitar rastreos indefinidos, explora como máximo 20 páginas Moodle por curso
y usa un tiempo de espera de 20 segundos por página; si alcanza el límite, la
advertencia queda registrada en `curso.json`.
Cada ZIP incluye un `TEMARIO.md`, un `curso.json` con secciones, tutor(es)
detectados, enlaces y estado de descarga, y carpetas de recursos organizadas por
unidad. El apartado **Presentación** solo incluye la página del programa Moodle
`/mod/page/view.php?id=809871` y sus imágenes, omitiendo el foro y las demás
actividades de esa sección. En las otras unidades, la aplicación sigue páginas,
libros, recursos y enlaces Moodle anidados y recopila archivos e imágenes. Conserva
como enlaces, pero no rastrea recursivamente, los foros y otras actividades para
evitar recorrer publicaciones o conversaciones extensas.
Las imágenes que Moodle muestra en la información del curso también se guardan.
Los videos externos se registran como enlaces y no se descargan. El seguimiento se
limita al dominio Moodle de UCNL.

La aplicación está enlazada únicamente a `127.0.0.1`; no guarda la contraseña ni
los archivos descargados en el servidor. Las cookies de Moodle se conservan solo
en memoria mientras la aplicación está ejecutándose. La clave que firma la sesión
local persiste en `%LOCALAPPDATA%\UCNLMoodleExporter\session.key` para no cerrar la
sesión del panel al reiniciar Flask. Los trabajos de exportación todavía viven en
memoria y se pierden si se reinicia su proceso; ejecuta una sola instancia de la
aplicación durante cada exportación. Usa este exportador únicamente con una cuenta
autorizada y respeta las condiciones de uso de la plataforma.
