import os
import re
# import subprocess
from typing import Optional, List
# from pyannote.audio import Model
import whisper
import json
import pandas as pd
import argparse
from pyannote.audio import Pipeline
from pydub import AudioSegment
# from whisperx import load_align_model, align
# from whisperx.diarize import DiarizationPipeline, assign_word_speakers
import openai

pattern = r"chunk_(\d+)"

def clean_rttm(rttm_file: str, number: str, directory: str) -> List:

    # Read the RTTM file using pandas
    columns = ['Type', 'File', 'Channel', 'Start', 'Duration', 'NA1', 'NA2', 'Speaker', 'NA3', 'NA4']
    rttm_df = pd.read_csv(rttm_file, sep=' ', header=None, names=columns)
    rttm_df['NextSpeaker'] = rttm_df['Speaker'].shift(-1)

    unique_speakers = rttm_df['Speaker'].unique()

    speaker_blocks = {}

    for speaker in unique_speakers:
        blocks = []
        start_block = None

        for index, row in rttm_df.iterrows():
            if row['Speaker'] == speaker:
                if start_block is None:
                    start_block = row['Start']

            elif start_block is not None:
                blocks.append({'Start': start_block, 'End': rttm_df.at[index - 1, 'Start'] + rttm_df.at[index - 1, 'Duration']})
                start_block = None

        if start_block is not None:
            last_row = rttm_df.iloc[-1]
            blocks.append({'Start': start_block, 'End': last_row['Start'] + last_row['Duration']})

        speaker_blocks[speaker] = blocks

    list_of_dicts = []

    for speaker, blocks in speaker_blocks.items():
        for block in blocks:
            list_of_dicts.append({"Speaker": speaker, "Start": block["Start"], "End": block["End"]})

    sorted_list_of_dicts = sorted(list_of_dicts, key=lambda x: x['Start'])

    with open(f"{directory}/{number}/{fname}-ordered.json", 'w', encoding='utf-8') as f:
        json.dump(sorted_list_of_dicts, f)

    return sorted_list_of_dicts


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
        print(output_file)

    # # ffmpeg - makes a larger file than pydub
    # command = f'ffmpeg -i "{input_file}" -vn -acodec pcm_s16le -ar 44100 -ac 1 "{output_file}"'

    # try:
    #     subprocess.run(command, shell=True, check=True)
    #     print(f'Successfully converted "{input_file}" to "{output_file}"')
    # except subprocess.CalledProcessError as e:
    #     print(f'Error: {e}, could not convert "{input_file}" to "{output_file}"')

    # pydub
    audio = AudioSegment.from_file(input_file, format="mp3")

    # Convert to WAV and save
    audio.export(output_file, format="wav")


def gen_wav(audioWav: str, audio_loc: str, output_file: str) -> str:
    if "wav" in audioWav:
        fname = audioWav.replace(".wav", "")
    elif "m4a" in audioWav:
        fname = audioWav.replace(".m4a", "")
        convert_to_wav(audio_loc, output_file)
    else:
        fname = audioWav.replace(".mp3", "")
        convert_to_wav(audio_loc, output_file)

    return fname


parser = argparse.ArgumentParser(description='Save telegram audio.')

parser.add_argument('-d', '--directory', help='Audio file location.')
parser.add_argument('-a', '--apiKeyPath', help='Location of api key.')
parser.add_argument('-w', '--audioWav', help='wav file name.')

args = parser.parse_args()

directory = args.directory
apiKeyPath = args.apiKeyPath
audioWav = args.audioWav

try:
    api_key = whisper.read_api_key(f"{apiKeyPath}/api_key")
except:
    api_key = whisper.read_api_key()

openai.api_key = api_key

try:
    hf_key = read_huggingface_key(f"{apiKeyPath}/huggingface_access")
except:
    hf_key = read_huggingface_key()

audio_loc = f"{directory}{audioWav}"

match = re.search(pattern, audioWav)
number = "0"
if match:
    number = str(match.group(1))
extension = audioWav.split(".")[-1]
new_name = audioWav.replace(extension, "wav")
output_file = f"{directory}/{number}/{new_name}"

# file name and convert to wav if necessary
# might not be working correctly as file is 3X larger than wav file previously generated
fname = gen_wav(audioWav, audio_loc, output_file)
print(f"\n{audio_loc}\n{output_file}\n")

# load diarisation model
pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization",
                                    use_auth_token=hf_key)

# apply the pipeline to an audio file
diarization = pipeline(output_file)

# dump the diarization output to disk using RTTM format
save_rttm = f"{directory}/{number}/{fname}.rttm"
print(save_rttm)
with open(save_rttm, "w") as rttm:
    diarization.write_rttm(rttm)

# clean segmentation of speakers
# return list of dictionaries {"Speaker": "SPEAKER_01", "Start": 1.308, "End": 58.007999999999996}
speaker_in_order = clean_rttm(save_rttm, number, directory)



# REQUIRES A CHECK THAT THE AUDIO CLIP IS >= 1 SECOND
#   File "/home/james/.local/share/virtualenvs/whisper-MYUEtSTx/lib/python3.10/site-packages/openai/api_requestor.py", line 683, in _interpret_response_line
#     raise self.handle_error_response(
# openai.error.InvalidRequestError: Audio file is too short. Minimum audio length is 0.1 seconds.



# load in original mp3 file and chunk on timestamps.
# this is necessary because the wav files are stupidly big
# might be worth deleting the wav files afterward too
# Iterate through the JSON data and slice the audio
audio = AudioSegment.from_file(audio_loc)

for idx, speaker_info in enumerate(speaker_in_order):
    start_time = int(speaker_info["Start"] * 1000)  # Convert to milliseconds
    end_time = int(speaker_info["End"] * 1000)  # Convert to milliseconds
    speaker = speaker_info["Speaker"]

    # Slice the audio
    audio_chunk = audio[start_time:end_time]

    # Export the audio chunk as an MP3 file
    speaker_mp3_chunk = f"{directory}/{number}/mp3s/"
    os.makedirs(speaker_mp3_chunk, exist_ok=True)
    output_filename = f"{speaker_mp3_chunk}{speaker}_chunk_{idx}.mp3"
    print(output_filename)
    audio_chunk.export(output_filename, format="mp3")

    speaker_transcript_chunk = f"{directory}/{number}/transcripts/"
    os.makedirs(speaker_transcript_chunk, exist_ok=True)
    transcript_out = whisper.transcript(output_filename)
    whisper.save_out(transcript_out, speaker_transcript_chunk, f"{idx}-chunk")


# # Order of execution
# chunk audio file into blocks of 10 minutes <- YES
# convert to wav <- YES
# diarise for speakers <- YES
# save rttm <- YES
# segmentation <- YES
# transcribe audio <- YES
