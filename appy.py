import streamlit as st
import streamlit.components.v1 as components
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator
import os

def translate_html_content(html_content):
    """Traduce el contenido de texto dentro del HTML respetando las etiquetas de formato."""
    soup = BeautifulSoup(html_content, 'html.parser')
    translator = GoogleTranslator(source='en', target='es')
    
    for text_node in soup.find_all(string=True):
        # Evitar traducir scripts, estilos o el título técnico del HTML
        if text_node.parent.name in ['script', 'style', 'title']:
            continue
        
        original_text = text_node.strip()
        if original_text and len(original_text) > 1:
            try:
                translated = translator.translate(original_text)
                text_node.replace_with(translated)
            except Exception:
                continue
                
    return str(soup)

def process_epub(file_bytes, filename):
    """Procesa el ePUB capítulo por capítulo actualizando la interfaz."""
    with open("temp_input.epub", "wb") as f:
        f.write(file_bytes)
    
    book = epub.read_epub("temp_input.epub")
    docs = [item for item in book.get_items() if item.get_type() == ebooklib.ITEM_DOCUMENT]
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, item in enumerate(docs):
        status_text.text(f"Traduciendo capítulo {i+1} de {len(docs)}...")
        translated_html = translate_html_content(item.get_content())
        item.set_content(translated_html.encode('utf-8'))
        progress_bar.progress((i + 1) / len(docs))
    
    output_path = f"Traducido_{filename}"
    epub.write_epub(output_path, book)
    
    # Limpiar elementos de progreso y archivos temporales
    progress_bar.empty()
    status_text.empty()
    os.remove("temp_input.epub")
    return output_path

# --- INTERFAZ GRÁFICA (STREAMLIT) ---
st.set_page_config(page_title="ePUB Cloud Translator", page_icon="☁️", layout="centered")
st.title("☁️ Traductor de ePUB en la Nube")

# CÓDIGO ANTI-BLOQUEO: Intenta mantener la pantalla encendida mientras la pestaña esté visible
components.html(
    """
    <script>
    let wakeLock = null;
    async function requestWakeLock() {
        try {
            wakeLock = await navigator.wakeLock.request('screen');
            console.log('Wake Lock activado: la pantalla no se apagará automáticamente.');
        } catch (err) {
            console.log('Wake Lock no soportado o denegado por el navegador.');
        }
    }
    requestWakeLock();
    document.addEventListener('visibilitychange', async () => {
        if (wakeLock !== null && document.visibilityState === 'visible') {
            await requestWakeLock();
        }
    });
    </script>
    """,
    height=0,
)

st.write("Sube tu libro en inglés para traducirlo al español manteniendo imágenes, negritas y capítulos.")

uploaded_file = st.file_uploader("Sube tu archivo .epub", type=['epub'])

if uploaded_file:
    # Inicializar el estado de la sesión si no existe
    if 'traducido' not in st.session_state:
        st.session_state.traducido = False
        st.session_state.archivo_resultado = ""

    # BLOQUE 1: Traducción (Se muestra si aún no se ha procesado el archivo)
    if not st.session_state.traducido:
        if st.button("🚀 Iniciar Traducción", use_container_width=True):
            try:
                with st.spinner("Traduciendo en la nube... Por favor, mantén esta pestaña abierta."):
                    result_file = process_epub(uploaded_file.getvalue(), uploaded_file.name)
                
                st.session_state.traducido = True
                st.session_state.archivo_resultado = result_file
                st.rerun() # Fuerza el refresco para ocultar este botón y mostrar el de descarga
                
            except Exception as e:
                st.error(f"Ocurrió un error inesperado: {e}")

    # BLOQUE 2: Descarga (Se muestra automáticamente al terminar)
    else:
        st.success("🎉 ¡Traducción completada con éxito!")
        
        try:
            with open(st.session_state.archivo_resultado, "rb") as f:
                st.download_button(
                    label="📥 ¡LISTO! TOCAR AQUÍ PARA DESCARGAR TU LIBRO",
                    data=f,
                    file_name=st.session_state.archivo_resultado,
                    mime="application/epub+zip",
                    use_container_width=True,
                    type="primary" # Resalta el botón en azul/color principal
                )
        except Exception as e:
            st.error(f"Error al preparar el archivo de descarga: {e}")
            
        # Opción para reiniciar el estado y traducir otro libro
        if st.button("🔄 Traducir otro libro", use_container_width=True):
            if os.path.exists(st.session_state.archivo_resultado):
                os.remove(st.session_state.archivo_resultado)
            st.session_state.traducido = False
            st.session_state.archivo_resultado = ""
            st.rerun()
