import queue  # Importar la clase queue para manejar la excepción Empty
from streamlit_webrtc import webrtc_streamer, WebRtcMode
from pydub import AudioSegment
import speech_recognition as sr
import requests
import json
import streamlit as st

# Configuración de las API Keys desde los Secrets de Streamlit
LEMON_FOX_API_KEY = st.secrets["lemon_fox"]["api_key"]
DASHSCOPE_API_KEY = st.secrets["dashscope"]["api_key"]

# Función para transcribir audio usando SpeechRecognition
def transcribir_audio_desde_microfono(audio_file):
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
st.title("Transcripción y Reporte Policial desde Micrófono")

# Captura de audio desde el micrófono
webrtc_ctx = webrtc_streamer(
    key="microfono",
    mode=WebRtcMode.SENDONLY,
    audio_receiver_size=256,
    media_stream_constraints={"audio": True},
    async_processing=True,
)

if webrtc_ctx.audio_receiver:
    st.write("Grabando audio... Habla ahora.")
    try:
        # Intentar obtener frames de audio
        audio_frames = webrtc_ctx.audio_receiver.get_frames(timeout=5)  # Grabar durante 5 segundos
    except queue.Empty:
        st.warning("No se detectó audio. Por favor, habla en el micrófono.")
        audio_frames = None

    if audio_frames:
        # Combinar los frames de audio en un solo segmento
        audio_segment = AudioSegment.empty()
        for frame in audio_frames:
            audio_segment += AudioSegment(
                data=frame.to_ndarray().tobytes(),
                sample_width=frame.sample_width,
                frame_rate=frame.sample_rate,
                channels=1
            )
        # Guardar el audio en un archivo temporal
        audio_segment.export("temp_audio.wav", format="wav")
        
        # Transcribir el audio
        st.write("Transcribiendo audio...")
        transcripcion = transcribir_audio_desde_microfono("temp_audio.wav")
        
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
        st.warning("No se detectó audio. Por favor, habla en el micrófono.")
else:
    st.warning("El micrófono no está activado. Por favor, permite el acceso al micrófono.")
