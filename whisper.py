import os
import json
import openai
import argparse
import datetime
from pydub import AudioSegment
import importlib.metadata
from typing import Dict, List, Union

#  Note: you need to be using OpenAI Python v0.27.0 for the code below to work
version = importlib.metadata.version('openai')
print(f"Whisper online; current version of Open AI: {version}")


def read_api_key(file_path: str = "api_key") -> str:
    with open(file_path, "r") as f:
        return f.read().strip()


def transcript(audio_dir: str, prompt: str = "Hello, this is a transcript.") -> Dict:
    audio_file = open(audio_dir, "rb")
    transcript_ = openai.Audio.transcribe("whisper-1", audio_file, initial_prompt=prompt)
    return transcript_


def translate(audio_dir: str, prompt: str = "Hello, this is a translation.") -> Dict:
    audio_file = open(audio_dir, "rb")
    translated_transcript = openai.Audio.translate("whisper-1", audio_file, initial_prompt=prompt)
    return translated_transcript


def save_out(_dict_: Dict, save_loc: str, _type_: str) -> None:
    # Save the dictionary to a JSON file
    now = datetime.datetime.now()
    formatted_time = now.strftime("%Y-%m-%d--%H-%M-%S")
    day = formatted_time.split("--")[0]
    time = formatted_time.split("--")[1]
    os.makedirs(f'{save_loc}/{day}/', exist_ok=True)
    save_file = f'{save_loc}/{day}/{time}-{_type_}.json'
    with open(save_file, 'w') as f:
        print(save_file)
        json.dump(_dict_, f)


def chunk_audio(file_to_check: str, format: str, save_loc: str) -> List:
    audio_file = AudioSegment.from_file(file_to_check, format=format)

    # Split the audio into 30-minute chunks
    chunk_length_ms = 30 * 60 * 1000
    chunks = list(range(0, len(audio_file), chunk_length_ms))

    # Create a directory to save the chunks
    chunk_save_loc = f"{save_loc}/chunks/"
    if not os.path.exists(chunk_save_loc):
        os.mkdir(chunk_save_loc)

    chunk_files = []
    for i, chunk_start in enumerate(chunks):
        chunk = audio_file[chunk_start:chunk_start + chunk_length_ms]
        save_name = f"{chunk_save_loc}/chunk_{i}.mp3"
        print(f"Saving to: {save_name}")
        chunk_files.append(save_name)
        chunk.export(save_name, format="mp3")
    return chunk_files


def check_file_size(file_to_check: str, save_loc: str) -> Union[List, None]:
    print(file_to_check)
    if os.stat(file_to_check).st_size > 0:
        if os.stat(file_to_check).st_size > 2e7:
            if "m4a" in file_to_check:
                format = "m4a"
                chunk_files = chunk_audio(file_to_check, format, save_loc)
                return chunk_files

            elif "mp3" in file_to_check:
                format = "mp3"
                chunk_files = chunk_audio(file_to_check, format, save_loc)
                return chunk_files

            else:
                print("No audio file found.")
    else:
        pass


def T_or_T(t_audio_file, prompt, save_loc, save, _type_) -> Dict:
    if _type_ == 'transcript':
        t_ = transcript(t_audio_file, prompt)
    elif _type_ == 'translated-transcript':
        t_ = translate(t_audio_file, prompt)
    print(f"{_type_}: {t_}")
    save_out(t_, save_loc, f"{_type_}-{save}")
    return t_


# Load your API key from an environment variable or secret management service
# get api key
def main():

    #################### ARG PARSING
    parser = argparse.ArgumentParser(description='Transcribe or translate audio to text.')
    parser.add_argument('-p', '--prompt', help='Prompt if desired e.g. Hello, this is a translation.', default = 'This default is used to ensure punctuation, acronyms are useful here too.')
    parser.add_argument('-s', '--save', help='string to make save file unique', default = "1")
    parser.add_argument('-o', '--out', help='Full path to save the audio clips. e.g. /mnt/usersData/whisper/')
    parser.add_argument('-a', '--apiKeyPath', help='Location of api key.')
    parser.add_argument('-t', '--transcribe', help='Location of audio file to transcribe to be used in mp3 format.')
    parser.add_argument('-x', '--translate', help='Location of audio file to translate to be used in mp3 format. Currently only does X-to-English.')
    args = parser.parse_args()

    prompt = args.prompt
    save = args.save
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

    if os.path.isfile(transcribe_audio_file) and not None:
        # fix issue with overly large files.
        chunk_files = check_file_size(transcribe_audio_file, save_loc)

        if chunk_files is not None:
            for n, cf in enumerate(chunk_files):
                T_or_T(cf, prompt, save_loc, save, f"transcript-{n}")

        else:
             T_or_T(transcribe_audio_file, prompt, save_loc, save, "transcript")

        # transcript_ = transcript(transcribe_audio_file, prompt)
        # print(f"Transcript: {transcript_}")
        # save_out(transcript_, save_loc, f"transcript-{save}")

    if os.path.isfile(translate_audio_file) and not None:
        # fix issue with overly large files.
        chunk_files = check_file_size(translate_audio_file, save_loc)

        if chunk_files is not None:
            for n, cf in enumerate(chunk_files):
                T_or_T(cf, prompt, save_loc, save, f"translated-transcript-{n}")

        else:
             T_or_T(translate_audio_file, prompt, save_loc, save, "translated-transcript")

        # translated_transcript = translate(translate_audio_file, prompt)
        # print(f"Translated transcript: {translated_transcript}")
        # save_out(translated_transcript, save_loc, f"translated-{save}")


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
