import streamlit as st
import requests
import json
import os
from pydub import AudioSegment
import speech_recognition as sr

# Configuración de las API Keys desde los Secrets de Streamlit
LEMON_FOX_API_KEY = st.secrets["lemon_fox"]["api_key"]
DASHSCOPE_API_KEY = st.secrets["dashscope"]["api_key"]

# Función para transcribir audio usando SpeechRecognition
def transcribir_audio_desde_archivo(audio_file):
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_file) as source:
        audio = recognizer.record(source)
        try:
            texto = recognizer.recognize_google(audio, language="es-ES")
            return texto
        except sr.UnknownValueError:
            st.error("No se pudo entender el audio")
            return None
        except sr.RequestError:
            st.error("Error al conectar con el servicio de reconocimiento de voz")
            return None

# Función para generar el reporte policial usando Dashscope
def generar_reporte_policial(transcripcion):
    url = "https://dashscope-intl.aliyuncs.com"
    headers = {
        "Authorization": f"Bearer {DASHSCOPE_API_KEY}",
        "Content-Type": "application/json",
        "X-DashScope-SSE": "enable"
    }
    data = {
        "model": "qwen-max",
        "input": {
            "messages": [
                {"role": "system", "content": "Eres un asistente que ayuda a generar reportes policiales en español."},
                {"role": "user", "content": f"Organiza la siguiente transcripción en un reporte policial: {transcripcion}"}
            ]
        },
        "parameters": {
            "result_format": "message",
            "top_p": 0.8,
            "temperature": 1
        }
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Error al generar el reporte: {response.status_code}")
        return None

# Interfaz de Streamlit
st.title("Transcripción y Reporte Policial desde Archivo de Audio")

# Subir archivo de audio
audio_file = st.file_uploader("Sube un archivo de audio", type=["wav", "mp3"])

if audio_file is not None:
    # Guardar el archivo de audio temporalmente
    with open("temp_audio.wav", "wb") as f:
        f.write(audio_file.getbuffer())
    
    # Transcribir el audio
    st.write("Transcribiendo audio...")
    transcripcion = transcribir_audio_desde_archivo("temp_audio.wav")
    
    if transcripcion:
        st.write("Transcripción completada:")
        st.write(transcripcion)
        
        # Generar el reporte policial
        st.write("Generando reporte policial...")
        reporte = generar_reporte_policial(transcripcion)
        
        if reporte:
            st.write("Reporte policial generado:")
            st.write(reporte)
        else:
            st.error("No se pudo generar el reporte policial.")
    else:
        st.error("No se pudo transcribir el audio.")
else:
    st.warning("Por favor, sube un archivo de audio.")
