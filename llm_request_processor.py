from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('DEEPSEEK_API_KEY')

class LLMRequestProcessor():
    def __init__(self):
        self.client = OpenAI(api_key=API_KEY, base_url="https://api.deepseek.com")

    def process_request(self, request):
        response = self.client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": request}
        ],
        stream=False
        )

        return response.choices[0].message.content