# pipenv install pyAudioAnalysis numpy scipy scikit-learn imblearn plotly hmmlearn matplotlib eyed3

# import os
# import argparse
# from pyAudioAnalysis import audioBasicIO
# from pyAudioAnalysis import audioSegmentation as aS
# from pydub import AudioSegment


# def convert_to_mp3(input_file):
#     print(f"\n{input_file}\n")
#     output_file = os.path.splitext(input_file)[0] + '.mp3'
#     audio = AudioSegment.from_file(input_file)
#     audio.export(output_file, format='mp3')
#     return output_file


# def save_speaker_chunks(input_file, speaker_labels, sampling_rate, output_dir):
#     audio = AudioSegment.from_file(input_file)
#     step_duration = 2000  # in milliseconds (pyAudioAnalysis uses a 2-second window for speaker diarization)
#     start_time = 0

#     for i in range(len(speaker_labels) - 1):
#         if speaker_labels[i] != speaker_labels[i + 1]:
#             end_time = i * step_duration
#             speaker_id = speaker_labels[i]
#             output_file = os.path.join(output_dir, f"speaker_{speaker_id}_start_{start_time}_end_{end_time}.mp3")
#             chunk = audio[start_time:end_time]
#             chunk.export(output_file, format='mp3')
#             start_time = end_time

#     # Save the last chunk
#     speaker_id = speaker_labels[-1]
#     end_time = len(audio)
#     output_file = os.path.join(output_dir, f"speaker_{speaker_id}_start_{start_time}_end_{end_time}.mp3")
#     chunk = audio[start_time:end_time]
#     chunk.export(output_file, format='mp3')


# def speaker_diarisation(directory, file, num_speakers):
#     input_file = os.path.join(directory, file)

#     # Convert input file to mp3 format
#     input_file_mp3 = convert_to_mp3(input_file)
#     print(f"File converted\n")

#     # Read audio file
#     [sampling_rate, signal] = audioBasicIO.read_audio_file(input_file_mp3)
#     print(f"Signal shape: {signal.shape}")
#     print(f"Reading audio file\n")

#     # Check if the audio is stereo, if yes, convert to mono
#     if len(signal.shape) == 2 and signal.shape[1] == 2:
#         signal = audioBasicIO.stereo_to_mono(signal)

#     # Speaker diarization
#     # issue is here ...
#     # speaker_labels = aS.speaker_diarization(signal, sampling_rate, num_speakers)
#     # Call the updated speaker_diarization function
#     # mid_window = 0.5
#     # mid_step = 0.05
#     # short_window = 0.05
#     # lda_dim = 0
#     # plot_res = 1
#     # UnicodeDecodeError: 'utf-8' codec can't decode byte 0xff in position 45: invalid start byte
#     #   File "/home/james/.local/share/virtualenvs/whisper-MYUEtSTx/lib/python3.10/site-packages/pyAudioAnalysis/audioSegmentation.py", line 168, in read_segmentation_gt
#     # change "rt" to "rb"
#     speaker_labels, purity_cluster_m, purity_speaker_m = aS.speaker_diarization(input_file_mp3, num_speakers)#, mid_window, mid_step, short_window, lda_dim, plot_res)

#     # Print speaker change points
#     for i in range(len(speaker_labels) - 1):
#         if speaker_labels[i] != speaker_labels[i + 1]:
#             print(f"Speaker change at {round((i * 2.0) / sampling_rate, 2)} seconds")

#     # Save speaker chunks in a directory
#     output_dir = os.path.join(directory, "speaker_chunks")
#     os.makedirs(output_dir, exist_ok=True)
#     print(output_dir)
#     save_speaker_chunks(input_file, speaker_labels, sampling_rate, output_dir)


# if __name__ == "__main__":
#     parser = argparse.ArgumentParser(description="Speaker diarization from audio files")
#     parser.add_argument("-d", "--directory", help="Path to the folder containing the audio file")
#     parser.add_argument("-f", "--file", help="Audio file name")
#     parser.add_argument("-s", "--num_speakers", type=int, help="Number of speakers")

#     args = parser.parse_args()

#     speaker_diarisation(args.directory, args.file, args.num_speakers)




# import wave
# import numpy as np
# from pyannote.audio.features import Pretrained
# from pyannote.audio.pipeline import SpeakerDiarization


# def pyannote_diarization(directory, file, out):
#     input_file = os.path.join(directory, file)

#     audio = AudioSegment.from_file(input_file, format="m4a")
#     wav_file = input_file.replace(".m4a", ".wav")
#     audio.export(wav_file, format="wav")
#     print(wav_file)
#     output_file = f"{directory}/{out}"

#     # Initialize the diarization pipeline
#     diarization = SpeakerDiarization(segmentation="pyannote/segmentation", embedding="pyannote/embedding", clustering="pyannote/cluster")

#     # Load audio file
#     with wave.open(wav_file, "rb") as wave_file:
#         n_channels = wave_file.getnchannels()
#         sample_width = wave_file.getsampwidth()
#         frame_rate = wave_file.getframerate()
#         n_frames = wave_file.getnframes()
#         duration = n_frames / float(frame_rate)

