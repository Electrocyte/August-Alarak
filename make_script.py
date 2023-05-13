import json
import glob
import os

def count_integer_folders(path: str) -> int:
    # List all items in the directory
    items = os.listdir(path)

    # Filter the items to only include folders that are also integers
    integer_folders = [item for item in items if os.path.isdir(os.path.join(path, item)) and item.isdigit()]

    # Count the number of integer folders
    count = len(integer_folders)

    return count


def format_conversation_for_summarization(conversation):
    formatted_text = ""

    for dictionary in conversation:
        for speaker, text in dictionary.items():
            formatted_text += f"{speaker}: {text}\n"

    return formatted_text.strip()


directory = "/mnt/d/Dropbox/Temasek/Ataraxia Ascension Plate/Recordings/2023-04-15 Fall of Arenor/chunks/"

# count number of folders in directory that are also int
integer_folder_count = count_integer_folders(directory)
print(f"Number of integer folders in '{directory}': {integer_folder_count}")

all_transcripts = []
for n in range(integer_folder_count):
    globbed_files = glob.glob(f"{directory}/{n}/transcripts/**/*.json")
    for gf in globbed_files:
        with open(gf, 'r', encoding='utf-8') as f:
            current = json.load(f)
            all_transcripts.append(current)

formatted_conversation = format_conversation_for_summarization(all_transcripts)

print(all_transcripts)
print()
print(formatted_conversation)

with open(f"{directory}/LoDs-summary.json", 'w', encoding='utf-8') as f:
    json.dump(all_transcripts, f)

with open(f"{directory}/ss-summary.json", 'w', encoding='utf-8') as f:
    json.dump(formatted_conversation, f)

# I will provide you with audio transcript (first post) for a file with no speaker diarisation and an audio
# transcript that contains the diarised audio transcript (second post). Please polish the diarised transcript
# using the full original audio transcript. To confirm you understand post "Understood" after this instruction
# and subsequently after I post the no speaker diarisation transcript AND the speaker diarisation transcript.

# audio transcript without speaker diarization as follows:
# {"text": "Hello, my name is John. I am a student at the University of Singapore."}

# audio transcript with speaker diarization as follows:
# [{"SPEAKER_00": "Hello, my name is John."}, {"SPEAKER_01": "I am a student at the University of Singapore."}]

# attention for GPT-4 is currently not long enough for this to work meaningfully.

# Steps:
# 1. Run diarise2.py
# 2. Run make_script.py

# Edits: change diarise2 to target all chunks in a folder
# Hook this up with GPT once the token limit is increased
