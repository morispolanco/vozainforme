import streamlit as st
import requests
import json
import os
import tempfile
import time

# Configuración de la página
st.set_page_config(
    page_title="Transcriptor de Notas Policiales",
    page_icon="🚔",
    layout="wide"
)

# Título y descripción
st.title("🚔 Transcriptor de Notas Policiales")
st.markdown("""
Esta aplicación te permite:
1. Subir un archivo de audio con notas policiales en español
2. Transcribir el audio usando Lemon Fox
3. Generar un reporte policial estructurado usando Dashscope (Qwen-Max)
""")

# Función para transcribir audio con Lemon Fox
def transcribe_audio(audio_file, language="spanish"):
    # Obtener API key de los secrets de Streamlit
    lemonfox_api_key = st.secrets["LEMONFOX_API_KEY"]
    
    # Endpoint de Lemon Fox
    url = "https://api.lemonfox.ai/v1/audio/transcriptions"
    
    # Configurar headers y datos
    headers = {
        "Authorization": f"Bearer {lemonfox_api_key}"
    }
    
    files = {
        "file": audio_file,
        "language": (None, language),
        "response_format": (None, "json")
    }
    
    with st.spinner("Transcribiendo audio..."):
        response = requests.post(url, headers=headers, files=files)
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error en la transcripción: {response.text}")
            return None

# Función para generar reporte policial con Dashscope
def generate_police_report(transcription):
    # Obtener API key de los secrets de Streamlit
    dashscope_api_key = st.secrets["DASHSCOPE_API_KEY"]
    
    # Endpoint de Dashscope
    url = "https://dashscope-intl.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
    
    # Configurar headers
    headers = {
        "Authorization": f"Bearer {dashscope_api_key}",
        "Content-Type": "application/json",
        "X-DashScope-SSE": "enable"
    }
    
    # Prompt para el sistema
    system_prompt = """Eres un asistente especializado en redactar reportes policiales profesionales.
    Tu tarea es convertir transcripciones de notas de audio en reportes policiales estructurados.
    El reporte debe incluir:
    
    1. Fecha y hora del incidente
    2. Ubicación
    3. Descripción de los hechos
    4. Personas involucradas
    5. Evidencia mencionada
    6. Acciones tomadas
    7. Recomendaciones
    
    Organiza la información de manera clara y profesional. Si alguna sección no tiene información disponible,
    indícalo como "No especificado". Mantén un tono formal y objetivo."""
    
    # Prompt para el usuario
    user_prompt = f"""Convierte la siguiente transcripción de audio en un reporte policial estructurado:
    
    {transcription}
    
    Por favor, extrae toda la información relevante y organízala según las secciones mencionadas."""
    
    # Datos para la solicitud
    data = {
        "model": "qwen-max",
        "input": {
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ]
        },
        "parameters": {
            "result_format": "message",
            "top_p": 0.8,
            "temperature": 0.7
        }
    }
    
    with st.spinner("Generando reporte policial..."):
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 200:
            result = response.json()
            # Extraer el contenido del mensaje de respuesta
            if "output" in result and "message" in result["output"]:
                return result["output"]["message"]["content"]
            else:
                st.error("Formato de respuesta inesperado")
                return None
        else:
            st.error(f"Error al generar el reporte: {response.text}")
            return None

# Interfaz principal
st.header("Subir archivo de audio")
uploaded_file = st.file_uploader("Selecciona un archivo de audio (.mp3, .wav, .m4a)", 
                                type=["mp3", "wav", "m4a"])

if uploaded_file is not None:
    # Mostrar reproductor de audio
    st.audio(uploaded_file, format=f"audio/{uploaded_file.name.split('.')[-1]}")
    
    # Botón para iniciar el proceso
    if st.button("Procesar Audio"):
        # Guardar el archivo temporalmente para procesarlo
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            temp_file_path = tmp_file.name
        
        try:
            # Abrir el archivo temporal para enviarlo a la API
            with open(temp_file_path, "rb") as audio_file:
                # Transcribir el audio
                transcription_result = transcribe_audio(audio_file)
                
                if transcription_result and "text" in transcription_result:
                    transcription_text = transcription_result["text"]
                    
                    # Mostrar la transcripción
                    st.header("Transcripción")
                    st.text_area("Texto transcrito", transcription_text, height=200)
                    
                    # Generar el reporte policial
                    police_report = generate_police_report(transcription_text)
                    
                    if police_report:
                        # Mostrar el reporte policial
                        st.header("Reporte Policial")
                        st.markdown(police_report)
                        
                        # Opción para descargar el reporte
                        st.download_button(
                            label="Descargar Reporte",
                            data=police_report,
                            file_name="reporte_policial.md",
                            mime="text/markdown"
                        )
        finally:
            # Eliminar el archivo temporal
            os.unlink(temp_file_path)

# Información adicional
st.sidebar.header("Información")
st.sidebar.info("""
### Sobre esta aplicación
Esta aplicación utiliza:
- **Lemon Fox API** para transcripción de audio
- **Dashscope API (Qwen-Max)** para generar reportes estructurados

### Idiomas soportados
Actualmente, la aplicación está optimizada para audio en español.
""")

# Footer
st.markdown("---")
st.markdown("Desarrollado con ❤️ usando Streamlit")
