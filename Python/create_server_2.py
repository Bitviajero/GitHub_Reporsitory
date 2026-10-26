import os
import json
from pathlib import Path
import argparse
import webbrowser
import http.server
import socketserver
import threading
import time
import urllib.parse

class ServidorCursosHTTP(http.server.SimpleHTTPRequestHandler):
    """Handler personalizado para servir archivos correctamente"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Sobrescribir GET para manejar correctamente las rutas"""
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        
        # Decodificar URL
        path = urllib.parse.unquote(path)
        
        # Eliminar primer slash si existe
        if path.startswith('/'):
            path = path[1:]
        
        # Si es la raíz o archivo por defecto
        if not path or path == '':
            path = 'index.html'
        
        # Obtener la ruta completa
        full_path = os.path.join(self.directory, path)
        
        # Verificar si existe
        if os.path.exists(full_path):
            if os.path.isdir(full_path):
                # Si es directorio, listar archivos
                self.list_directory(full_path)
            else:
                # Servir archivo
                self.send_file(full_path)
        else:
            # Intentar buscar el archivo en el directorio base
            alt_path = os.path.join(os.getcwd(), path)
            if os.path.exists(alt_path):
                self.send_file(alt_path)
            else:
                self.send_error(404, f"Archivo no encontrado: {path}")
    
    def send_file(self, filepath):
        """Envía un archivo al cliente"""
        try:
            with open(filepath, 'rb') as f:
                content = f.read()
            
            # Determinar tipo MIME
            ext = os.path.splitext(filepath)[1].lower()
            content_type = self.get_mime_type(ext)
            
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(content)))
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_error(500, f"Error al leer archivo: {str(e)}")
    
    def get_mime_type(self, ext):
        """Obtiene el tipo MIME según la extensión"""
        mime_types = {
            '.html': 'text/html',
            '.css': 'text/css',
            '.js': 'application/javascript',
            '.json': 'application/json',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.svg': 'image/svg+xml',
            '.mp4': 'video/mp4',
            '.webm': 'video/webm',
            '.avi': 'video/x-msvideo',
            '.mov': 'video/quicktime',
            '.mkv': 'video/x-matroska',
            '.pdf': 'application/pdf',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.txt': 'text/plain',
            '.zip': 'application/zip',
            '.rar': 'application/x-rar-compressed',
        }
        return mime_types.get(ext, 'application/octet-stream')
    
    def log_message(self, format, *args):
        """Silenciar logs del servidor para no saturar la consola"""
        pass  # Descomentar para ver logs: print(format % args)

