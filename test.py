from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('DEEPSEEK_API_KEY')

client = OpenAI(api_key=API_KEY, base_url="https://api.deepseek.com")

question = input("Input question:   ")

response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "system", "content": question}
    ],
    stream=False
)

print(response.choices[0].message.content)