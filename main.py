from voice_recognizer import VoiceRecognizer
from llm_request_processor import LLMRequestProcessor

llmrp = LLMRequestProcessor()

def vr_callback(command):
    response = llmrp.process_request(command)
    print(f'LLM response: {response}')

def main():
    vr = VoiceRecognizer(vr_callback)
    try:
        vr.listen()
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        vr.stop()

if __name__ == '__main__':
    main()