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
    def __init__(self, command_callback=None):
        self.command_callback = command_callback
        cur_dir = os.getcwd()
        self.porcupine = pvporcupine.create(
            access_key=API_KEY,
            keyword_paths=[cur_dir + '/wake_word_model/Jarvis_en_raspberry-pi_v3_0_0.ppn']
        )

        self.pa = pyaudio.PyAudio()
        self.recognizer = sr.Recognizer()
        
        # Find the correct input device
        input_device_index, self.device_sample_rate = self.find_input_device()
        
        if input_device_index is None:
            print("No suitable input device found!")
            self.audio_stream = None
            return
        
        print(f"Using device sample rate: {self.device_sample_rate} Hz")
        
        # Calculate the resampling ratio
        self.resample_ratio = 16000 / self.device_sample_rate
        self.required_frames = int(self.porcupine.frame_length / self.resample_ratio)
        
        try:
            self.audio_stream = self.pa.open(
                rate=self.device_sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=self.required_frames,
                input_device_index=input_device_index
            )
            print("Audio stream opened successfully")
        except Exception as e:
            print(f"Error opening audio stream: {e}")
            self.audio_stream = None

    def find_input_device(self):
        """Find the first available input device"""
        for i in range(self.pa.get_device_count()):
            info = self.pa.get_device_info_by_index(i)
            if info['maxInputChannels'] >= 1:
                return i, int(info['defaultSampleRate'])
        return None, None

    def listen(self):
        if self.audio_stream is None:
            return
        
        print("Listening for wake word... (Say 'Jarvis')")
        try:
            while True:
                pcm = self.audio_stream.read(self.required_frames, exception_on_overflow=False)
                
                # Resample and process
                resampled_pcm = audioop.ratecv(
                    pcm, 2, 1, self.device_sample_rate, 16000, None
                )[0]
                
                if len(resampled_pcm) < self.porcupine.frame_length * 2:
                    padding_needed = (self.porcupine.frame_length * 2) - len(resampled_pcm)
                    resampled_pcm += b'\x00' * padding_needed
                
                pcm_samples = struct.unpack_from("h" * self.porcupine.frame_length, resampled_pcm)
                keyword_index = self.porcupine.process(pcm_samples)
                
                if keyword_index >= 0:
                    print("Wake word detected!")
                    self.process_command()
                    
        except KeyboardInterrupt:
            print("Stopping listener...")
        except Exception as e:
            print(f"Error in listen loop: {e}")

    def process_command(self):
        try:
            if self.audio_stream:
                self.audio_stream.close()
                self.audio_stream = None
            
            print("Listening for command...")
            
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=8)
            
            command = self.recognizer.recognize_google(audio)
            print(f"Command received: {command}")
            
            # Call the callback function with the command
            if self.command_callback:
                self.command_callback(command)
            else:
                print(f"No callback set. Command was: {command}")
            
            self.reopen_audio_stream()
            
        except Exception as e:
            print(f"Error processing command: {e}")
            self.reopen_audio_stream()

    def reopen_audio_stream(self):
        try:
            input_device_index, _ = self.find_input_device()
            if input_device_index is not None:
                self.audio_stream = self.pa.open(
                    rate=self.device_sample_rate,
                    channels=1,
                    format=pyaudio.paInt16,
                    input=True,
                    frames_per_buffer=self.required_frames,
                    input_device_index=input_device_index
                )
        except Exception as e:
            print(f"Error reopening audio stream: {e}")

    def stop(self):
        if hasattr(self, 'audio_stream') and self.audio_stream:
            self.audio_stream.close()
        if hasattr(self, 'pa'):
            self.pa.terminate()
        if hasattr(self, 'porcupine'):
            self.porcupine.delete()