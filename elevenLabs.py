import requests
import json
import os
from dataclasses import asdict
from typing import List, Dict
import model
import datetime

BASE_URL = "https://api.elevenlabs.io/v1"
print(f"ElevenLabs script online")

def read_api_key(file_path: str = "11_api_key") -> str:
    with open(file_path, "r") as f:
        return f.read().strip()


def text_to_speech(api_key: str, \
                   voice: model.Voice, \
                   text: str, \
                   voice_setting: model.VoiceSetting(0.25, 0.75)) -> bytes:

    url = f"{BASE_URL}/text-to-speech/{voice.id}"

    data_dict = {"text": text,
                 "voice_settings": asdict(voice_setting)}

    response = requests.post(url, json = data_dict, headers = {"xi-api-key": api_key})
    if response.status_code != 200:
        print(response.content)
        response.raise_for_status()

    return response.content


def main(apiKeyPath: str, text: str, out_loc: str):

    # get api key
    try:
        api_key = read_api_key(f"{apiKeyPath}/11_api_key")
    except:
        api_key = read_api_key()

    voice_build_json = f"{apiKeyPath}/voice-build.json"
    with open(voice_build_json, "r") as h:
        voice_list_dict = json.loads(h.read())
        voice_list = [model.Voice.from_dict(voice) for voice in voice_list_dict]
    voices = { voice.name: voice for voice in voice_list }

    stab = 0.25
    simi = 0.8

    use_voice = voices["Alarak"]

    now = datetime.datetime.now()
    formatted_time = now.strftime("%Y-%m-%d--%H-%M-%S")
    day = formatted_time.split("--")[0]
    time = formatted_time.split("--")[1]
    os.makedirs(f'{out_loc}/{day}/', exist_ok=True)
    save_file = f"{out_loc}/{day}/{time}-Alarak.mp3"

    voice_setting = model.VoiceSetting(stab, simi)
    tts = text_to_speech(api_key, use_voice, \
        text, voice_setting)

    with open(save_file, "wb") as binary_file:
        print(save_file)
        binary_file.write(tts)
    return tts


if __name__ == '__main__':
    main()
