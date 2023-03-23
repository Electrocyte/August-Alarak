import os
import json
import openai
import argparse
import datetime
import importlib.metadata
from typing import Dict

#  Note: you need to be using OpenAI Python v0.27.0 for the code below to work
version = importlib.metadata.version('openai')
print(f"Current version of Open AI: {version}")

def read_api_key(file_path: str = "api_key") -> str:
    with open(file_path, "r") as f:
        return f.read()


def transcript(api_key: str, audio_dir: str, prompt: str = "Hello, this is a transcript.") -> Dict:
    audio_file = open(audio_dir, "rb")
    transcript_ = openai.Audio.transcribe("whisper-1", audio_file, initial_prompt=prompt)
    return transcript_


def translate(api_key: str, audio_dir: str, prompt: str = "Hello, this is a translation.") -> Dict:
    audio_file = open(audio_dir, "rb")
    translated_transcript = openai.Audio.translate("whisper-1", audio_file, initial_prompt=prompt)
    return translated_transcript


def save_out(_dict_: Dict, save_loc: str, _type_: str) -> None:
    # Save the dictionary to a JSON file
    now = datetime.datetime.now()
    formatted_time = now.strftime("%Y-%m-%d--%H-%M-%S")
    save_file = f'{save_loc}/{formatted_time}-{_type_}.json'
    with open(save_file, 'w') as f:
        print(save_file)
        json.dump(_dict_, f)


# Load your API key from an environment variable or secret management service
# get api key
def main():

    #################### ARG PARSING
    parser = argparse.ArgumentParser(description='Transcribe or translate audio to text.')
    parser.add_argument('-p', '--prompt', help='Prompt if desired e.g. Hello, this is a translation. is the default used to ensure punctuation, acronyms are useful here too.')
    parser.add_argument('-o', '--out', help='Full path to save the audio clips. e.g. /mnt/usersData/whisper/')
    parser.add_argument('-a', '--apiKeyPath', help='Location of api key.')
    parser.add_argument('-t', '--transcribe', help='Location of audio file to transcribe to be used in mp3 format.')
    parser.add_argument('-x', '--translate', help='Location of audio file to translate to be used in mp3 format. Currently only does X-to-English.')
    args = parser.parse_args()

    prompt = args.prompt
    save_loc = args.out
    apiKeyPath = args.apiKeyPath
    transcribe_audio_file = args.transcribe
    translate_audio_file = args.translate
    #################### ARG PARSING

    try:
        api_key = read_api_key()
    except:
        api_key = read_api_key(f"{apiKeyPath}/api_key")
    
    openai.api_key = api_key

    if os.path.isfile(transcribe_audio_file):
        transcript_ = transcript(api_key, transcribe_audio_file, prompt)
        print(f"Transcript: {transcript_}")
        save_out(transcript_, save_loc, "transcript")

    if os.path.isfile(translate_audio_file):
        translated_transcript = translate(api_key, translate_audio_file, prompt)
        print(f"Translated transcript: {translated_transcript}")
        save_out(translated_transcript, save_loc, "translated")


if __name__ == '__main__':
    main()

# Current version of Open AI: 0.27.2
# Transcript: {
#   "text": "The three green dragonborn enter the seedy bar, \
# their eyes scanning the dimly lit room as they look for any \
# signs of their target, Kax'ist. Yonar steps forward, approaching \
# the barkeep with a stern expression. We are looking for information \
# on a man named Kaxus. He's been accused of high treason against the \
# ..."
# }
# Translated transcript: {
#   "text": "Feel the pain. Think of the pain. Receive the pain. \
# Know the pain. Those who do not know the pain do not know true peace. \
# I will not forget the pain of Yahiko. From here, \
# I will bring pain to the world. Shinra Tensei"
# }