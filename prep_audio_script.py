import argparse
import json

parser = argparse.ArgumentParser(description='Convert epub into script.')
parser.add_argument('-d', '--directory', help='Location of saved files.')
parser.add_argument('-s', '--script', help='json script filename.')
args = parser.parse_args()

directory = args.directory
script = args.script

file = f"{directory}/{script}"

elevenLabsR = []
with open(file, 'r') as f:
    elevenLabs = json.load(f)

    for i in elevenLabs:
        speaker = i["Speaker"]
        speech = i["Speech"].split('. ')  # split speech into list of sentences at '. '
        print(speaker, speech)
        elevenLabsR.append({speaker: ["0.25", "0.80", speech]})
print(elevenLabsR)

script_out = script.replace('.json', '-11LR')
readyfile = f'{directory}/{script_out}.json'
with open(readyfile, 'w') as g:
    json.dump(elevenLabsR, g, indent=4)  # include indent in dump to format output file

# Use json.dumps to convert to a JSON formatted string
json_string = json.dumps(elevenLabsR, indent=4)

# Print the result
print(json_string)
