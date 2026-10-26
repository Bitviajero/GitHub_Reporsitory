import os
import json
from pathlib import Path
import argparse
import webbrowser
import subprocess
import platform

class GeneradorHTMLCursos:
    def __init__(self, directorio_base, archivo_salida="cursos.html", 
                 abrir_videos=True, abrir_pdfs=True, excluir_ocultos=True):
        self.directorio_base = Path(directorio_base)
        self.archivo_salida = archivo_salida
        self.abrir_videos = abrir_videos
        self.abrir_pdfs = abrir_pdfs
        self.excluir_ocultos = excluir_ocultos
        self.estructura = {}
        self.ruta_relativa = None
        
    def generar_estructura(self):
        """Recorre el directorio y genera una estructura de datos"""
        if not self.directorio_base.exists() or not self.directorio_base.is_dir():
            print(f"❌ Error: El directorio '{self.directorio_base}' no existe o no es válido.")
            return False
        
        self.ruta_relativa = self.directorio_base.absolute()
        self.estructura = self._recorrer_directorio(self.directorio_base)
        return True
    
    def _recorrer_directorio(self, ruta):
        """Función recursiva para obtener estructura de carpetas y archivos"""
        estructura = {
            'nombre': ruta.name,
            'tipo': 'carpeta',
            'ruta': str(ruta.absolute()),
            'contenido': []
        }
        
        try:
            items = list(ruta.iterdir())
            if self.excluir_ocultos:
                items = [item for item in items if not item.name.startswith('.')]
            
            # Separar carpetas y archivos
            carpetas = sorted([item for item in items if item.is_dir()])
            archivos = sorted([item for item in items if item.is_file()])
            
            # Procesar carpetas
            for carpeta in carpetas:
                estructura['contenido'].append(self._recorrer_directorio(carpeta))
            
            # Procesar archivos
            for archivo in archivos:
                extension = archivo.suffix.lower()
                estructura['contenido'].append({
                    'nombre': archivo.name,
                    'tipo': 'archivo',
                    'extension': extension,
                    'ruta': str(archivo.absolute()),
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
            print("❌ Error: No se ha generado la estructura. Ejecuta generar_estructura() primero.")
            return False
        
        html = self._crear_html()
        
        try:
            with open(self.archivo_salida, 'w', encoding='utf-8') as f:
                f.write(html)
            print(f"✅ HTML generado exitosamente: {self.archivo_salida}")
            return True
        except Exception as e:
            print(f"❌ Error al guardar HTML: {e}")
            return False
    
    def _crear_html(self):
        """Crea el contenido HTML completo"""
        return f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📚 Estructura de Cursos</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
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
        
        .header .info {{
            color: #666;
            font-size: 0.9em;
        }}
        
        .header .info span {{
            background: #f0f0f0;
            padding: 5px 10px;
            border-radius: 5px;
            margin-left: 10px;
        }}
        
        .tree {{
            margin-top: 20px;
        }}
        
        .tree-item {{
            margin: 5px 0;
            padding-left: 0px;
        }}
        
        .tree-item .content {{
            display: flex;
            align-items: center;
            padding: 8px 12px;
            border-radius: 8px;
            transition: all 0.2s ease;
            cursor: default;
        }}
        
        .tree-item .content:hover {{
            background: #f8f9fa;
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
        
        .toggle-btn {{
            display: inline-block;
            width: 20px;
            height: 20px;
            line-height: 20px;
            text-align: center;
            margin-right: 10px;
            font-size: 14px;
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
        
        @media (max-width: 768px) {{
            .container {{
                padding: 15px;
            }}
            
            .header h1 {{
                font-size: 1.5em;
            }}
            
            .acciones {{
                flex-wrap: wrap;
            }}
            
            .btn {{
                font-size: 0.75em;
                padding: 3px 8px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div>
                <h1>📚 Estructura de Cursos</h1>
                <div class="info">
                    📁 <span>{self.directorio_base.name}</span>
                    📍 <span>{self.directorio_base.absolute()}</span>
                </div>
            </div>
            <div style="text-align: right;">
                <button onclick="expandirTodo()" class="btn btn-abrir" style="margin-right: 5px;">📂 Expandir todo</button>
                <button onclick="colapsarTodo()" class="btn btn-carpeta">📁 Colapsar todo</button>
            </div>
        </div>
        
        <div class="search-box">
            <input type="text" id="buscador" placeholder="🔍 Buscar archivos o carpetas..." onkeyup="buscar()">
        </div>
        
        <div class="tree" id="arbol">
            {self._generar_html_recursivo(self.estructura)}
        </div>
        
        <div class="stats" id="stats">
            <div>
                <div class="numero" id="total-carpetas">0</div>
                <div class="label">📁 Carpetas</div>
            </div>
            <div>
                <div class="numero" id="total-archivos">0</div>
                <div class="label">📄 Archivos</div>
            </div>
            <div>
                <div class="numero" id="total-videos">0</div>
                <div class="label">🎬 Videos</div>
            </div>
            <div>
                <div class="numero" id="total-pdfs">0</div>
                <div class="label">📕 PDFs</div>
            </div>
        </div>
    </div>
    
    <script>
        // Inicializar contadores
        let totalCarpetas = 0;
        let totalArchivos = 0;
        let totalVideos = 0;
        let totalPdfs = 0;
        
        function inicializarContadores() {{
            const items = document.querySelectorAll('.tree-item');
            items.forEach(item => {{
                if (item.classList.contains('folder')) {{
                    totalCarpetas++;
                }} else if (item.classList.contains('file')) {{
                    totalArchivos++;
                    const nombre = item.querySelector('.nombre').textContent.toLowerCase();
                    if (nombre.includes('.mp4') || nombre.includes('.avi') || nombre.includes('.mkv') || 
                        nombre.includes('.mov') || nombre.includes('.webm')) {{
                        totalVideos++;
                    }}
                    if (nombre.includes('.pdf')) {{
                        totalPdfs++;
                    }}
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
            document.querySelectorAll('.toggle-btn').forEach(el => {{
                el.classList.remove('collapsed');
            }});
        }}
        
        function colapsarTodo() {{
            document.querySelectorAll('.children').forEach(el => {{
                el.classList.add('hidden');
                el.classList.remove('show');
            }});
            document.querySelectorAll('.toggle-btn').forEach(el => {{
                el.classList.add('collapsed');
            }});
        }}
        
        function buscar() {{
            const input = document.getElementById('buscador');
            const filtro = input.value.toLowerCase().trim();
            const items = document.querySelectorAll('.tree-item');
            
            items.forEach(item => {{
                const nombre = item.querySelector('.nombre');
                if (!nombre) return;
                
                const texto = nombre.textContent.toLowerCase();
                if (filtro === '' || texto.includes(filtro)) {{
                    item.style.display = '';
                    // Mostrar padres
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
            const url = 'file:///' + ruta.replace(/\\\\/g, '/').replace(/:/g, '|');
            
            if (tipo === 'video' && {str(self.abrir_videos).lower()}) {{
                // Abrir en el navegador o reproductor
                window.open(url, '_blank');
            }} else if (tipo === 'pdf' && {str(self.abrir_pdfs).lower()}) {{
                window.open(url, '_blank');
            }} else {{
                window.open(url, '_blank');
            }}
        }}
        
        function abrirCarpeta(ruta) {{
            const url = 'file:///' + ruta.replace(/\\\\/g, '/').replace(/:/g, '|');
            window.open(url, '_blank');
        }}
        
        // Inicializar
        window.onload = function() {{
            inicializarContadores();
            
            // Por defecto colapsar todo excepto primer nivel
            document.querySelectorAll('.children').forEach(el => {{
                el.classList.add('hidden');
                // Si es primer nivel, mostrar
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
            html = f'<div class="tree-item folder">'
            html += f'<div class="content" onclick="toggleFolder(this)">'
            
            # Botón toggle
            if tiene_contenido:
                html += f'<span class="toggle-btn">▼</span>'
            else:
                html += f'<span class="toggle-btn" style="visibility:hidden;">•</span>'
            
            html += f'<span class="icon">📁</span>'
            html += f'<span class="nombre">{nodo["nombre"]}</span>'
            html += f'<div class="acciones">'
            html += f'<button class="btn btn-carpeta" onclick="event.stopPropagation(); abrirCarpeta(\'{nodo["ruta"]}\')">📂 Abrir</button>'
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
                'video': '🎬',
                'pdf': '📕',
                'documento': '📄',
                'texto': '📝',
                'imagen': '🖼️',
                'comprimido': '📦',
                'codigo': '💻',
                'otros': '📎'
            }
            icono = iconos.get(nodo['tipo_archivo'], '📄')
            
            # Determinar qué botones mostrar
            botones = ''
            if nodo['tipo_archivo'] == 'video' and self.abrir_videos:
                botones += f'<button class="btn btn-video" onclick="event.stopPropagation(); abrirArchivo(\'{nodo["ruta"]}\', \'video\')">▶ Ver</button>'
            elif nodo['tipo_archivo'] == 'pdf' and self.abrir_pdfs:
                botones += f'<button class="btn btn-pdf" onclick="event.stopPropagation(); abrirArchivo(\'{nodo["ruta"]}\', \'pdf\')">📖 Ver</button>'
            
            # Siempre mostrar botón de abrir
            botones += f'<button class="btn btn-abrir" onclick="event.stopPropagation(); abrirArchivo(\'{nodo["ruta"]}\', \'otros\')">📂 Abrir</button>'
            
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

def main():
    parser = argparse.ArgumentParser(
        description='Genera un HTML interactivo con la estructura de tus cursos',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python script_html.py "C:/Mis Cursos"
  python script_html.py "C:/Mis Cursos" -o "cursos.html"
  python script_html.py "C:/Mis Cursos" --no-videos  (no abre videos directamente)
  python script_html.py "C:/Mis Cursos" --mostrar-ocultos
        """
    )
    
    parser.add_argument('directorio', 
                        help='Ruta del directorio base de los cursos')
    
    parser.add_argument('-o', '--output', 
                        default='cursos.html',
                        help='Nombre del archivo HTML de salida (por defecto: cursos.html)')
    
    parser.add_argument('--no-videos', 
                        action='store_true',
                        help='No mostrar botones para abrir videos')
    
    parser.add_argument('--no-pdfs', 
                        action='store_true',
                        help='No mostrar botones para abrir PDFs')
    
    parser.add_argument('--mostrar-ocultos', 
                        action='store_true',
                        help='Mostrar archivos y carpetas ocultos')
    
    parser.add_argument('--abrir', 
                        action='store_true',
                        help='Abrir el HTML automáticamente en el navegador')
    
    args = parser.parse_args()
    
    # Crear generador
    generador = GeneradorHTMLCursos(
        directorio_base=args.directorio,
        archivo_salida=args.output,
        abrir_videos=not args.no_videos,
        abrir_pdfs=not args.no_pdfs,
        excluir_ocultos=not args.mostrar_ocultos
    )
    
    # Generar estructura
    if generador.generar_estructura():
        # Generar HTML
        if generador.generar_html():
            if args.abrir:
                print("🌐 Abriendo en el navegador...")
                webbrowser.open(args.output)

if __name__ == "__main__":
    main()