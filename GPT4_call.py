from revChatGPT.V3 import Chatbot
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
        "temperature": 0.5,
    }

    chatbot = Chatbot(access)
    data = chatbot.ask(f"{prompt} {text}")
    res = ""
    for i in data:
        res = i["message"]
    return res


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='GPT-4.')

    parser.add_argument('-a', '--apiKeyPath', help='Location of api key.')
    parser.add_argument('-t', '--text', help='Input text.')
    parser.add_argument('-p', '--prompt', help='Prompt.')

    args = parser.parse_args()

    apiKeyPath = args.apiKeyPath
    text = args.text
    prompt = args.prompt

    try:
        ACCESS_TOKEN = read_api_key(f"{apiKeyPath}/gpt4_api")
    except:
        ACCESS_TOKEN = read_api_key()

    with open(text, 'r', encoding='utf-8') as f:
        json_text = json.load(f)

    res = process_message(json_text, prompt)
    print(res)
