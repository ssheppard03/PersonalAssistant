import speech_recognition as sr
import time
from dotenv import load_dotenv
import os

load_dotenv()

class SimpleVoiceRecognizer():
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.wake_word = "jarvis"
        
    def listen_continuously(self):
        """Listen continuously for wake word and commands"""
        print(f"Listening for wake word '{self.wake_word}'...")
        
        while True:
            try:
                print("Ready...")
                with sr.Microphone() as source:
                    # Adjust for ambient noise each cycle
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    
                    # Listen for short periods
                    audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=2)
                
                text = self.recognizer.recognize_google(audio).lower()
                print(f"Heard: {text}")
                
                if self.wake_word in text:
                    print("Wake word detected! Listening for command...")
                    self.process_command()
                    
            except sr.UnknownValueError:
                # No speech detected, continue listening
                pass
            except sr.WaitTimeoutError:
                # No audio detected, continue listening
                pass
            except sr.RequestError as e:
                print(f"Speech recognition error: {e}")
            except Exception as e:
                print(f"Error: {e}")

    def process_command(self):
        """Process command after wake word"""
        try:
            with sr.Microphone() as source:
                print("Adjusting for command...")
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                print("Speak your command now...")
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=8)
            
            command = self.recognizer.recognize_google(audio)
            print(f"Command: {command}")
            # Process your command here
            
        except sr.UnknownValueError:
            print("Sorry, I didn't understand the command.")
        except sr.WaitTimeoutError:
            print("No command detected within timeout.")
        except sr.RequestError:
            print("Could not request results from speech service")

if __name__ == '__main__':
    vr = SimpleVoiceRecognizer()
    vr.listen_continuously()