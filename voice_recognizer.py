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
        
        # Find the correct input device and its supported sample rates
        input_device_index, supported_sample_rate = self.find_input_device()
        
        if input_device_index is None:
            print("No suitable input device found!")
            self.audio_stream = None
            return
        
        print(f"Using sample rate: {supported_sample_rate}")
        
        try:
            self.audio_stream = self.pa.open(
                rate=supported_sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=self.porcupine.frame_length,
                input_device_index=input_device_index
            )
            print(f"Successfully opened audio stream with device index {input_device_index}")
        except Exception as e:
            print(f"Error opening audio stream: {e}")
            self.audio_stream = None

    def find_input_device(self):
        """Find the first available input device and check supported sample rates"""
        print("Searching for input devices...")
        
        # Common sample rates to try
        sample_rates = [16000, 44100, 48000, 22050, 32000]
        
        for i in range(self.pa.get_device_count()):
            info = self.pa.get_device_info_by_index(i)
            if info['maxInputChannels'] >= 1:
                print(f"\nTesting device {i}: {info['name']}")
                print(f"  Default sample rate: {info['defaultSampleRate']}")
                
                # Test which sample rates are supported
                for rate in sample_rates:
                    if self.is_sample_rate_supported(i, rate):
                        print(f"  ✓ Supports {rate} Hz")
                        return i, rate
                    else:
                        print(f"  ✗ Does not support {rate} Hz")
        
        return None, None

    def is_sample_rate_supported(self, device_index, sample_rate):
        """Check if a sample rate is supported by the device"""
        try:
            # Try to open a stream with this sample rate
            test_stream = self.pa.open(
                rate=sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=256
            )
            test_stream.close()
            return True
        except:
            return False

    def listen(self):
        if self.audio_stream is None:
            print("Cannot listen - no audio stream available")
            return
        
        print("Listening for wake word...")
        try:
            while True:
                pcm = self.audio_stream.read(self.porcupine.frame_length, exception_on_overflow=False)
                pcm = struct.unpack_from("h" * self.porcupine.frame_length, pcm)
                
                keyword_index = self.porcupine.process(pcm)
                
                if keyword_index >= 0:
                    print("Wake word detected, processing command...")
                    self.process_command()
        except KeyboardInterrupt:
            print("Stopping listener...")
        except Exception as e:
            print(f"Error in listen loop: {e}")

    def process_command(self):
        r = sr.Recognizer()
        try:
            # For speech recognition, we can use a different approach
            print("Listening for command...")
            with sr.Microphone() as source:
                print("Adjusting for ambient noise...")
                r.adjust_for_ambient_noise(source, duration=1)
                print("Speak now...")
                audio = r.listen(source, timeout=5, phrase_time_limit=8)
            
            try:
                command = r.recognize_google(audio)
                print(f"You said: {command}")
                # Add your command processing logic here
                
            except sr.UnknownValueError:
                print("Sorry, I didn't understand that.")
            except sr.RequestError as e:
                print(f"Could not request results from Google Speech Recognition service: {e}")
        except Exception as e:
            print(f"Error accessing microphone for command: {e}")

    def __del__(self):
        if hasattr(self, 'audio_stream') and self.audio_stream:
            self.audio_stream.close()
        if hasattr(self, 'pa'):
            self.pa.terminate()
        if hasattr(self, 'porcupine'):
            self.porcupine.delete()

if __name__ == '__main__':
    vr = VoiceRecognizer()
    if vr.audio_stream is not None:
        try:
            vr.listen()
        except KeyboardInterrupt:
            print("Program interrupted by user")
    else:
        print("Voice recognizer initialization failed")