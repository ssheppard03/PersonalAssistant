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
        self.recognizer = sr.Recognizer()
        
        # Find the correct input device
        input_device_index, self.device_sample_rate = self.find_input_device()
        
        if input_device_index is None:
            print("No suitable input device found!")
            self.audio_stream = None
            return
        
        print(f"Using device sample rate: {self.device_sample_rate} Hz")
        print(f"Porcupine requires: 16000 Hz")
        
        # Calculate the resampling ratio
        self.resample_ratio = 16000 / self.device_sample_rate
        print(f"Resampling ratio: {self.resample_ratio}")
        
        # Calculate how many frames we need to read
        self.required_frames = int(self.porcupine.frame_length / self.resample_ratio)
        print(f"Reading {self.required_frames} frames from device to get {self.porcupine.frame_length} frames at 16kHz")
        
        try:
            self.audio_stream = self.pa.open(
                rate=self.device_sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=self.required_frames,
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

    def listen(self):
        if self.audio_stream is None:
            print("Cannot listen - no audio stream available")
            return
        
        print("Listening for wake word... (Say 'Jarvis')")
        try:
            while True:
                # Read the required number of frames from the device
                pcm = self.audio_stream.read(self.required_frames, exception_on_overflow=False)
                
                # Resample from device rate to 16kHz
                resampled_pcm = audioop.ratecv(
                    pcm, 
                    2,  # Sample width in bytes (2 for 16-bit)
                    1,  # Number of channels
                    self.device_sample_rate,
                    16000,
                    None
                )[0]
                
                # Ensure we have exactly the number of samples Porcupine expects
                if len(resampled_pcm) < self.porcupine.frame_length * 2:
                    padding_needed = (self.porcupine.frame_length * 2) - len(resampled_pcm)
                    resampled_pcm += b'\x00' * padding_needed
                
                # Convert to the format Porcupine expects
                pcm_samples = struct.unpack_from("h" * self.porcupine.frame_length, resampled_pcm)
                
                # Process with Porcupine
                keyword_index = self.porcupine.process(pcm_samples)
                
                if keyword_index >= 0:
                    print("Wake word detected! Processing command...")
                    self.process_command()
                    
        except KeyboardInterrupt:
            print("Stopping listener...")
        except Exception as e:
            print(f"Error in listen loop: {e}")

    def process_command(self):
        """Process command after wake word - using a separate microphone instance"""
        try:
            # Close the current audio stream before opening a new one
            if self.audio_stream:
                self.audio_stream.close()
                self.audio_stream = None
            
            print("Listening for command...")
            
            # Use speech_recognition's microphone handling
            with sr.Microphone() as source:
                print("Adjusting for ambient noise...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                print("Speak now...")
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=8)
            
            try:
                command = self.recognizer.recognize_google(audio)
                print(f"You said: {command}")
                # Add your command processing logic here
                
            except sr.UnknownValueError:
                print("Sorry, I didn't understand that.")
            except sr.RequestError as e:
                print(f"Could not request results from Google Speech Recognition service: {e}")
            
            # Reopen the audio stream for wake word detection
            self.reopen_audio_stream()
            
        except Exception as e:
            print(f"Error accessing microphone for command: {e}")
            # Try to reopen the audio stream even if there was an error
            self.reopen_audio_stream()

    def reopen_audio_stream(self):
        """Reopen the audio stream for wake word detection"""
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
                print("Audio stream reopened for wake word detection")
        except Exception as e:
            print(f"Error reopening audio stream: {e}")
            self.audio_stream = None

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