# pipenv install pyAudioAnalysis numpy scipy scikit-learn imblearn plotly hmmlearn matplotlib eyed3

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


directory = "Recordings/2023-04-15 Fall of Arenor/chunks/"
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