class GeneradorHTMLCompleto:
    def __init__(self, directorio_base, archivo_salida="index.html", 
                 puerto=8000, abrir_videos=True, abrir_pdfs=True, 
                 excluir_ocultos=True):
        self.directorio_base = Path(directorio_base).resolve()
        self.archivo_salida = archivo_salida
        self.puerto = puerto
        self.abrir_videos = abrir_videos
        self.abrir_pdfs = abrir_pdfs
        self.excluir_ocultos = excluir_ocultos
        self.estructura = {}
        self.base_name = self.directorio_base.name
        
    def generar_estructura(self):
        """Recorre el directorio y genera una estructura de datos"""
        if not self.directorio_base.exists() or not self.directorio_base.is_dir():
            print(f"❌ Error: El directorio '{self.directorio_base}' no existe o no es válido.")
            return False
        
        self.estructura = self._recorrer_directorio(self.directorio_base)
        return True
    
    def _recorrer_directorio(self, ruta):
        """Función recursiva para obtener estructura de carpetas y archivos"""
        # Obtener ruta relativa desde el directorio base
        try:
            ruta_relativa = str(ruta.relative_to(self.directorio_base))
            if ruta_relativa == '.':
                ruta_relativa = ''
        except ValueError:
            ruta_relativa = str(ruta)
        
        estructura = {
            'nombre': ruta.name,
            'tipo': 'carpeta',
            'ruta_relativa': ruta_relativa.replace('\\', '/'),
            'contenido': []
        }
        
        try:
            items = list(ruta.iterdir())
            if self.excluir_ocultos:
                items = [item for item in items if not item.name.startswith('.')]
            
            carpetas = sorted([item for item in items if item.is_dir()])
            archivos = sorted([item for item in items if item.is_file()])
            
            for carpeta in carpetas:
                estructura['contenido'].append(self._recorrer_directorio(carpeta))
            
            for archivo in archivos:
                extension = archivo.suffix.lower()
                # Obtener ruta relativa del archivo
                try:
                    ruta_archivo = str(archivo.relative_to(self.directorio_base)).replace('\\', '/')
                except ValueError:
                    ruta_archivo = str(archivo)
                
                estructura['contenido'].append({
                    'nombre': archivo.name,
                    'tipo': 'archivo',
                    'extension': extension,
                    'ruta_relativa': ruta_archivo,
                    'tipo_archivo': self._clasificar_archivo(extension)
                })
                
        except PermissionError:
            estructura['contenido'].append({
                'nombre': '⚠️ Sin permisos de acceso',
                'tipo': 'error'
            })
        
        return estructura
    
    def _clasificar_archivo(self, extension):
        """Clasifica el archivo según su extensión"""
        tipos = {
            '.mp4': 'video', '.avi': 'video', '.mov': 'video', '.mkv': 'video',
            '.webm': 'video', '.flv': 'video', '.wmv': 'video',
            '.pdf': 'pdf', '.doc': 'documento', '.docx': 'documento',
            '.txt': 'texto', '.md': 'texto',
            '.jpg': 'imagen', '.jpeg': 'imagen', '.png': 'imagen',
            '.gif': 'imagen', '.bmp': 'imagen', '.svg': 'imagen',
            '.zip': 'comprimido', '.rar': 'comprimido', '.7z': 'comprimido',
            '.py': 'codigo', '.js': 'codigo', '.html': 'codigo',
            '.css': 'codigo', '.cpp': 'codigo', '.java': 'codigo'
        }
        return tipos.get(extension, 'otros')
    
    def generar_html(self):
        """Genera el archivo HTML con la estructura interactiva"""
        if not self.estructura:
            print("❌ Error: No se ha generado la estructura.")
            return False
        
        html = self._crear_html()
        
        # Guardar en el directorio base
        ruta_salida = self.directorio_base / self.archivo_salida
        
        try:
            with open(ruta_salida, 'w', encoding='utf-8') as f:
                f.write(html)
            print(f"✅ HTML generado exitosamente: {ruta_salida}")
            return True
        except Exception as e:
            print(f"❌ Error al guardar HTML: {e}")
            return False
    
    def _crear_html(self):
        """Crea el contenido HTML completo"""
        # Escapar caracteres especiales para JavaScript
        def escape_js(texto):
            return texto.replace('\\', '\\\\').replace("'", "\\'").replace('"', '\\"')
        
        return f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📚 {self.base_name}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            padding: 30px;
        }}
        
        .header {{
            border-bottom: 3px solid #667eea;
            padding-bottom: 20px;
            margin-bottom: 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
        }}
        
        .header h1 {{
            color: #333;
            font-size: 2em;
        }}
        
        .server-info {{
            background: #28a745;
            color: white;
            padding: 8px 15px;
            border-radius: 8px;
            font-size: 0.9em;
            display: inline-block;
        }}
        
        .tree-item {{
            margin: 5px 0;
        }}
        
        .tree-item .content {{
            display: flex;
            align-items: center;
            padding: 8px 12px;
            border-radius: 8px;
            transition: all 0.2s ease;
        }}
        
        .tree-item.folder > .content {{
            cursor: pointer;
            font-weight: 600;
        }}
        
        .tree-item.folder > .content:hover {{
            background: #e8edfd;
        }}
        
        .tree-item.file .content {{
            padding-left: 20px;
        }}
        
        .tree-item.file .content:hover {{
            background: #f8f9fa;
        }}
        
        .toggle-btn {{
            display: inline-block;
            width: 20px;
            height: 20px;
            line-height: 20px;
            text-align: center;
            margin-right: 10px;
            font-weight: bold;
            transition: transform 0.3s ease;
            border-radius: 4px;
            background: #f0f0f0;
            color: #555;
            user-select: none;
        }}
        
        .toggle-btn.collapsed {{
            transform: rotate(-90deg);
        }}
        
        .icon {{
            font-size: 1.3em;
            margin-right: 10px;
        }}
        
        .nombre {{
            flex: 1;
            color: #333;
            font-size: 1em;
        }}
        
        .acciones {{
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
        }}
        
        .btn {{
            padding: 4px 12px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 0.85em;
            transition: all 0.2s ease;
            text-decoration: none;
            display: inline-block;
        }}
        
        .btn-video {{
            background: #dc3545;
            color: white;
        }}
        
        .btn-video:hover {{
            background: #c82333;
            transform: scale(1.05);
        }}
        
        .btn-pdf {{
            background: #28a745;
            color: white;
        }}
        
        .btn-pdf:hover {{
            background: #218838;
            transform: scale(1.05);
        }}
        
        .btn-abrir {{
            background: #007bff;
            color: white;
        }}
        
        .btn-abrir:hover {{
            background: #0069d9;
            transform: scale(1.05);
        }}
        
        .btn-carpeta {{
            background: #6c757d;
            color: white;
        }}
        
        .btn-carpeta:hover {{
            background: #5a6268;
            transform: scale(1.05);
        }}
        
        .children {{
            padding-left: 30px;
            overflow: hidden;
            transition: max-height 0.3s ease;
        }}
        
        .children.hidden {{
            max-height: 0;
        }}
        
        .children.show {{
            max-height: 5000px;
        }}
        
        .empty {{
            color: #999;
            font-style: italic;
            padding: 10px 20px;
        }}
        
        .stats {{
            background: #f8f9fa;
            padding: 15px 20px;
            border-radius: 10px;
            margin-top: 30px;
            display: flex;
            justify-content: space-around;
            flex-wrap: wrap;
            gap: 15px;
        }}
        
        .stats div {{
            text-align: center;
        }}
        
        .stats .numero {{
            font-size: 1.8em;
            font-weight: bold;
            color: #667eea;
        }}
        
        .stats .label {{
            color: #666;
            font-size: 0.9em;
        }}
        
        .search-box {{
            margin: 20px 0;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 10px;
        }}
        
        .search-box input {{
            width: 100%;
            padding: 12px 15px;
            border: 2px solid #ddd;
            border-radius: 8px;
            font-size: 1em;
            transition: border-color 0.3s ease;
        }}
        
        .search-box input:focus {{
            outline: none;
            border-color: #667eea;
        }}
        
        .video-modal {{
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.9);
            justify-content: center;
            align-items: center;
        }}
        
        .video-modal.show {{
            display: flex;
        }}
        
        .video-modal video {{
            max-width: 90%;
            max-height: 90%;
            border-radius: 10px;
            box-shadow: 0 0 50px rgba(0,0,0,0.5);
        }}
        
        .video-modal .close {{
            position: absolute;
            top: 20px;
            right: 40px;
            color: white;
            font-size: 40px;
            cursor: pointer;
        }}
        
        @media (max-width: 768px) {{
            .container {{ padding: 15px; }}
            .header h1 {{ font-size: 1.5em; }}
            .acciones {{ flex-wrap: wrap; }}
            .btn {{ font-size: 0.75em; padding: 3px 8px; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div>
                <h1>📚 {self.base_name}</h1>
                <div style="margin-top: 5px; color: #666;">
                    📁 <span style="background: #f0f0f0; padding: 3px 10px; border-radius: 5px;">{self.directorio_base}</span>
                </div>
            </div>
            <div>
                <span class="server-info">🌐 Servidor: http://localhost:{self.puerto}</span>
                <br>
                <button onclick="expandirTodo()" class="btn btn-abrir" style="margin-top: 5px;">📂 Expandir todo</button>
                <button onclick="colapsarTodo()" class="btn btn-carpeta" style="margin-top: 5px;">📁 Colapsar todo</button>
            </div>
        </div>
        
        <div class="search-box">
            <input type="text" id="buscador" placeholder="🔍 Buscar archivos o carpetas..." onkeyup="buscar()">
        </div>
        
        <div class="tree" id="arbol">
            {self._generar_html_recursivo(self.estructura)}
        </div>
        
        <div class="stats">
            <div><div class="numero" id="total-carpetas">0</div><div class="label">📁 Carpetas</div></div>
            <div><div class="numero" id="total-archivos">0</div><div class="label">📄 Archivos</div></div>
            <div><div class="numero" id="total-videos">0</div><div class="label">🎬 Videos</div></div>
            <div><div class="numero" id="total-pdfs">0</div><div class="label">📕 PDFs</div></div>
        </div>
    </div>
    
    <!-- Modal para videos -->
    <div id="videoModal" class="video-modal" onclick="cerrarVideo()">
        <span class="close">&times;</span>
        <video id="videoPlayer" controls>
            <source src="" type="video/mp4">
            Tu navegador no soporta la reproducción de videos.
        </video>
    </div>
    
    <script>
        let totalCarpetas = 0, totalArchivos = 0, totalVideos = 0, totalPdfs = 0;
        
        function inicializarContadores() {{
            document.querySelectorAll('.tree-item').forEach(item => {{
                if (item.classList.contains('folder')) totalCarpetas++;
                else if (item.classList.contains('file')) {{
                    totalArchivos++;
                    const nombre = item.querySelector('.nombre').textContent.toLowerCase();
                    if (nombre.includes('.mp4') || nombre.includes('.avi') || nombre.includes('.mkv') || 
                        nombre.includes('.mov') || nombre.includes('.webm')) totalVideos++;
                    if (nombre.includes('.pdf')) totalPdfs++;
                }}
            }});
            document.getElementById('total-carpetas').textContent = totalCarpetas;
            document.getElementById('total-archivos').textContent = totalArchivos;
            document.getElementById('total-videos').textContent = totalVideos;
            document.getElementById('total-pdfs').textContent = totalPdfs;
        }}
        
        function toggleFolder(element) {{
            const item = element.closest('.tree-item');
            const children = item.querySelector('.children');
            const toggle = element.querySelector('.toggle-btn');
            if (children) {{
                if (children.classList.contains('hidden')) {{
                    children.classList.remove('hidden');
                    children.classList.add('show');
                    if (toggle) toggle.classList.remove('collapsed');
                }} else {{
                    children.classList.add('hidden');
                    children.classList.remove('show');
                    if (toggle) toggle.classList.add('collapsed');
                }}
            }}
        }}
        
        function expandirTodo() {{
            document.querySelectorAll('.children').forEach(el => {{
                el.classList.remove('hidden');
                el.classList.add('show');
            }});
            document.querySelectorAll('.toggle-btn').forEach(el => el.classList.remove('collapsed'));
        }}
        
        function colapsarTodo() {{
            document.querySelectorAll('.children').forEach(el => {{
                el.classList.add('hidden');
                el.classList.remove('show');
            }});
            document.querySelectorAll('.toggle-btn').forEach(el => el.classList.add('collapsed'));
        }}
        
        function buscar() {{
            const filtro = document.getElementById('buscador').value.toLowerCase().trim();
            document.querySelectorAll('.tree-item').forEach(item => {{
                const nombre = item.querySelector('.nombre');
                if (!nombre) return;
                const texto = nombre.textContent.toLowerCase();
                if (filtro === '' || texto.includes(filtro)) {{
                    item.style.display = '';
                    let parent = item.closest('.tree-item');
                    while (parent) {{
                        const children = parent.querySelector('.children');
                        if (children) {{
                            children.classList.remove('hidden');
                            children.classList.add('show');
                            const toggle = parent.querySelector('.toggle-btn');
                            if (toggle) toggle.classList.remove('collapsed');
                        }}
                        parent = parent.parentElement?.closest('.tree-item');
                    }}
                }} else {{
                    item.style.display = 'none';
                }}
            }});
        }}
        
        function abrirArchivo(ruta, tipo) {{
            // Construir URL correcta
            const url = '/' + ruta;
            console.log('Abriendo:', url);
            
            if (tipo === 'video') {{
                const modal = document.getElementById('videoModal');
                const video = document.getElementById('videoPlayer');
                video.src = url;
                modal.classList.add('show');
                video.play().catch(e => {{
                    console.error('Error al reproducir:', e);
                    // Si falla, abrir en nueva pestaña
                    window.open(url, '_blank');
                }});
            }} else if (tipo === 'pdf') {{
                window.open(url, '_blank');
            }} else {{
                window.open(url, '_blank');
            }}
        }}
        
        function cerrarVideo() {{
            const modal = document.getElementById('videoModal');
            const video = document.getElementById('videoPlayer');
            video.pause();
            video.src = '';
            modal.classList.remove('show');
        }}
        
        function abrirCarpeta(ruta) {{
            const url = '/' + ruta;
            window.open(url, '_blank');
        }}
        
        // Inicializar
        window.onload = function() {{
            inicializarContadores();
            document.querySelectorAll('.children').forEach(el => {{
                el.classList.add('hidden');
                if (el.closest('.tree-item').parentElement.id === 'arbol') {{
                    el.classList.remove('hidden');
                    el.classList.add('show');
                }}
            }});
            document.querySelectorAll('.toggle-btn').forEach(el => {{
                const parent = el.closest('.tree-item');
                if (parent && parent.parentElement?.id !== 'arbol') {{
                    el.classList.add('collapsed');
                }}
            }});
        }};
    </script>
</body>
</html>"""
    
    def _generar_html_recursivo(self, nodo, nivel=0):
        """Genera HTML recursivo para la estructura"""
        if nodo['tipo'] == 'error':
            return f'<div class="tree-item"><div class="content"><span class="nombre">⚠️ {nodo["nombre"]}</span></div></div>'
        
        if nodo['tipo'] == 'carpeta':
            tiene_contenido = len(nodo['contenido']) > 0
            # Escapar ruta para JavaScript
            ruta_js = nodo['ruta_relativa'].replace("'", "\\'")
            
            html = f'<div class="tree-item folder">'
            html += f'<div class="content" onclick="toggleFolder(this)">'
            if tiene_contenido:
                html += f'<span class="toggle-btn">▼</span>'
            else:
                html += f'<span class="toggle-btn" style="visibility:hidden;">•</span>'
            html += f'<span class="icon">📁</span>'
            html += f'<span class="nombre">{nodo["nombre"]}</span>'
            html += f'<div class="acciones">'
            html += f'<button class="btn btn-carpeta" onclick="event.stopPropagation(); abrirCarpeta(\'{ruta_js}\')">📂 Abrir</button>'
            html += f'</div>'
            html += f'</div>'
            if tiene_contenido:
                html += f'<div class="children">'
                for item in nodo['contenido']:
                    html += self._generar_html_recursivo(item, nivel + 1)
                html += f'</div>'
            else:
                html += f'<div class="children"><div class="empty">📭 Carpeta vacía</div></div>'
            html += f'</div>'
            return html
        
        elif nodo['tipo'] == 'archivo':
            iconos = {
                'video': '🎬', 'pdf': '📕', 'documento': '📄',
                'texto': '📝', 'imagen': '🖼️', 'comprimido': '📦',
                'codigo': '💻', 'otros': '📎'
            }
            icono = iconos.get(nodo['tipo_archivo'], '📄')
            
            # Escapar ruta para JavaScript
            ruta_js = nodo['ruta_relativa'].replace("'", "\\'")
            
            botones = ''
            if nodo['tipo_archivo'] == 'video' and self.abrir_videos:
                botones += f'<button class="btn btn-video" onclick="event.stopPropagation(); abrirArchivo(\'{ruta_js}\', \'video\')">▶ Ver</button>'
            elif nodo['tipo_archivo'] == 'pdf' and self.abrir_pdfs:
                botones += f'<button class="btn btn-pdf" onclick="event.stopPropagation(); abrirArchivo(\'{ruta_js}\', \'pdf\')">📖 Ver</button>'
            
            botones += f'<button class="btn btn-abrir" onclick="event.stopPropagation(); abrirArchivo(\'{ruta_js}\', \'otros\')">📂 Abrir</button>'
            
            html = f'<div class="tree-item file">'
            html += f'<div class="content">'
            html += f'<span class="toggle-btn" style="visibility:hidden;">•</span>'
            html += f'<span class="icon">{icono}</span>'
            html += f'<span class="nombre">{nodo["nombre"]}</span>'
            html += f'<div class="acciones">{botones}</div>'
            html += f'</div>'
            html += f'</div>'
            return html
        
        return ''

def iniciar_servidor(directorio, puerto=8000):
    """Inicia el servidor HTTP en el directorio especificado"""
    os.chdir(directorio)
    
    handler = ServidorCursosHTTP
    
    try:
        with socketserver.TCPServer(("", puerto), handler) as httpd:
            print(f"\n{'='*60}")
            print(f"✅ Servidor iniciado correctamente")
            print(f"📁 Sirviendo: {directorio}")
            print(f"🌐 URL: http://localhost:{puerto}")
            print(f"📄 HTML: http://localhost:{puerto}/index.html")
            print(f"{'='*60}")
            print("⏹️  Presiona Ctrl+C para detener el servidor\n")
            
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n⏹️  Servidor detenido")
    except Exception as e:
        print(f"❌ Error al iniciar servidor: {e}")

def main():
    parser = argparse.ArgumentParser(
        description='Genera HTML interactivo con servidor local',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python script.py "C:/Mis Cursos"
  python script.py "C:/Mis Cursos" -p 8080 --abrir
  python script.py "C:/Mis Cursos" --no-videos
        """
    )
    
    parser.add_argument('directorio', help='Ruta del directorio base de los cursos')
    parser.add_argument('-o', '--output', default='index.html', help='Nombre del HTML (default: index.html)')
    parser.add_argument('-p', '--puerto', type=int, default=8000, help='Puerto del servidor (default: 8000)')
    parser.add_argument('--no-videos', action='store_true', help='No mostrar botones de video')
    parser.add_argument('--no-pdfs', action='store_true', help='No mostrar botones de PDF')
    parser.add_argument('--mostrar-ocultos', action='store_true', help='Mostrar archivos ocultos')
    parser.add_argument('--abrir', action='store_true', help='Abrir automáticamente en navegador')
    parser.add_argument('--no-servidor', action='store_true', help='Solo generar HTML sin iniciar servidor')
    
    args = parser.parse_args()
    
    # Generar HTML
    generador = GeneradorHTMLCompleto(
        directorio_base=args.directorio,
        archivo_salida=args.output,
        puerto=args.puerto,
        abrir_videos=not args.no_videos,
        abrir_pdfs=not args.no_pdfs,
        excluir_ocultos=not args.mostrar_ocultos
    )
    
    if generador.generar_estructura():
        if generador.generar_html():
            if args.abrir:
                url = f"http://localhost:{args.puerto}/{args.output}"
                print(f"🌐 Abriendo en navegador: {url}")
                webbrowser.open(url)
            
            if not args.no_servidor:
                # Iniciar servidor
                iniciar_servidor(str(generador.directorio_base), args.puerto)

if __name__ == "__main__":
    main()