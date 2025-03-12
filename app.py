import streamlit as st
import tempfile
import requests
import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# Get API key from environment variable
API_KEY = os.getenv('LEMONFOX_API_KEY')

# Page configuration
st.set_page_config(
    page_title="Voz Informe",
    page_icon="🎤",
    layout="centered"
)

# Custom CSS for styling
st.markdown("""
<style>
    .stButton > button {
        background-color: #1e40af;
        color: white;
        width: 100%;
    }
    .stButton > button:hover {
        background-color: #1e3a8a;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# Title and description
st.title("Voz Informe")
st.markdown("### Grabación y Transcripción de Audio")

# Initialize session state
if 'transcription' not in st.session_state:
    st.session_state.transcription = ""
if 'report' not in st.session_state:
    st.session_state.report = ""

# Audio recording section
st.subheader("Grabación de Audio")
audio_file = st.audio_recorder()

if audio_file is not None:
    # Create a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as tmp_file:
        tmp_file.write(audio_file.getvalue())
        tmp_file_path = tmp_file.name

    with st.spinner('Procesando audio...'):
        try:
            # Prepare the file for LemonFox API
            files = {
                'file': ('recording.webm', open(tmp_file_path, 'rb'), 'audio/webm')
            }
            headers = {
                'Authorization': f'Bearer {API_KEY}'
            }
            data = {
                'language': 'spanish',
                'response_format': 'json'
            }

            # Call LemonFox API
            response = requests.post(
                'https://api.lemonfox.ai/v1/audio/transcriptions',
                headers=headers,
                files=files,
                data=data
            )

            if response.status_code == 200:
                transcription_data = response.json()
                st.session_state.transcription = transcription_data['text']
                st.success('Audio transcrito exitosamente')
            else:
                st.error('Error en la transcripción del audio')

        except Exception as e:
            st.error(f'Error al procesar el audio: {str(e)}')
        finally:
            # Clean up the temporary file
            os.unlink(tmp_file_path)

# Display transcription if available
if st.session_state.transcription:
    st.subheader("Transcripción")
    st.text_area("Texto transcrito", st.session_state.transcription, height=150, disabled=True)

    # Report generation section
    if st.button("Generar Informe"):
        with st.spinner('Generando informe...'):
            # Local report generation function
            def generate_report_content(transcription):
                # Basic report template
                report = f"""INFORME POLICIAL

FECHA: {datetime.now().strftime('%d/%m/%Y')}
HORA: {datetime.now().strftime('%H:%M')}

DETALLE:
{transcription}

Fin del informe."""
                return report

            st.session_state.report = generate_report_content(st.session_state.transcription)
            st.success('Informe generado exitosamente')

# Display report if available
if st.session_state.report:
    st.subheader("Informe Policial")
    st.text_area("Informe generado", st.session_state.report, height=300, disabled=True)
    
    # Copy report button
    if st.button("Copiar Informe"):
        st.write("<script>navigator.clipboard.writeText('{}')</script>".format(
            st.session_state.report.replace("'", "\\'"))
        , unsafe_allow_html=True)
        st.success("Informe copiado al portapapeles")

# Reset button
if st.session_state.transcription or st.session_state.report:
    if st.button("Nuevo"):
        st.session_state.transcription = ""
        st.session_state.report = ""
        st.experimental_rerun()
