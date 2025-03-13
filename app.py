import streamlit as st
import requests
import json
from io import BytesIO

# Configuración de la página
st.set_page_config(page_title="Transcripción a Reporte Policial", layout="wide")

# Título
st.title("Convertidor de Notas de Audio a Reporte Policial")

# Función para transcribir audio usando Lemon Fox
def transcribe_audio(audio_file):
    url = "https://api.lemonfox.ai/v1/audio/transcriptions"
    headers = {
        "Authorization": f"Bearer {st.secrets['LEMONFOX_API_KEY']}"
    }
    files = {
        "file": audio_file,
        "language": (None, "spanish"),
        "response_format": (None, "json")
    }
    
    try:
        response = requests.post(url, headers=headers, files=files)
        response.raise_for_status()
        return response.json()["text"]
    except Exception as e:
        st.error(f"Error en la transcripción: {str(e)}")
        return None

# Función para generar reporte policial usando Dashscope
def generate_police_report(transcription):
    url = "https://dashscope-intl.aliyuncs.com"
    headers = {
        "Authorization": f"Bearer {st.secrets['DASHSCOPE_API_KEY']}",
        "Content-Type": "application/json",
        "X-DashScope-SSE": "enable"
    }
    
    prompt = f"""Convierte el siguiente texto en un reporte policial formal en español. 
    Usa un formato profesional con secciones claras como: 
    1. Datos del reporte
    2. Declaración
    3. Observaciones
    Mantén la información original pero organízala adecuadamente:
    
    {transcription}"""
    
    payload = {
        "model": "qwen-max",
        "input": {
            "messages": [
                {
                    "role": "system",
                    "content": "Eres un asistente policial experto en redactar reportes formales"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        },
        "parameters": {
            "result_format": "message",
            "top_p": 0.8,
            "temperature": 1
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()["output"]["choices"][0]["message"]["content"]
    except Exception as e:
        st.error(f"Error al generar reporte: {str(e)}")
        return None

# Interfaz de usuario
audio_file = st.file_uploader("Sube tu nota de audio", type=['mp3', 'wav', 'm4a'])

if audio_file is not None:
    # Mostrar detalles del archivo
    st.audio(audio_file)
    
    if st.button("Procesar Audio"):
        with st.spinner("Transcribiendo audio..."):
            transcription = transcribe_audio(audio_file)
            
        if transcription:
            st.subheader("Transcripción")
            st.write(transcription)
            
            with st.spinner("Generando reporte policial..."):
                report = generate_police_report(transcription)
                
            if report:
                st.subheader("Reporte Policial")
                st.markdown(report)
                
                # Opción para descargar el reporte
                st.download_button(
                    label="Descargar Reporte",
                    data=report,
                    file_name="reporte_policial.txt",
                    mime="text/plain"
                )
