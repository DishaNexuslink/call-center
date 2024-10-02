
import os
import io
from google.cloud import speech

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "carbide-ego-426104-k1-efc8226a0796.json"

import queue
import re
import sys
from google.cloud import speech
import pyaudio

# Audio recording parameters
RATE = 16000
CHUNK = int(RATE / 10)  # 100ms


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
            input=True,
            frames_per_buffer=self._chunk,
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




def listen_print_loop(responses):
    """Iterates through server responses and prints them."""
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
            sys.stdout.write(transcript + overwrite_chars + "\r")
            sys.stdout.flush()
            num_chars_printed = len(transcript)
        else:
            print(transcript + overwrite_chars)
            if re.search(r"\b(exit|quit)\b", transcript, re.I):
                print("Exiting..")
                break
            num_chars_printed = 0


def main():
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

        # Process responses
        listen_print_loop(responses)


if __name__ == "__main__":
    main()

# =====================================================================================

import os
import queue
import re
import streamlit as st
from google.cloud import speech
import pyaudio
import time  # Import time module to calculate duration

# Set your Google Cloud credentials path
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "carbide-ego-426104-k1-efc8226a0796.json"

# Audio recording parameters
RATE = 16000
CHUNK = int(RATE / 10)  # 100ms

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

        # For interim results
        if not result.is_final:
            # Display real-time transcription without saving it
            text_placeholder.text(transcript + overwrite_chars)
            num_chars_printed = len(transcript)
        else:
            # Only append finalized transcript to session state
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

        # Process responses in real-time
        listen_print_loop(responses, text_placeholder)

# Streamlit UI
st.title("Real-Time Speech-to-Text Transcription")

# Initialize session state to hold the transcript if not already initialized
if 'transcript' not in st.session_state:
    st.session_state.transcript = ""  # Initialize an empty transcript

# Initialize session state to hold the start time and duration
if 'start_time' not in st.session_state:
    st.session_state.start_time = None  # Start time of speech

if 'speech_duration' not in st.session_state:
    st.session_state.speech_duration = None  # Duration of the speech

# Placeholder for real-time text
text_placeholder = st.empty()

# Buttons for Start and Stop
if st.button("Start Speaking"):
    st.session_state.transcript = ""  # Reset transcript when starting
    st.session_state.start_time = time.time()  # Record the start time
    main(text_placeholder)  # Call main() when the button is clicked

if st.button("Stop Speaking"):
    st.session_state.speech_duration = time.time() - st.session_state.start_time  

    text_placeholder.text("Stopped.")

    st.write("Final Transcript: ", st.session_state.transcript)

    st.write(f"Speech Duration: {st.session_state.speech_duration:.2f} seconds")



text=st.session_state.transcript


