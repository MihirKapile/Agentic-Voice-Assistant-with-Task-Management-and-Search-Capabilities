import streamlit as st
from io import BytesIO
import pyaudio
from app import agent

SAMPLE_RATE = 44100
CHUNK_SIZE = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RECORD_SECONDS = 10

def record_audio(duration):
    audio = pyaudio.PyAudio()
    stream = audio.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=SAMPLE_RATE,
        input=True,
        frames_per_buffer=CHUNK_SIZE,
    )
    st.info("Recording... Speak now!")
    frames = []
    for _ in range(0, int(SAMPLE_RATE / CHUNK_SIZE * duration)):
        data = stream.read(CHUNK_SIZE)
        frames.append(data)
    st.success("Recording complete!")
    stream.stop_stream()
    stream.close()
    audio.terminate()
    return b"".join(frames)

def transcribe_audio(audio_data):
    return "Transcription: [Replace with actual transcription]"

st.title("Audio and Text Input with Streamlit")
st.write("This app allows you to either record audio or send text to an agent.")

st.header("Audio Input")
if st.button("Record Audio"):
    audio_data = record_audio(RECORD_SECONDS)
    st.audio(BytesIO(audio_data), format="audio/wav")
    transcription = transcribe_audio(audio_data)
    st.write(f"Transcription: {transcription}")
    response = agent.run(transcription)
    st.write("Agent Response:")
    st.write(response)

st.header("Text Input")
text_input = st.text_input("Enter your message:")
if st.button("Send Text"):
    if text_input.strip():
        response = agent.run(text_input)
        st.write("Agent Response:")
        st.write(response)
    else:
        st.warning("Please enter a valid message.")