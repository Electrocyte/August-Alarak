from os import environ
environ['CHATGPT_BASE_URL'] = "https://bypass.churchless.tech/"
from revChatGPT.V1 import Chatbot
import argparse
import json


def read_api_key(file_path: str = "gpt4_api") -> str:
    with open(file_path, "r") as f:
        return f.read().strip()


def process_message(text: str, prompt: str) -> str:

    access = {
        "access_token": ACCESS_TOKEN,
        # "api_key ": ACCESS_TOKEN,
        "model": "gpt-4",
        # "temperature": 0.5,
    }

    chatbot = Chatbot(access)
    data = chatbot.ask(f"{prompt} {text}")
    res = ""
    for i in data:
        res = i["message"]
    return res


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='GPT-4.')

    parser.add_argument('-a', '--accessToken', help='Location of api key.')
    parser.add_argument('-t', '--text', help='Input text.')
    parser.add_argument('-p', '--prompt', help='Prompt.')

    args = parser.parse_args()

    accessToken = args.accessToken
    text = args.text
    prompt = args.prompt

    try:
        ACCESS_TOKEN = read_api_key(f"{accessToken}/gpt4_api")
    except:
        ACCESS_TOKEN = read_api_key()

    with open(text, 'r', encoding='utf-8') as f:
        json_text = json.load(f)

    res = process_message(json_text, prompt)
    print(res)
