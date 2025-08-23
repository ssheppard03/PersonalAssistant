from voice_recognizer import VoiceRecognizer
from llm_request_processor import LLMRequestProcessor

llmrp = LLMRequestProcessor()

def vr_callback(command):
    if 'mode' in command:
        if 'coding' in command:
            llmrp.set_mode('coding')
            print('Switched mode to coding')
        else:
            llmrp.set_mode('normal')
            print('Switch mode to normal')
    else:
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