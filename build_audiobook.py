
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
    # print(repr(text)) # see new lines

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

    # # Print the result
    # print(json_string)

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

preprompt = "Given the following spoken passages, please assign a speaker name for the speaker marked as 'unknown'. \
    ONLY return List1 with speakers, identified before the '$$$' in List1 in PYTHON format. \
    Use context clues from the given speeches to determine the most likely speaker for the ones marked as 'unknown'. \
        Replace 'unknown' with the correct speaker. \
            The conversation is as follows, Alarak is the narrator, not a character:"

postprompt = "Given the following spoken passages, please assign a speaker name for the speaker marked as 'unknown'. \
    ONLY return List2 with speakers, identified after the '$$$' in List2 in PYTHON format. \
    Use context clues from the given speeches to determine the most likely speaker for the ones marked as 'unknown'. \
        Replace 'unknown' with the correct speaker. \
            The conversation is as follows, Alarak is the narrator, not a character:"

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
        if rolling_totals > 5000 and rolling_totals < 5500:
            nn += 1
            LoD, text = process_text(blocks)

            half_total = rolling_totals / 2
            new_dict = {"Speaker": "$$$", "Speech": "$$$"}
            i_counter = 0
            for e, i, in enumerate(LoD):
                i_counter += len(i['Speech'])
                if i_counter > half_total:
                    LoD.insert(e, new_dict)
                    break

            p1 = LoD[0:e]
            p2 = LoD[e:]

            pp1 = f"List1, provide speakers for this: {p1}, List2, only use this for context: {p2}"
            pp2 = f"List1, only use this for context: {p1}, List2, provide speakers for this: {p2}"

            initial_file = f'{folder}/{savename}-epubfragment-{nn}.json'
            with open(initial_file, 'w') as g:
                json.dump(LoD, g)

            pre_save_file = f'{folder}/{savename}-GPT-4-pre-{nn}.json'
            post_save_file = f'{folder}/{savename}-GPT-4-post-{nn}.json'
            # print(f"Saving to: {save_file} - Character count: {text}")

            ## GPT-3.5
            # if not os.path.exists(save_file):
                # GPT_reply1 = call_GPT.direct_contact_GPT(LoD, prompt)
                # # print("GPT_reply: ", GPT_reply)  # check what's inside GPT_reply

                # the_reply1 = GPT_reply1['choices'][0]['message']['content']
                # # print("the_reply: ", the_reply)  # check what's inside the_reply

            ## GPT-4
            if not os.path.exists(pre_save_file):
                the_reply1 = GPT4_call.process_message(pp1, preprompt, ACCESS_TOKEN)

                with open(pre_save_file, 'w') as f:
                    json.dump([the_reply1], f)

            ## GPT-4
            if not os.path.exists(post_save_file):
                the_reply2 = GPT4_call.process_message(pp2, postprompt, ACCESS_TOKEN)

                with open(post_save_file, 'w') as f:
                    json.dump([the_reply2], f)

            # print(f"\n{the_reply1}\n")

            # Reset blocks and counter for the next batch
            blocks = []
            count = 0
            rolling_totals = 0
            # break
            if "3.json" in pre_save_file:
                break


        # need to account for an instance of over shoot !!!!!!!!!!!!!
        # i.e. when rolling_totals > 8000
        elif rolling_totals >= 5500 and rolling_totals < 8000:
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


def clean_up(i):
    result = re.sub(r"^.*:\s*\n", "", i, flags=re.MULTILINE)
    result = re.sub(r'```python\nList1 = ', '', result)
    result = re.sub(r"\n\w.*?$", "", result, flags=re.MULTILINE)

    # remove newlines
    s = re.sub(r'\n', '', result)

    # replace single quotes with double quotes to make it valid JSON
    s = re.sub(r"(\w)(\')(\w)", r"\1---\3", s)
    s = re.sub(r"(\")(\')", r"\1---", s)
    s = re.sub(r"(\')(\")", r"---\2", s)
    s = re.sub(r"(\')(\.)", r"---\2", s)

    # # replace single quotes with double quotes to make it valid JSON
    s = re.sub(r"'.*?'", replacer, s)
    s = s.replace('---', "'")
    s = s.replace('"...,', '"},')
    s = re.sub(r'\w$', '"}]', s)
    s = re.sub(r'^\w.*\[', '[', s)
    s = re.sub(r'\`\`\`python    ', '[', s)
    s = re.sub(r'\`\`\`', '', s)
    s = re.sub(r'\–$', '"}]', s)

    s = re.sub(r'^\s*\{"', '[{"', s)

    return s


def check_original(s, ori, _type_):
    # find the index of dictionary with '$$$' speaker
    index = next(i for i, d in enumerate(ori) if d["Speaker"] == "$$$")

    # get all dictionaries before the one with '$$$' speaker
    speeches_before = ori[:index]

    # get all dictionaries after the one with '$$$' speaker
    speeches_after = ori[index:]

    if _type_ == "before":
        ori = speeches_before
    elif _type_ == "after":
        ori = speeches_after

    try:
        lst = json.loads(s)
        print(f"\n{len(ori)}")
        print(len(lst))

        if _type_ == "after":
            # flag variable to indicate the presence of '$$$'
            has_dollar_key = False

            # iterate over the dictionaries in the list
            for speech in lst:
                # if '$$$' is found in any value of the dictionary
                if "$$$" in speech.values():
                    has_dollar_key = True
                    break
            if not has_dollar_key:
                lst.insert(0, {"Speaker": "$$$", "Speech": "$$$"})
                print(len(lst))

        print(len(lst) == len(ori))
        if len(lst) == len(ori):
            cleaned_dicts = ori
            for r in range(len(ori)):
                # print(f"\n{ori[r]}")
                # print(f"{lst[r]}\n")
                if cleaned_dicts[r]['Speaker'] == 'unknown':
                    cleaned_dicts[r]['Speaker'] = lst[r]['Speaker']
            cleaned_list = [d for d in cleaned_dicts if d['Speaker'] != '$$$']
            return cleaned_list
    except:
        print(f"\nBroken string, thanks GPT-4")
        return None


files = glob.glob(f'{folder}/{savename}-GPT-4-pre*.json')

failed_files = []
for file in files:
    number = file.split(".")[0].split("-")[-1]
    print(number)
    ori_json = f'{folder}/{savename}-epubfragment-{number}.json'
    postfile = file.replace("pre", "post")
    with open(file, 'r', encoding='utf-8') as f, open(ori_json, 'r') as g, open(postfile, 'r', encoding='utf-8') as h:

        ori = json.loads(g.read())
        predata = json.load(f)
        postdata = json.load(h)

        for i in range(len(predata)):

            pre_s = clean_up(predata[i])
            post_s = clean_up(postdata[i])

            # print(pre_s)
            # print("\n\n")
            # print(ori)

            # # parse the JSON string into Python list of dictionaries
            pre_part = check_original(pre_s, ori, "before")
            post_part = check_original(post_s, ori, "after")

            if pre_part is None:
                failed_files.append(f"\n{file} \n{pre_part}")
                if post_part is None:
                    failed_files.append(f"\n{postfile} \n{post_part}")
            else:
                cleaned_json = f'{folder}/{savename}-ready-for-audio-{number}.json'
                print(cleaned_json)
                with open(cleaned_json, 'w') as k:
                    json.dump(pre_part + post_part, k)

failed_json = f'{folder}/{savename}-double-check-errors.json'
print(failed_json)
with open(failed_json, 'w') as l:
    json.dump(failed_files, l)

    # break



# python ./build_audiobook.py | jq
