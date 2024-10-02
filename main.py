# import os
# import queue
# import re
# import time
# import requests  
# import streamlit as st
# from google.cloud import speech
# import pyaudio

# os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "carbide-ego-426104-k1-efc8226a0796.json"

# RATE = 16000
# CHUNK = int(RATE / 10)  

# class MicrophoneStream:
#     """Opens a recording stream as a generator yielding the audio chunks."""
#     def __init__(self, rate=RATE, chunk=CHUNK):
#         self._rate = rate
#         self._chunk = chunk
#         self._buff = queue.Queue()
#         self.closed = True

#     def __enter__(self):
#         self._audio_interface = pyaudio.PyAudio()
#         self._audio_stream = self._audio_interface.open(
#             format=pyaudio.paInt16,
#             channels=1,
#             rate=self._rate,
#             frames_per_buffer=self._chunk,
#             input=True,
#             stream_callback=self._fill_buffer,
#         )
#         self.closed = False
#         return self

#     def __exit__(self, type, value, traceback):
#         self._audio_stream.stop_stream()
#         self._audio_stream.close()
#         self.closed = True
#         self._buff.put(None)
#         self._audio_interface.terminate()

#     def _fill_buffer(self, in_data, frame_count, time_info, status_flags):
#         self._buff.put(in_data)
#         return None, pyaudio.paContinue

#     def generator(self):
#         while not self.closed:
#             chunk = self._buff.get()
#             if chunk is None:
#                 return
#             data = [chunk]
#             while True:
#                 try:
#                     chunk = self._buff.get(block=False)
#                     if chunk is None:
#                         return
#                     data.append(chunk)
#                 except queue.Empty:
#                     break
#             yield b"".join(data)

# def listen_print_loop(responses, text_placeholder):
#     """Iterates through server responses and updates the transcript."""
#     num_chars_printed = 0

#     for response in responses:
#         if not response.results:
#             continue

#         result = response.results[0]
#         if not result.alternatives:
#             continue

#         transcript = result.alternatives[0].transcript
#         overwrite_chars = " " * (num_chars_printed - len(transcript))

#         if not result.is_final:
#             text_placeholder.text(transcript + overwrite_chars)
#             num_chars_printed = len(transcript)
#         else:
#             st.session_state.transcript += transcript + overwrite_chars + " "
#             text_placeholder.text(st.session_state.transcript)
#             num_chars_printed = 0

# def main(text_placeholder):
#     language_code = "en-US"
#     client = speech.SpeechClient()

#     config = speech.RecognitionConfig(
#         encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
#         sample_rate_hertz=RATE,
#         language_code=language_code,
#     )

#     streaming_config = speech.StreamingRecognitionConfig(
#         config=config,
#         interim_results=True,
#     )

#     with MicrophoneStream(RATE, CHUNK) as stream:
#         audio_generator = stream.generator()
#         requests = (
#             speech.StreamingRecognizeRequest(audio_content=content)
#             for content in audio_generator
#         )

#         responses = client.streaming_recognize(streaming_config, requests)

#         listen_print_loop(responses, text_placeholder)

# st.title("Real-Time Speech-to-Text Transcription")

# if 'transcript' not in st.session_state:
#     st.session_state.transcript = "" 
# if 'start_time' not in st.session_state:
#     st.session_state.start_time = None  
# if 'speech_duration' not in st.session_state:
#     st.session_state.speech_duration = None  

# text_placeholder = st.empty()

# if st.button("Start Speaking"):
#     st.session_state.transcript = ""  
#     st.session_state.start_time = time.time() 
#     main(text_placeholder)  

# if st.button("Stop Speaking"):
#     st.session_state.speech_duration = time.time() - st.session_state.start_time  

#     text_placeholder.text("Stopped.")

#     st.write("call recoring:", st.session_state.transcript)
#     # Display the duration of the speech
#     st.write(f"call  Duration: {st.session_state.speech_duration:.2f} seconds")

#     # Make POST request to FastAPI to classify transcript
#     api_url = "http://localhost:8000/route_divert/"
#     payload = {"text": st.session_state.transcript}

#     try:
#         response = requests.post(api_url, json=payload)
#         if response.status_code == 200:
#             result = response.json()
#             st.write(f"{result}")
#         else:
#             st.write(f"Error: {response.status_code}, {response.text}")
#     except Exception as e:
#         st.write(f"Error in making request: {e}")

# working fine
# ===========================================================

import os
import queue
import re
import time
import requests  
import streamlit as st
from google.cloud import speech
import pyaudio

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "carbide-ego-426104-k1-efc8226a0796.json"

RATE = 16000
CHUNK = int(RATE / 10)  

