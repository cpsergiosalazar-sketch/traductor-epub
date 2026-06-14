import streamlit as st
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator
import os

def translate_html_content(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    translator = GoogleTranslator(source='en', target='es')
    
    for text_node in soup.find_all(string=True):
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
    
    os.remove("temp_input.epub")
    return output_path

# --- Interfaz Streamlit ---
st.set_page_config(page_title="ePUB Cloud Translator", page_icon="☁️")
st.title("☁️ Traductor de ePUB en la Nube")
st.write("Sube tu libro en inglés para traducirlo manteniendo el formato original.")

uploaded_file = st.file_uploader("Sube tu archivo .epub", type=['epub'])

if uploaded_file:
    if st.button("🚀 Iniciar Traducción"):
        try:
            with st.spinner("Traduciendo en los servidores de la nube... Esto puede tardar unos minutos."):
                result_file = process_epub(uploaded_file.getvalue(), uploaded_file.name)
            
            st.success("¡Traducción completada!")
            
            with open(result_file, "rb") as f:
                st.download_button(
                    label="📥 Descargar ePUB Traducido",
                    data=f,
                    file_name=result_file,
                    mime="application/epub+zip"
                )
            os.remove(result_file)
            
        except Exception as e:
            st.error(f"Error: {e}")
