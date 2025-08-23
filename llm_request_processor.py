from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('DEEPSEEK_API_KEY')

class LLMRequestProcessor():
    def __init__(self):
        self.client = OpenAI(api_key=API_KEY, base_url="https://api.deepseek.com")
        self.current_mode = "normal"
        self.mode_settings = {
            "normal": {
                "system_prompt": "You are a helpful, friendly personal assistant. Provide concise, conversational responses.",
                "temperature": 0.7,
                "max_tokens": 800,
                "style": "conversational"
            },
            "coding": {
                "system_prompt": "You are an expert programming assistant. Provide clean, efficient code with explanations. Format code with markdown code blocks. Focus on best practices and readability.",
                "temperature": 0.3,
                "max_tokens": 2000,
                "style": "technical"
            }
        }

    def _build_messages(self, request, system_prompt):
        messages = [{"role": "system", "content": system_prompt}]
        messages.append({"role": "user", "content": request})
        return messages

    def set_mode(self, mode_name):
        if mode_name in self.mode_settings:
            self.current_mode = mode_name
            print(f"Mode switched to: {mode_name}")
            return True
        else:
            print(f"Mode '{mode_name}' not found. Available modes: {list(self.mode_settings.keys())}")
            return False

    def process_request(self, request):
        mode_config = self.mode_settings[self.current_mode]

        messages = self._build_messages(request, mode_config['system_prompt'])
        params = {
            "temperature": mode_config['temperature'],
            "max_tokens": mode_config['max_tokens']
        }

        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=messages,
                stream=False,
                **params
            )
                        
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"Error processing request: {e}")
            return f"Error: {str(e)}"