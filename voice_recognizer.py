import pvporcupine
import pyaudio
import struct
import speech_recognition as sr
from dotenv import load_dotenv
import os

load_dotenv()

API_KEY = os.getenv('PICOVOICE_API_KEY')

class VoiceRecognizer():
    def __init__(self):
        cur_dir = os.getcwd()
        self.porcupine = pvporcupine.create(
            access_key=API_KEY,
            keyword_paths=[cur_dir + '/wake_word_model/Jarvis_en_raspberry-pi_v3_0_0.ppn']
        )

        self.pa = pyaudio.PyAudio()
        self.audio_stream = self.pa.open(
            rate=self.porcupine.sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=self.porcupine.frame_length
        )

    def listen(self):
        while True:
            pcm = self.audio_stream.read(self.porcupine.frame_length)
            pcm = struct.unpack_from("h" * self.porcupine.frame_length, pcm)
            
            keyword_index = self.porcupine.process(pcm)
            
            if keyword_index >= 0:
                print("Wake word detected, processing command...")
                self.process_command()

    def process_command(self):
        r = sr.Recognizer()
        with sr.Microphone() as source:
            print("Listening for command...")
            audio = r.listen(source, timeout=3, phrase_time_limit=5)
        
        try:
            command = r.recognize_google(audio)
            print(f"You said: {command}")
            # Add your command processing logic here
            
        except sr.UnknownValueError:
            print("Sorry, I didn't understand that.")
        except sr.RequestError:
            print("Could not request results from Google Speech Recognition service")

if __name__ == '__main__':
    vr = VoiceRecognizer()
    vr.listen()