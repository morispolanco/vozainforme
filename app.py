import streamlit as st
import requests
import os
from pydub import AudioSegment
from io import BytesIO

# Configuración de página
st.set_page_config(page_title="Transcripción y Reporte Policial")

# Obtener las API Keys desde los Secrets de Streamlit
DASHSCOPE_API_KEY = st.secrets["DASHSCOPE_API_KEY"]
LEMONFOX_API_KEY = st.secrets["LEMONFOX_API_KEY"]

# Función para transcribir audio con Lemon Fox
def transcribe_audio(file, language="spanish"):
    url = "https://api.lemonfox.ai/v1/audio/transcriptions"
    headers = {
        "Authorization": f"Bearer {LEMONFOX_API_KEY}",
    }
    files = {
        "file": file,
        "language": (None, language),
        "response_format": (None, "json"),
    }
    response = requests.post(url, headers=headers, files=files)
    if response.status_code == 200:
        return response.json().get("text", "")
    else:
        st.error(f"Error en la transcripción: {response.text}")
        return ""

# Función para generar un reporte policial con Dashscope
def generate_police_report(transcription):
    url = "https://dashscope-intl.aliyuncs.com"
    headers = {
        "Authorization": f"Bearer {DASHSCOPE_API_KEY}",
        "Content-Type": "application/json",
        "X-DashScope-SSE": "enable",
    }
    prompt = (
        "Genera un reporte policial formal basado en la siguiente transcripción:\n\n"
        f"{transcription}"
    )
    data = {
        "model": "qwen-max",
        "input": {
            "messages": [
                {"role": "system", "content": "Eres un asistente que genera reportes formales."},
                {"role": "user", "content": prompt},
            ]
        },
        "parameters": {
            "result_format": "message",
            "top_p": 0.8,
            "temperature": 1,
        },
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        return response.json().get("output", {}).get("choices", [{}])[0].get("message", {}).get("content", "")
    else:
        st.error(f"Error al generar el reporte: {response.text}")
        return ""

# Interfaz de usuario
st.title("Transcripción de Audio y Generación de Reporte Policial")

# Opción para cargar un archivo de audio o usar el micrófono
option = st.radio("Selecciona una opción:", ("Subir archivo de audio", "Usar micrófono"))

if option == "Subir archivo de audio":
    uploaded_file = st.file_uploader("Sube un archivo de audio", type=["mp3", "wav"])
    if uploaded_file:
        st.audio(uploaded_file, format="audio/wav")
        if st.button("Transcribir y Generar Reporte"):
            with st.spinner("Transcribiendo audio..."):
                transcription = transcribe_audio(uploaded_file, language="spanish")
            if transcription:
                st.subheader("Transcripción:")
                st.write(transcription)
                with st.spinner("Generando reporte policial..."):
                    report = generate_police_report(transcription)
                if report:
                    st.subheader("Reporte Policial:")
                    st.write(report)

elif option == "Usar micrófono":
    audio_bytes = st_audiorec()
    if audio_bytes:
        st.audio(audio_bytes, format="audio/wav")
        # Convertir bytes a archivo temporal
        audio_segment = AudioSegment.from_file(BytesIO(audio_bytes), format="wav")
        temp_file = BytesIO()
        audio_segment.export(temp_file, format="wav")
        temp_file.seek(0)
        if st.button("Transcribir y Generar Reporte"):
            with st.spinner("Transcribiendo audio..."):
                transcription = transcribe_audio(temp_file, language="spanish")
            if transcription:
                st.subheader("Transcripción:")
                st.write(transcription)
                with st.spinner("Generando reporte policial..."):
                    report = generate_police_report(transcription)
                if report:
                    st.subheader("Reporte Policial:")
                    st.write(report)

# Función auxiliar para grabar audio desde el micrófono
def st_audiorec():
    from streamlit_webrtc import webrtc_streamer, WebRtcMode, RTCConfiguration
    import av

    audio_buffer = []

    def audio_frame_callback(frame):
        audio_buffer.append(frame.to_ndarray().tobytes())
        return frame

    webrtc_streamer(
        key="audio_recorder",
        mode=WebRtcMode.SENDONLY,
        rtc_configuration=RTCConfiguration({"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]})
    )

    if st.button("Detener grabación"):
        return b"".join(audio_buffer)
    return None
