
import re
import os
import json
import glob
import call_GPT
import GPT4_call
import ebooklib
import whisper
import openai
import argparse
from ebooklib import epub
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Tuple


def process_text(blocks) -> Tuple[List, int]:
    # Join the blocks of text into a single string
    text = ' '.join(blocks)
    print(repr(text)) # see new lines

    # Replace stylised quotes
    text = text.replace('‘', "'").replace('’', "'")
    text = text.replace('\n', "")

    # Add a new line before each quote
    text = re.sub(r" '", "\n'", text)
    text = re.sub(r"' ", "'\n ", text)

    LoD = []
    for item in text.split('\n'):
        temp_dict = {}
        if item.startswith("'"):
            temp_dict['Speaker'] = 'unknown'
            temp_dict['Speech'] = item
        else:
            temp_dict['Speaker'] = 'Alarak'
            temp_dict['Speech'] = item
        LoD.append(temp_dict)

    # Use json.dumps to convert to a JSON formatted string
    json_string = json.dumps(LoD, indent=4)

    # Print the result
    print(json_string)

    return LoD, len(text)

# pipenv install EbookLib

parser = argparse.ArgumentParser(description='Convert epub into script.')
parser.add_argument('-a', '--apiKeyPath', help='Location of api key.')
parser.add_argument('-f', '--folder', help='Location of saved files.')
parser.add_argument('-s', '--savename', help='Save ID.')
parser.add_argument('-e', '--Epub', help='Save ID.')
args = parser.parse_args()
apiKeyPath = args.apiKeyPath
folder = args.folder
savename = args.savename
Epub = args.Epub

target_book = f"{folder}/{Epub}"

try:
    ACCESS_TOKEN = GPT4_call.read_api_key(f"{apiKeyPath}/gpt4_api")
except:
    ACCESS_TOKEN = GPT4_call.read_api_key()

try:
    api_key = whisper.read_api_key(f"{apiKeyPath}/api_key")
except:
    api_key = whisper.read_api_key()

openai.api_key = api_key

# Load the epub file
book = epub.read_epub(target_book)

# prompt = """Rewrite the following text into a list of dictionaries with the key 'Speaker' and value is always the speech, where 'Speaker' is the name of the speaker or narrator if no speaker is specified, and the value is any speech or narrated text. Replace stylized quotes in 'Speech' with regular quotes and mark the speaker as 'unknown' if not known. The text to be rewritten is: """
prompt = "Given the following spoken passages, please assign a speaker name for the ones marked as 'unknown'. Use context clues from the given speeches to determine the most likely speaker for the ones marked as 'unknown'. Replace 'unknown' with the correct speaker. The conversation is as follows, Alarak is the narrator, not a character:"

# Get a list of items of type ITEM_DOCUMENT
document_items = list(book.get_items_of_type(ebooklib.ITEM_DOCUMENT))

# Iterate over the items and print their content
n = 0
nn = 0
for item in document_items:
    # Decoding as 'utf-8'. You may need to adjust this if the text is in a different encoding.
    content = item.get_content().decode('utf-8')

    # Parse the content with BeautifulSoup
    soup = BeautifulSoup(content, 'html.parser')

    # Initialize an empty list to hold blocks of text
    blocks = []
    # Initialize a counter
    count = 0
    rolling_totals = 0

    # Find elements with the desired classes
    for p in soup.find_all('p', class_=['textfirst', 'calibre8', 'calibre7']):
        # Append the text of the current element to the current block
        blocks.append(p.get_text())
        # Increment the counter
        count += 1
        rolling_total = len(p.get_text())
        rolling_totals += rolling_total
        # print(n, count, nn)

        # If we've collected 10 elements, process them
        if rolling_totals > 3500 and rolling_totals < 4500:
            nn += 1
            LoD, text = process_text(blocks)

            initial_file = f'{folder}/{savename}-epubfragment-{nn}.json'
            with open(initial_file, 'w') as g:
                json.dump(LoD, g)

            save_file = f'{folder}/{savename}-GPT-4-{nn}.json'
            print(f"Saving to: {save_file} - Character count: {text}")

            ## GPT-3.5
            # if not os.path.exists(save_file):
                # GPT_reply1 = call_GPT.direct_contact_GPT(LoD, prompt)
                # # print("GPT_reply: ", GPT_reply)  # check what's inside GPT_reply

                # the_reply1 = GPT_reply1['choices'][0]['message']['content']
                # # print("the_reply: ", the_reply)  # check what's inside the_reply

            ## GPT-4
            if not os.path.exists(save_file):
                the_reply1 = GPT4_call.process_message(LoD, prompt, ACCESS_TOKEN)
                print(the_reply1)

                with open(save_file, 'w') as f:
                    json.dump([the_reply1], f)

            # print(f"\n{the_reply1}\n")

            # Reset blocks and counter for the next batch
            blocks = []
            count = 0
            rolling_totals = 0
            break


        # need to account for an instance of over shoot !!!!!!!!!!!!!
        # i.e. when rolling_totals > 8000
        elif rolling_totals >= 4500 and rolling_totals < 8000:
            LoD = process_text(blocks)
            print(f"Too many characters, terminating.")
            break

        else:
            pass

    n += 1
    if n > 8:
        break


def replacer(match):
    s = match.group()
    return s.replace("'", '"')


# prompt_cleanup = "Please convert the following into a json item with a list of dictionaries, remove all newlines and additional '\\':"

files = glob.glob(f'{folder}/{savename}-GPT-4-*.json')

parts = []
for file in files:
    number = file.split(".")[0].split("-")[-1]
    ori_json = f'{folder}/{savename}-epubfragment-{number}.json'
    with open(file, 'r', encoding='utf-8') as f, open(ori_json, 'r') as g:
        ori = json.loads(g.read())

        data = json.load(f)
        for i in data:

            result = re.sub(r"^.*:\s*\n", "", i, flags=re.MULTILINE)
            # remove newlines
            s = re.sub(r'\n', '', result)

            # replace single quotes with double quotes to make it valid JSON
            s = re.sub(r"(\w)(\')(\w)", r"\1---\3", s)
            s = re.sub(r"(\")(\')", r"\1---", s)
            s = re.sub(r"(\')(\")", r"---\2", s)

            # # replace single quotes with double quotes to make it valid JSON
            s = re.sub(r"'.*?'", replacer, s)

            s = s.replace('---', "'")

            # # parse the JSON string into Python list of dictionaries
            try:
                lst = json.loads(s)
                print(f"\n{len(ori)}")
                print(len(lst))

                for r in range(len(ori)):
                    print(f"\n{ori[r]}")
                    print(f"{lst[r]}\n")

                parts.append(lst)
            except:
                print("Broken string, thanks GPT-4")
    break




# python ./build_audiobook.py | jq