#     # Read audio signal
#     signal = np.frombuffer(wave_file.readframes(n_frames), dtype=np.int16)

#     # Convert stereo to mono if necessary
#     if n_channels == 2:
#         signal = signal.reshape((-1, 2)).mean(axis=1)

#     # Resample to 16 kHz
#     if frame_rate != 16000:
#         from scipy.signal import resample_poly
#         signal = resample_poly(signal, up=16000, down=frame_rate)

#     # Perform speaker diarization
#     hypothesis = diarization(signal, sample_rate=16000)

#     # Print speaker change points
#     for segment in hypothesis:
#         print(f"Speaker {segment.label}: {segment.start}s to {segment.end}s")

#     # Save diarization result to an output file if specified
#     if output_file is not None:
#         with open(output_file, "w") as f:
#             for segment in hypothesis:
#                 f.write(f"{segment.label}\t{segment.start}\t{segment.end}\n")

# # Usage example
# pyannote_diarization("/mnt/d/Dropbox/Temasek/Ataraxia Ascension Plate/Recordings/2023-04-15 Fall of Arenor/chunks/", "chunk_0.mp3", output_file="test_output.txt")
# pyannote_diarization("/mnt/d/Dropbox/Temasek/Ataraxia Ascension Plate/Recordings/2023-04-15 Fall of Arenor/chunks/", "audio1017151090.m4a", output_file="test_output.txt")


from pyAudioAnalysis import audioSegmentation as aS
from typing import List, Tuple
from pydub import AudioSegment
import os

from typing import Dict
from collections import defaultdict


def get_segments(flags: List[int]) -> List[Tuple[int, int, int]]:
    segments = []
    start_time = 0
    current_speaker = flags[0]

    for i in range(1, len(flags)):
        if flags[i] != current_speaker:
            end_time = i
            segments.append((start_time, end_time, current_speaker))
            start_time = end_time
            current_speaker = flags[i]

    # Add the final segment
    segments.append((start_time, len(flags), current_speaker))
    return segments


def get_speaker_subtracks(segments: List[Tuple[int, int, int]], output_audio: str) -> Dict:
    # Initialize the subtracks dictionary
    speaker_subtracks = defaultdict(lambda: AudioSegment.empty())

    frame_duration_ms = 20  # Frame duration in milliseconds; adjust based on your diarization settings

    audio = AudioSegment.from_wav(output_audio)

    # Combine the segments of the same speaker
    for segment in segments:
        start_time = segment[0] * frame_duration_ms
        end_time = segment[1] * frame_duration_ms
        speaker_id = segment[2] + 1  # Speaker IDs are 1-based
        subtrack = audio[start_time:end_time]
        speaker_subtracks[speaker_id] += subtrack

    return speaker_subtracks


def get_subtracks(segments: List[Tuple[int, int, int]], output_audio: str) -> List[Tuple[AudioSegment, int]]:
    frame_duration_ms = 20  # Frame duration in milliseconds; adjust based on your diarization settings

    audio = AudioSegment.from_wav(output_audio)

    subtracks = []
    for segment in segments:
        start_time = segment[0] * frame_duration_ms
        end_time = segment[1] * frame_duration_ms
        speaker_id = segment[2] + 1  # Speaker IDs are 1-based
        subtrack = audio[start_time:end_time]
        subtracks.append((subtrack, speaker_id))
    return subtracks


directory = "/mnt/d/Dropbox/Temasek/Ataraxia Ascension Plate/Recordings/2023-04-15 Fall of Arenor/chunks/"
number_of_speakers = 4

input_audio = os.path.join(directory, "chunk_0.mp3")
output_audio = os.path.join(directory, "output_audio.wav")

# Load the audio file
audio = AudioSegment.from_mp3(input_audio)

# Convert to mono and set sample rate to 16 kHz
audio = audio.set_channels(1).set_frame_rate(16000)

# Export the processed audio
audio.export(output_audio, format="wav")

# Perform speaker diarization
flags, classes, class_names = aS.speaker_diarization(output_audio, number_of_speakers)

# # Print the results
# print("Diarization results:")
# for i, segment in enumerate(flags):
#     print(f"Segment {i + 1}: Speaker {segment + 1}")

segments = get_segments(flags)

subtracks = get_subtracks(segments, output_audio)
speaker_subtracks = get_speaker_subtracks(segments, output_audio)

output_folder = f"{directory}output_subtracks/"
os.makedirs(output_folder, exist_ok=True)

# save individual sound bites
for i, (subtrack, speaker_id) in enumerate(subtracks):
    output_file = os.path.join(output_folder, f"speaker_{speaker_id}_segment_{i + 1}.wav")
    subtrack.export(output_file, format="wav")

# Save the continuous subtracks for each speaker
for speaker_id, subtrack in speaker_subtracks.items():
    output_file = os.path.join(output_folder, f"speaker_{speaker_id}_continuous.wav")
    print(output_file)
    subtrack.export(output_file, format="wav")
