import streamlit as st
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase, WebRtcMode
import requests
import json
import queue
import numpy as np
from io import BytesIO
import soundfile as sf

# Configuración de la página
st.set_page_config(page_title="Transcripción a Reporte Policial")

# Título
st.title("Convertidor de Notas de Audio a Reporte Policial (Micrófono)")

# Cola para almacenar los datos de audio
audio_queue = queue.Queue()

# Clase para procesar el audio del micrófono
class AudioProcessor(AudioProcessorBase):
    def __init__(self):
        self.audio_buffer = []
        self.sample_rate = 16000  # Frecuencia de muestreo fija

    def recv(self, frame):
        try:
            audio_data = frame.to_ndarray()
            self.audio_buffer.append(audio_data)
            audio_queue.put(audio_data)
            return frame
        except Exception as e:
            st.error(f"Error al procesar audio: {str(e)}")
            return frame

    def get_audio_data(self):
        if self.audio_buffer:
            try:
                return np.concatenate(self.audio_buffer)
            except Exception as e:
                st.error(f"Error al concatenar audio: {str(e)}")
                return None
        return None

# Función para transcribir audio usando Lemon Fox
def transcribe_audio(audio_data):
    url = "https://api.lemonfox.ai/v1/audio/transcriptions"
    headers = {
        "Authorization": f"Bearer {st.secrets['LEMONFOX_API_KEY']}"
    }
    
    # Convertir audio a formato WAV
    buffer = BytesIO()
    try:
        sf.write(buffer, audio_data, 16000, format='WAV')
        buffer.seek(0)
    except Exception as e:
        st.error(f"Error al convertir audio a WAV: {str(e)}")
        return None
    
    files = {
        "file": ("audio.wav", buffer, "audio/wav"),
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
                {"role": "system", "content": "Eres un asistente policial experto en redactar reportes formales"},
                {"role": "user", "content": prompt}
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

# Interfaz de usuario con micrófono
st.subheader("Grabación de Audio")
ctx = webrtc_streamer(
    key="audio",
    mode=WebRtcMode.SENDONLY,  # Solo envía audio, no recibe
    audio_processor_factory=AudioProcessor,
    media_stream_constraints={"audio": True, "video": False},
    async_processing=True  # Procesamiento asíncrono para evitar bloqueos
)

# Estado de la sesión para manejar el procesamiento
if "processing" not in st.session_state:
    st.session_state.processing = False

if ctx.state.playing:
    st.info("Grabando... Presiona 'Stop' cuando termines.")
else:
    st.info("Presiona 'Start' para comenzar a grabar.")

if st.button("Procesar Grabación", disabled=st.session_state.processing):
    if ctx.audio_processor:
        st.session_state.processing = True
        audio_data = ctx.audio_processor.get_audio_data()
        
        if audio_data is not None:
            with st.spinner("Transcribiendo audio..."):
                transcription = transcribe_audio(audio_data)
                
            if transcription:
                st.subheader("Transcripción")
                st.write(transcription)
                
                with st.spinner("Generando reporte policial..."):
                    report = generate_police_report(transcription)
                    
                if report:
                    st.subheader("Reporte Policial")
                    st.markdown(report)
                    
                    st.download_button(
                        label="Descargar Reporte",
                        data=report,
                        file_name="reporte_policial.txt",
                        mime="text/plain"
                    )
        else:
            st.warning("No se detectó audio. Por favor, graba algo primero.")
        st.session_state.processing = False
    else:
        st.error("El micrófono no está inicializado. Inicia la grabación primero.")
