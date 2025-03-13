
import streamlit as st
import pyaudio
import wave
import json
import requests
import base64
import os

# Cargar API Keys desde secrets
from streamlit import secrets
lemonfox_api_key = secrets["lemonfox_api_key"]
dashscope_api_key = secrets["dashscope_api_key"]

# Configuración de la aplicación
st.title("Transcripción de audio y generación de reporte policial")

# Configuración del micrófono
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100
RECORD_SECONDS = 5
WAVE_OUTPUT_FILENAME = "output.wav"

# Función para grabar audio
def grabar_audio():
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)
    print("Grabando audio...")
    frames = []
    for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(data)
    print("Grabación finalizada.")
    stream.stop_stream()
    stream.close()
    p.terminate()
    wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()

# Función para transcribir audio con Lemon Fox
def transcribir_audio():
    url = "https://api.lemonfox.ai/v1/audio/transcriptions"
    headers = {
        "Authorization": f"Bearer {lemonfox_api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "file": f"https://output.lemonfox.ai/{WAVE_OUTPUT_FILENAME}",
        "language": "spanish",
        "response_format": "json"
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))
    return response.json()

# Función para generar reporte policial con Dashscope
def generar_reporte_policial(transcripcion):
    url = "https://dashscope-intl.aliyuncs.com"
    headers = {
        "Authorization": f"Bearer {dashscope_api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "qwen-max",
        "input": {
            "messages": [
                {"role": "system", "content": ""},
                {"role": "user", "content": transcripcion}
            ]
        },
        "parameters": {
            "result_format": "message",
            "top_p": 0.8,
            "temperature": 1
        }
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))
    return response.json()

# Grabar audio
if st.button("Grabar audio"):
    grabar_audio()

# Transcribir audio
if st.button("Transcribir audio"):
    transcripcion = transcribir_audio()
    st.write(transcripcion)

# Generar reporte policial
if st.button("Generar reporte policial"):
    if "transcripcion" in st.session_state:
        reporte = generar_reporte_policial(st.session_state.transcripcion)
        st.write(reporte)
    else:
        st.error("No hay transcripción disponible")
