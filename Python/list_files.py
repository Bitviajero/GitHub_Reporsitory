import os
import argparse
from pathlib import Path

def generar_arbol_directorios(directorio_base, archivo_salida="estructura_cursos.txt", 
                            indent="", es_raiz=True, archivos=True, max_profundidad=None, 
                            profundidad=0, excluir_ocultos=True):
    """
    Genera un árbol de directorios y lo escribe en un archivo de texto.
    
    Args:
        directorio_base: Ruta del directorio raíz a explorar
        archivo_salida: Nombre del archivo de salida
        indent: Indentación actual (uso interno)
        es_raiz: Indica si es el directorio raíz (uso interno)
        archivos: Incluir archivos en la lista
        max_profundidad: Profundidad máxima a explorar (None = sin límite)
        profundidad: Nivel de profundidad actual (uso interno)
        excluir_ocultos: Omitir archivos/carpetas ocultos (que empiezan con .)
    """
    # Convertir a Path para mejor manejo
    ruta_base = Path(directorio_base)
    
    if not ruta_base.exists():
        print(f"❌ Error: El directorio '{directorio_base}' no existe.")
        return False
    
    if not ruta_base.is_dir():
        print(f"❌ Error: '{directorio_base}' no es un directorio.")
        return False
    
    # Preparar archivo de salida
    try:
        with open(archivo_salida, 'w', encoding='utf-8') as f:
            # Escribir encabezado
            f.write(f"📚 ESTRUCTURA DE CURSOS\n")
            f.write(f"📁 Directorio base: {ruta_base.absolute()}\n")
            f.write(f"{'='*60}\n\n")
            
            # Llamar a la función recursiva
            _recorrer_directorio(ruta_base, f, "", True, archivos, max_profundidad, 0, excluir_ocultos)
        
        print(f"✅ ¡Archivo generado exitosamente! '{archivo_salida}'")
        return True
        
    except Exception as e:
        print(f"❌ Error al escribir el archivo: {e}")
        return False

def _recorrer_directorio(ruta, archivo, prefijo, es_raiz, mostrar_archivos, 
                        max_profundidad, profundidad, excluir_ocultos):
    """
    Función recursiva para recorrer el directorio.
    """
    # Verificar límite de profundidad
    if max_profundidad is not None and profundidad > max_profundidad:
        return
    
    # Obtener el nombre del directorio actual
    nombre_dir = ruta.name if not es_raiz else ruta.name
    
    # Escribir el directorio actual
    if es_raiz:
        archivo.write(f"📁 {nombre_dir}/\n")
    else:
        archivo.write(f"{prefijo}📁 {nombre_dir}/\n")
    
    # Obtener contenidos (ordenados alfabéticamente)
    try:
        items = list(ruta.iterdir())
        # Filtrar ocultos si está activado
        if excluir_ocultos:
            items = [item for item in items if not item.name.startswith('.')]
        # Ordenar: primero carpetas, luego archivos
        carpetas = sorted([item for item in items if item.is_dir()])
        archivos_lista = sorted([item for item in items if item.is_file()])
        items = carpetas + archivos_lista
    except PermissionError:
        archivo.write(f"{prefijo}   ⚠️  [Sin permisos de lectura]\n")
        return
    
    # Preparar prefijos para la indentación
    nuevo_prefijo = prefijo + "   "
    
    # Contar items para saber cuándo es el último
    total_items = len(items)
    
    for idx, item in enumerate(items):
        es_ultimo = (idx == total_items - 1)
        conector = "└── " if es_ultimo else "├── "
        
        if item.is_dir():
            # Es una carpeta - recursión
            sub_prefijo = nuevo_prefijo if not es_ultimo else prefijo + "   "
            # Escribir el nombre de la subcarpeta
            archivo.write(f"{nuevo_prefijo}{conector}📁 {item.name}/\n")
            
            # Recursión con el nuevo prefijo
            _recorrer_directorio(item, archivo, sub_prefijo, False, mostrar_archivos, 
                                max_profundidad, profundidad + 1, excluir_ocultos)
        else:
            # Es un archivo
            if mostrar_archivos:
                # Obtener extensión para icono
                extension = item.suffix.lower()
                icono = "📄"
                if extension in ['.pdf']:
                    icono = "📕"
                elif extension in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
                    icono = "🖼️"
                elif extension in ['.mp4', '.avi', '.mov', '.mkv']:
                    icono = "🎬"
                elif extension in ['.mp3', '.wav', '.flac']:
                    icono = "🎵"
                elif extension in ['.zip', '.rar', '.7z']:
                    icono = "📦"
                elif extension in ['.py', '.js', '.html', '.css']:
                    icono = "💻"
                elif extension in ['.doc', '.docx', '.txt']:
                    icono = "📝"
                
                # Escribir archivo con su icono
                archivo.write(f"{nuevo_prefijo}{conector}{icono} {item.name}\n")

def main():
    """Función principal con interfaz de línea de comandos"""
    parser = argparse.ArgumentParser(
        description='Genera un archivo TXT con la estructura de carpetas de tus cursos',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python script.py /ruta/a/mis/cursos
  python script.py /ruta/a/mis/cursos -o estructura.txt
  python script.py /ruta/a/mis/cursos -s -p 2  (solo carpetas, profundidad 2)
  python script.py "C:/Mis Documentos/Cursos" -e   (excluye archivos ocultos)
        """
    )
    
    parser.add_argument('directorio', 
                        help='Ruta del directorio base de los cursos')
    
    parser.add_argument('-o', '--output', 
                        default='estructura_cursos.txt',
                        help='Nombre del archivo de salida (por defecto: estructura_cursos.txt)')
    
    parser.add_argument('-s', '--solo-carpetas', 
                        action='store_true',
                        help='Mostrar solo carpetas, omitir archivos')
    
    parser.add_argument('-p', '--profundidad', 
                        type=int, 
                        default=None,
                        help='Profundidad máxima a explorar (ej: -p 2)')
    
    parser.add_argument('-e', '--excluir-ocultos', 
                        action='store_true',
                        help='Excluir archivos y carpetas ocultos (que empiezan con .)')
    
    args = parser.parse_args()
    
    # Ejecutar la generación
    generar_arbol_directorios(
        directorio_base=args.directorio,
        archivo_salida=args.output,
        archivos=not args.solo_carpetas,
        max_profundidad=args.profundidad,
        excluir_ocultos=args.excluir_ocultos
    )

if __name__ == "__main__":
    main()