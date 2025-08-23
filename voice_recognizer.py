import pvporcupine
import pyaudio
import struct
import speech_recognition as sr
from dotenv import load_dotenv
import os
import audioop

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
        
        # Find the correct input device
        input_device_index, self.device_sample_rate = self.find_input_device()
        
        if input_device_index is None:
            print("No suitable input device found!")
            self.audio_stream = None
            return
        
        print(f"Using device sample rate: {self.device_sample_rate} Hz")
        print(f"Porcupine requires: 16000 Hz")
        
        try:
            self.audio_stream = self.pa.open(
                rate=self.device_sample_rate,  # Use the device's native sample rate
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
        """Find the first available input device"""
        print("Searching for input devices...")
        
        for i in range(self.pa.get_device_count()):
            info = self.pa.get_device_info_by_index(i)
            if info['maxInputChannels'] >= 1:
                print(f"Device {i}: {info['name']}")
                print(f"  Default sample rate: {info['defaultSampleRate']}")
                return i, int(info['defaultSampleRate'])
        
        return None, None

    def resample_audio(self, audio_data, from_rate, to_rate):
        """Resample audio from one sample rate to another"""
        if from_rate == to_rate:
            return audio_data
        
        # Calculate the conversion factor
        conversion_factor = to_rate / from_rate
        
        # Resample the audio
        resampled_data = audioop.ratecv(
            audio_data, 
            2,  # Sample width in bytes (2 for 16-bit)
            1,  # Number of channels
            from_rate,
            to_rate,
            None
        )[0]
        
        return resampled_data

    def listen(self):
        if self.audio_stream is None:
            print("Cannot listen - no audio stream available")
            return
        
        print("Listening for wake word... (Say 'Jarvis')")
        try:
            while True:
                # Read audio from microphone at device's sample rate
                pcm = self.audio_stream.read(self.porcupine.frame_length, exception_on_overflow=False)
                
                # Resample from device rate (44.1kHz) to Porcupine rate (16kHz)
                if self.device_sample_rate != 16000:
                    pcm = self.resample_audio(pcm, self.device_sample_rate, 16000)
                
                # Convert to the format Porcupine expects
                pcm = struct.unpack_from("h" * self.porcupine.frame_length, pcm)
                
                # Process with Porcupine
                keyword_index = self.porcupine.process(pcm)
                
                if keyword_index >= 0:
                    print("Wake word detected! Processing command...")
                    self.process_command()
                    
        except KeyboardInterrupt:
            print("Stopping listener...")
        except Exception as e:
            print(f"Error in listen loop: {e}")

    def process_command(self):
        r = sr.Recognizer()
        try:
            print("Listening for command...")
            with sr.Microphone() as source:
                print("Adjusting for ambient noise...")
                r.adjust_for_ambient_noise(source, duration=1)
                print("Speak now...")
                audio = r.listen(source, timeout=5, phrase_time_limit=8)
            
            try:
                command = r.recognize_google(audio)
                print(f"You said: {command}")
                # TODO add logic here
                
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