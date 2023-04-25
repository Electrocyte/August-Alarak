import os
import subprocess
from typing import Optional, List, Dict, Any
# import time
# import psutil
# import GPUtil
# from pytube import YouTube
import matplotlib.pyplot as plt
import whisper
import argparse
# from whisperx import load_align_model, align
# from whisperx.diarize import DiarizationPipeline, assign_word_speakers
import openai


def read_huggingface_key(file_path: str = "huggingface_access") -> str:
    with open(file_path, "r") as f:
        return f.read().strip()


def convert_to_wav(input_file: str, output_file: Optional[str] = None) -> None:
    """
    Converts an audio file to WAV format using FFmpeg.

    Args:
        input_file: The path of the input audio file to convert.
        output_file: The path of the output WAV file. If None, the output file will be created by replacing the input file
        extension with ".wav".

    Returns:
        None
    """
    if not output_file:
        output_file = os.path.splitext(input_file)[0] + ".wav"

    command = f'ffmpeg -i "{input_file}" -vn -acodec pcm_s16le -ar 44100 -ac 1 "{output_file}"'

    try:
        subprocess.run(command, shell=True, check=True)
        print(f'Successfully converted "{input_file}" to "{output_file}"')
    except subprocess.CalledProcessError as e:
        print(f'Error: {e}, could not convert "{input_file}" to "{output_file}"')



parser = argparse.ArgumentParser(description='Save telegram audio.')

parser.add_argument('-d', '--directory', help='Audio file location.')
parser.add_argument('-a', '--apiKeyPath', help='Location of api key.')
parser.add_argument('-w', '--audioWav', help='wav file name.')
parser.add_argument('-m', '--audioM4a', help='m4a file name.')

args = parser.parse_args()

directory = args.directory
apiKeyPath = args.apiKeyPath
audioWav = args.audioWav
audioM4a = args.audioM4a

if len(audioWav) > 0:
    audio_loc = f"{directory}{audioWav}"
elif "mp3" in audioM4a:
    audio_loc = f"{directory}{audioM4a}"
else:
    print("Convert to wav.")
    audio_loc = convert_to_wav(f"{directory}/{audioM4a}")

try:
    api_key = whisper.read_api_key(f"{apiKeyPath}/api_key")
except:
    api_key = whisper.read_api_key()

try:
    hf_key = read_huggingface_key(f"{apiKeyPath}/huggingface_access")
except:
    hf_key = read_huggingface_key()

openai.api_key = api_key

# # this approach uses the openai api, which only gives a dictionary of the text.
# transcript_out = whisper.transcript(audio_loc)

from pyannote.audio import Pipeline
pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization",
                                    use_auth_token=hf_key)

# apply the pipeline to an audio file
diarization = pipeline(audio_loc)

# dump the diarization output to disk using RTTM format
save_rttm = f"{directory}/audio.rttm"
print(save_rttm)
with open(save_rttm, "w") as rttm:
    diarization.write_rttm(rttm)
