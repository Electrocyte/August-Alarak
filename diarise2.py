import os
import subprocess
from typing import Optional, List, Dict, Any
from pyannote.audio import Model
import whisper
import json
import pandas as pd
import argparse
from pyannote.audio import Pipeline
# from whisperx import load_align_model, align
# from whisperx.diarize import DiarizationPipeline, assign_word_speakers
import openai


def clean_rttm(rttm_file: str) -> None:

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

    with open(f"{directory}/{fname}-ordered.json", 'w', encoding='utf-8') as f:
        json.dump(sorted_list_of_dicts, f)


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

try:
    api_key = whisper.read_api_key(f"{apiKeyPath}/api_key")
except:
    api_key = whisper.read_api_key()

openai.api_key = api_key

try:
    hf_key = read_huggingface_key(f"{apiKeyPath}/huggingface_access")
except:
    hf_key = read_huggingface_key()

# file name and convert to wav if necessary
if "wav" in audioWav:
    audio_loc = f"{directory}{audioWav}"
    fname = audioWav.replace(".wav", "")
elif "m4a" in audioM4a:
    audio_loc = f"{directory}{audioM4a}"
    fname = audioM4a.replace(".m4a", "")
    audio_loc = convert_to_wav(audio_loc)
else:
    audio_loc = f"{directory}{audioWav}"
    fname = audioWav.replace(".mp3", "")
    audio_loc = convert_to_wav(audio_loc)

# # this approach uses the openai api, which only gives a dictionary of the text.
transcript_out = whisper.transcript(audio_loc)

pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization",
                                    use_auth_token=hf_key)

# apply the pipeline to an audio file
diarization = pipeline(audio_loc)

# dump the diarization output to disk using RTTM format
save_rttm = f"{directory}/{fname}.rttm"
print(save_rttm)
with open(save_rttm, "w") as rttm:
    diarization.write_rttm(rttm)

clean_rttm(save_rttm)











# # speaker segmentation
# from pyannote.audio.pipelines import VoiceActivityDetection
# model = Model.from_pretrained("pyannote/segmentation",
#                               use_auth_token=hf_key)
# pipeline = VoiceActivityDetection(segmentation=model)
# HYPER_PARAMETERS = {
#   # onset/offset activation thresholds
#   "onset": 0.5, "offset": 0.5,
#   # remove speech regions shorter than that many seconds.
#   "min_duration_on": 0.0,
#   # fill non-speech regions shorter than that many seconds.
#   "min_duration_off": 0.0
# }
# pipeline.instantiate(HYPER_PARAMETERS)
# vad = pipeline(audio_loc)

# from pyannote.audio.pipelines import OverlappedSpeechDetection
# pipeline = OverlappedSpeechDetection(segmentation=model)
# pipeline.instantiate(HYPER_PARAMETERS)
# osd = pipeline(audio_loc)

# # pipenv install pyannote.core
# import pyannote.core as pc

# baseline_results = [
#     {"speaker": label, "start": segment.start, "end": segment.end}
#     for segment, _, label in diarization.itertracks(yield_label=True)
# ]

# # Convert baseline_results back to a pyannote.core.Annotation instance
# baseline_annotation = pc.Annotation()
# for result in baseline_results:
#     segment = pc.Segment(start=result["start"], end=result["end"])
#     baseline_annotation[segment] = result["speaker"]

# from pyannote.audio.pipelines import Resegmentation
# pipeline = Resegmentation(segmentation=model,
#                           diarization="baseline")
# pipeline.instantiate(HYPER_PARAMETERS)
# resegmented_baseline = pipeline({"audio": audio_loc, "baseline": baseline_annotation})
# # where `baseline` should be provided as a pyannote.core.Annotation instance


# # Order of execution
# chunk audio file into blocks of 10 minutes <- YES
# convert to wav <- YES
# transcribe audio <- YES
# diarise for speakers <- YES
# save rttm <- YES
# segmentation <- ???
