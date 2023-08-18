import argparse
import json
import glob
import os

parser = argparse.ArgumentParser(description='Convert epub into script.')
parser.add_argument('-d', '--directory', help='Location of saved files.')
parser.add_argument('-s', '--script', help='json script filename.')
args = parser.parse_args()

directory = args.directory
script = args.script

files = glob.glob(f"{directory}/clean/{script}")

elevenR = f"{directory}/11LR/"
os.makedirs(elevenR, exist_ok=True)

all_speakers = set()
unknown_speeches = []

for file in files:
    elevenLabsR = []
    with open(file, 'r') as f:
        elevenLabs = json.load(f)

        for i in elevenLabs:
            speaker = i["Speaker"].strip()
            all_speakers.add(speaker)
            speech = i["Speech"]
            if speaker == "unknown":
                unknown_speeches.append(speech)

            speech = i["Speech"].split('. ')  # split speech into list of sentences at '. '
            print(speaker, speech)
            elevenLabsR.append({speaker: ["0.25", "0.80", speech]})
    print(elevenLabsR)

    fileout = file.split('/')[-1]
    script_out = fileout.replace('.json', '-11LR')
    readyfile = f'{elevenR}/{script_out}.json'
    with open(readyfile, 'w') as g:
        json.dump(elevenLabsR, g, indent=4)  # include indent in dump to format output file

    # Use json.dumps to convert to a JSON formatted string
    json_string = json.dumps(elevenLabsR, indent=4)

    # Print the result
    print(json_string)

list_of_speakers = list(all_speakers)

sorted_speakers = sorted(list_of_speakers)
print(sorted_speakers)
print(unknown_speeches)

# Save to JSON
with open(f'{directory}/speakers.json', 'w') as outfile:
    json.dump(sorted_speakers, outfile, indent=4)