class MicrophoneStream:
    """Opens a recording stream as a generator yielding the audio chunks."""
    def __init__(self, rate=RATE, chunk=CHUNK):
        self._rate = rate
        self._chunk = chunk
        self._buff = queue.Queue()
        self.closed = True

    def __enter__(self):
        self._audio_interface = pyaudio.PyAudio()
        self._audio_stream = self._audio_interface.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self._rate,
            frames_per_buffer=self._chunk,
            input=True,
            stream_callback=self._fill_buffer,
        )
        self.closed = False
        return self

    def __exit__(self, type, value, traceback):
        self._audio_stream.stop_stream()
        self._audio_stream.close()
        self.closed = True
        self._buff.put(None)
        self._audio_interface.terminate()

    def _fill_buffer(self, in_data, frame_count, time_info, status_flags):
        self._buff.put(in_data)
        return None, pyaudio.paContinue

    def generator(self):
        while not self.closed:
            chunk = self._buff.get()
            if chunk is None:
                return
            data = [chunk]
            while True:
                try:
                    chunk = self._buff.get(block=False)
                    if chunk is None:
                        return
                    data.append(chunk)
                except queue.Empty:
                    break
            yield b"".join(data)

def listen_print_loop(responses, text_placeholder):
    """Iterates through server responses and updates the transcript."""
    num_chars_printed = 0

    for response in responses:
        if not response.results:
            continue

        result = response.results[0]
        if not result.alternatives:
            continue

        transcript = result.alternatives[0].transcript
        overwrite_chars = " " * (num_chars_printed - len(transcript))

        if not result.is_final:
            text_placeholder.text(transcript + overwrite_chars)
            num_chars_printed = len(transcript)
        else:
            st.session_state.transcript += transcript + overwrite_chars + " "
            text_placeholder.text(st.session_state.transcript)
            num_chars_printed = 0

def main(text_placeholder):
    language_code = "en-US"
    client = speech.SpeechClient()

    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=RATE,
        language_code=language_code,
    )

    streaming_config = speech.StreamingRecognitionConfig(
        config=config,
        interim_results=True,
    )

    with MicrophoneStream(RATE, CHUNK) as stream:
        audio_generator = stream.generator()
        requests = (
            speech.StreamingRecognizeRequest(audio_content=content)
            for content in audio_generator
        )

        responses = client.streaming_recognize(streaming_config, requests)

        listen_print_loop(responses, text_placeholder)

st.title("Real-Time Speech-to-Text Transcription")

if 'transcript' not in st.session_state:
    st.session_state.transcript = "" 
if 'start_time' not in st.session_state:
    st.session_state.start_time = None  
if 'speech_duration' not in st.session_state:
    st.session_state.speech_duration = None  

text_placeholder = st.empty()

if st.button("make a call"):
    st.session_state.transcript = ""  
    st.session_state.start_time = time.time() 
    main(text_placeholder)  

if st.button("cut the call"):
    st.session_state.speech_duration = time.time() - st.session_state.start_time  

    text_placeholder.text("Stopped.")

    st.write("call recoring:", st.session_state.transcript)
    # Display the duration of the speech
    st.write(f"call  Duration: {st.session_state.speech_duration:.2f} seconds")

    # Make POST request to FastAPI to classify transcript
    api_url = "http://localhost:8000/route_divert/"
    payload = {"text": st.session_state.transcript}

    try:
        response = requests.post(api_url, json=payload)
        if response.status_code == 200:
            result = response.json()
            st.write(f"{result}")
        else:
            st.write(f"Error: {response.status_code}, {response.text}")
    except Exception as e:
        st.write(f"Error in making request: {e}")


# query response
if 'transcript' not in st.session_state:
    st.session_state.transcript = "" 
if 'start_time' not in st.session_state:
    st.session_state.start_time = None  
if 'speech_duration' not in st.session_state:
    st.session_state.speech_duration = None  

text_placeholder = st.empty()

if st.button("ask anything"):
    st.session_state.transcript = ""  
    st.session_state.start_time = time.time() 
    main(text_placeholder)  

if st.button("Stop "):
    st.session_state.speech_duration = time.time() - st.session_state.start_time  

    text_placeholder.text("Stopped.")

    st.write("call recoring:", st.session_state.transcript)
    # Display the duration of the speech
    st.write(f"call  Duration: {st.session_state.speech_duration:.2f} seconds")

    # Make POST request to FastAPI to classify transcript
    api_url = "http://localhost:8001/Query Response/"
    payload = {"query": st.session_state.transcript}

    try:
        response = requests.post(api_url, json=payload)
        if response.status_code == 200:
            result = response.json()
            st.write(f"Result: {result['result']}")
            st.write(f"Time taken to respond: {result['time taken to respond']}")
        else:
            st.write(f"Error: {response.status_code}, {response.text}")
    except Exception as e:
        st.write(f"Error in making request: {e}")