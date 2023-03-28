import os
import json
import openai
import argparse
import datetime
import importlib.metadata
from typing import Dict

#  Note: you need to be using OpenAI Python v0.27.0 for the code below to work
version = importlib.metadata.version('openai')
print(f"Chat-GPT script online; current version of Open AI: {version}")


def read_api_key(file_path: str = "api_key") -> str:
    with open(file_path, "r") as f:
        return f.read().strip()


def json_contact_GPT(json_read: Dict, prompt: str = "Minimise any other prose.") -> Dict:
    full_prompt = f"{prompt} {list(json_read.values())[0]}"
    print(f"{full_prompt}\n")

    reply = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages = [
                {"role": "system", "content": "You are High Lord Alarak. Your exquisite prose is Legendary."},
                {"role": "user", "content": full_prompt},
                # {"role": "assistant", "content": "The Los Angeles Dodgers won the World Series in 2020."},
                # {"role": "user", "content": "Where was it played?"}
            ]
        )
    return reply


def direct_contact_GPT(text: str, prompt: str = "Minimise any other prose.") -> Dict:
    full_prompt = f"{prompt} {text}"
    print(f"{full_prompt}\n")

    # {"id": "chatcmpl-6z2Dbtif3GwjTkGNkepXWKsRPGB1Q"}
    # {"model": "gpt-3.5-turbo-0301"}

    reply = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages = [
                {"role": "system", "content": "You are High Lord Alarak. Your exquisite prose is Legendary."},
                {"role": "user", "content": full_prompt},
                # {"role": "assistant", "content": "The Los Angeles Dodgers won the World Series in 2020."},
                # {"role": "user", "content": "Where was it played?"}
            ]
        )
    return reply


def save_out(response: Dict, save_loc: str, _type_: str) -> None:
    the_reply = response['choices'][0]['message']['content']
    model = response['model']
    usage = response['usage']
    finish_reason = response['choices'][0]['finish_reason']
    finish_reasons = {"stop": "API returned complete model output", "length": "Incomplete model output due to max_tokens parameter or token limit", "content_filter": "Omitted content due to a flag from our content filters", "null": "API response still in progress or incomplete"}

    print(f"{finish_reason}, {finish_reasons[finish_reason]}")

    to_save = {"Reply": the_reply, "Completion status": finish_reasons[finish_reason], "Model": model, "Usage": usage}

    # # Save the dictionary to a JSON file
    now = datetime.datetime.now()
    formatted_time = now.strftime("%Y-%m-%d--%H-%M-%S")
    save_file = f'{save_loc}/{formatted_time}-{_type_}.json'
    with open(save_file, 'w') as f:
        print(f"{save_file}\n")
        json.dump(to_save, f)


# Load your API key from an environment variable or secret management service
# get api key
def main():

    #################### ARG PARSING
    parser = argparse.ArgumentParser(description='Transcribe or translate audio to text.')
    parser.add_argument('-o', '--out', help='Full path to save the text file. e.g. /mnt/usersData/chat-GPT/')
    parser.add_argument('-a', '--apiKeyPath', help='Location of api key.', default = "")
    parser.add_argument('-t', '--textFile', help='Location of text file to work on.')
    parser.add_argument('-p', '--prompt', help='Any additional prompt.')
    args = parser.parse_args()

    save_loc = args.out
    apiKeyPath = args.apiKeyPath
    input_file = args.textFile
    prompt = args.prompt
    #################### ARG PARSING

    with open(input_file, "r") as json_file:
        json_read = json.loads(json_file.read())

    try:
        api_key = read_api_key()
    except:
        api_key = read_api_key(f"{apiKeyPath}/api_key")

    openai.api_key = api_key

    if os.path.isfile(input_file):
        GPT_reply = json_contact_GPT(json_read, prompt)
        # print(f"GPT reply: {GPT_reply}")
        save_out(GPT_reply, save_loc, "gpt")


if __name__ == '__main__':
    main()

# dict['id': "", 'choices':[{message[role] = 'assistant'}]]
# {
#  'id': 'chatcmpl-6p9XYPYSTTRi0xEviKjjilqrWU2Ve',
#  'object': 'chat.completion',
#  'created': 1677649420,
#  'model': 'gpt-3.5-turbo',
#  'usage': {'prompt_tokens': 56, 'completion_tokens': 31, 'total_tokens': 87},
#  'choices': [
#    {
#     'message': {
#       'role': 'assistant',
#       'content': 'The 2020 World Series was played in Arlington, Texas at the Globe Life Field, which was the new home stadium for the Texas Rangers.'},
#     'finish_reason': 'stop',
#     'index': 0
#    }
#   ]
# }
