import streamlit as st
from streamlit_audio_recorder import st_audiorec  # Librería para grabar audio
import tempfile
import requests
import os
from dotenv import load_dotenv
from datetime import datetime

# Cargar variables de entorno
load_dotenv()

# Obtener la API key desde las variables de entorno
API_KEY = os.getenv('LEMONFOX_API_KEY')

# Configuración de la página
st.set_page_config(
    page_title="Voz Informe",
    page_icon="🎤",
    layout="centered"
)

# CSS personalizado para estilizar botones
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

# Título y descripción
st.title("Voz Informe")
st.markdown("### Grabación y Transcripción de Audio")

# Inicializar el estado de la sesión
if 'transcription' not in st.session_state:
    st.session_state.transcription = ""
if 'report' not in st.session_state:
    st.session_state.report = ""

# Sección de grabación de audio
st.subheader("Grabación de Audio")
audio_bytes = st_audiorec()  # Grabar audio usando st_audiorec

if audio_bytes:
    # Crear un archivo temporal para guardar el audio grabado
    with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as tmp_file:
        tmp_file.write(audio_bytes)
        tmp_file_path = tmp_file.name

    with st.spinner('Procesando audio...'):
        try:
            # Preparar el archivo para enviar a la API de LemonFox
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

            # Llamar a la API de LemonFox
            response = requests.post(
                'https://api.lemonfox.ai/v1/audio/transcriptions',
                headers=headers,
                files=files,
                data=data
            )

            if response.status_code == 200:
                transcription_data = response.json()
                if 'text' in transcription_data:
                    st.session_state.transcription = transcription_data['text']
                    st.success('Audio transcrito exitosamente')
                else:
                    st.error('La respuesta del API no contiene el campo esperado: "text".')
            else:
                st.error(f'Error en la transcripción del audio: {response.text}')

        except Exception as e:
            st.error(f'Error al procesar el audio: {str(e)}')
        
        finally:
            # Eliminar el archivo temporal
            try:
                os.unlink(tmp_file_path)
            except Exception as e:
                st.warning(f"No se pudo eliminar el archivo temporal: {str(e)}")

# Mostrar la transcripción si está disponible
if st.session_state.transcription:
    st.subheader("Transcripción")
    st.text_area("Texto transcrito", st.session_state.transcription, height=150, disabled=True)

    # Sección de generación de informe
    if st.button("Generar Informe"):
        with st.spinner('Generando informe...'):
            def generate_report_content(transcription):
                # Plantilla básica del informe
                report = f"""INFORME POLICIAL

FECHA: {datetime.now().strftime('%d/%m/%Y')}
HORA: {datetime.now().strftime('%H:%M')}

DETALLE:
{transcription}

Fin del informe."""
                return report

            st.session_state.report = generate_report_content(st.session_state.transcription)
            st.success('Informe generado exitosamente')

# Mostrar el informe si está disponible
if st.session_state.report:
    st.subheader("Informe Policial")
    st.text_area("Informe generado", st.session_state.report, height=300, disabled=True)
    
    # Botón para copiar el informe al portapapeles
    if st.button("Copiar Informe"):
        st.write("<script>navigator.clipboard.writeText('{}')</script>".format(
            st.session_state.report.replace("'", "\\'"))
        , unsafe_allow_html=True)
        st.success("Informe copiado al portapapeles")

# Botón para reiniciar
if st.session_state.transcription or st.session_state.report:
    if st.button("Nuevo"):
        st.session_state.transcription = ""
        st.session_state.report = ""
        st.experimental_rerun()
