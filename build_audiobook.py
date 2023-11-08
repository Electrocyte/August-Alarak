
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
# import statistics
from bs4 import BeautifulSoup, Tag
from typing import List, Dict, Any, Tuple, Optional
import os


def get_headers(soup: BeautifulSoup) -> list:
    """Extract all headers from h1 to h6."""
    return [header for i in range(1, 7) for header in soup.find_all(f'h{i}')]


def extract_content_between_headers(header, next_header) -> str:
    """Extract content between two headers."""
    content = []
    curr_element = header.find_next_sibling()
    while curr_element and curr_element != next_header:
        if isinstance(curr_element, Tag):
            content.append(curr_element.get_text().strip())
        curr_element = curr_element.next_sibling if curr_element else None
    return ''.join(content)


def split_by_headers(soup: BeautifulSoup) -> dict:
    """Split the content by headers and return as dictionary."""
    headers = get_headers(soup)
    sections = {}
    for index, header in enumerate(headers):
        section_name = header.get_text().strip().replace(' ', '_').replace('.', '').replace(',', '')
        next_header = headers[index + 1] if index < len(headers) - 1 else None
        sections[section_name] = extract_content_between_headers(header, next_header)
    return sections


def generate_unique_name(base_name: str, existing_names: Dict[str, int]) -> str:
    """Generate a unique name based on the base name."""
    if base_name not in existing_names:
        return base_name

    i = 1
    while f"{base_name}_{i}" in existing_names:
        i += 1

    return f"{base_name}_{i}"


def identify_headers(book) -> Dict[str, int]:
    """Return a dictionary with section names as keys and their character counts as values."""
    document_items = list(book.get_items_of_type(ebooklib.ITEM_DOCUMENT))
    section_counts = {}
    predefined_sections = ["book_one"]  # Add any other predefined sections here

    for section in predefined_sections:
        section_counts[section] = 0

    for item in document_items:
        content = item.get_content().decode('utf-8')
        soup = BeautifulSoup(content, 'html.parser')
        sections = split_by_headers(soup)

        for section_name, section_content in sections.items():
            unique_name = generate_unique_name(section_name, section_counts)
            print(f"Section {unique_name} Character Count: {len(section_content)}")
            section_counts[unique_name] = len(section_content)

    return section_counts


def extract_content_from_book(book, folder, savename):
    # Ensure the save directory exists
    if not os.path.exists(folder):
        os.makedirs(folder)

    document_items = list(book.get_items_of_type(ebooklib.ITEM_DOCUMENT))

    chapter_count = 0
    chapters = {}

    for item in document_items:
        content = item.get_content().decode('utf-8')
        soup = BeautifulSoup(content, 'html.parser')

        paragraphs = soup.find_all('p')
        is_within_chapter = False
        chapter_content = []

        for p in paragraphs:
            text = p.get_text().strip()

            classes = p.get('class', [])

            # Starting a new chapter
            if 'textfirst' in classes:
                # If we're already within a chapter, save it
                if is_within_chapter and chapter_content:
                    save_chapter(chapter_content, folder, savename, chapter_count)
                    print(f"Chapter {chapter_count} Character Count:", sum(len(para) for para in chapter_content))
                    chapter_count += 1
                    chapter_content = []

                is_within_chapter = True
                chapter_content.append(text)

            elif 'calibre8' in classes and is_within_chapter:
                chapter_content.append(text)

            elif 'break' in classes and is_within_chapter:
                # chapter_content.append("*")  # denoting break
                next_p = p.find_next('p')
                if next_p and 'textbreak' in next_p.get('class', []):
                    chapter_content.append(next_p.get_text().strip())

        # Save the last chapter if it's present
        if chapter_content:
            chapter_info = {
                "content": chapter_content,
                "header": None  # Placeholder for the header
            }
            chapters[f"Chapter {chapter_count}"] = chapter_info
            save_chapter(chapter_content, folder, savename, chapter_count)
            print(f"Chapter {chapter_count} Character Count:", sum(len(para) for para in chapter_content))
            chapter_count += 1

    return chapters


def save_chapter(chapter_content, folder, savename, chapter_count):
    initial_file = f'{folder}/{savename}-epubchapter-{chapter_count}.json'
    print(f"\n{initial_file}")
    with open(initial_file, 'w') as g:
        json.dump(chapter_content, g)

    print(f"Saved chapter {chapter_count} to {initial_file}")


def compare_counts(header_counts: Dict[str, int], chapters: Dict[str, Dict]):
    for chapter, chapter_info in chapters.items():
        content_length = sum(len(para) for para in chapter_info["content"])

        # Find the header that matches this content length
        for header, h_count in header_counts.items():
            if content_length == h_count:
                chapter_info["header"] = header
                # Do not break if you want to keep unmatched headers
                break

    return chapters

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
    # ACCESS_TOKEN = GPT4_call.read_api_key(f"{apiKeyPath}/gpt4_api2")
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

onlyprompt = "Given the following spoken passages, please assign a speaker name for the speaker marked as 'unknown'. \
    Use context clues from the given speeches to determine the most likely speaker for the ones marked as 'unknown'. \
        Replace 'unknown' with the correct speaker. \
            The conversation is as follows, Alarak is the narrator, not a character:"

################### EXTRACT CHAPTERS #####################

section_counts = identify_headers(book)
chapters = extract_content_from_book(book, folder, savename)
updated_chapters = compare_counts(section_counts, chapters)

all_headers = set(section_counts.keys())
matched_headers = set(chap_info['header'] for chap_info in updated_chapters.values() if chap_info['header'])

missing_headers = all_headers - matched_headers

################### SPLIT INTO CHUNKS #####################

# def split_into_chunks(content, max_chars=4500):
def split_into_chunks(content, max_chars=16000):
    """Splits content into chunks of maximum characters, ensuring words are not split."""
    chunks = []
    current_chunk = ""
    current_length = 0

    for para in content:
        # If adding the next paragraph exceeds the max_chars limit
        if current_length + len(para) > max_chars:
            # Save the current chunk
            chunks.append(current_chunk.strip())
            current_chunk = para
            current_length = len(para)
        else:
            # Append the paragraph to the current chunk
            current_chunk += " " + para
            current_length += len(para) + 1  # +1 accounts for space

    # Save any remaining content
    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks


def split_saved_jsons_into_chunks(folder, savename):
    chapter_count = 0

    # Continue until there's no more file with the given name pattern
    while os.path.exists(f'{folder}/{savename}-epubchapter-{chapter_count}.json'):
        with open(f'{folder}/{savename}-epubchapter-{chapter_count}.json', 'r') as f:
            content = json.load(f)

        # Get chunks
        chunks = split_into_chunks(content)

        # Create a unique directory for this chapter
        chapter_folder = os.path.join(folder, f'{savename}-chapter-{chapter_count}')
        if not os.path.exists(chapter_folder):
            os.makedirs(chapter_folder)

        chap_chunk = f'{chapter_folder}/chunk/'
        os.makedirs(chap_chunk, exist_ok=True)

        # Save each chunk to the unique chapter folder
        for i, chunk in enumerate(chunks):
            chunk_filename = os.path.join(chap_chunk, f'chunk-{i}.json')
            with open(chunk_filename, 'w') as g:
                json.dump(chunk, g)

            # print(f"Saved chunk {i} of chapter {chapter_count} to {chunk_filename}")

        chapter_count += 1

# Call the function
split_saved_jsons_into_chunks(folder, savename)

################### GPT4 speaker analysis #####################

def process_text(blocks) -> Tuple[List, int]:
    # Join the blocks of text into a single string

    if isinstance(blocks[0], dict):
        # Assuming the dictionary has a 'Speech' key containing the text
        text_blocks = [block['Speech'] for block in blocks if 'Speech' in block]
        text = ' '.join(text_blocks)
    else:
        # Original behavior: join all blocks
        pass

    # Replace stylised quotes
    text = blocks.replace('‘', "'").replace('’', "'")
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

    return LoD, len(text)


def count_chars_in_json(data):
    json_string = json.dumps(data)
    return len(json_string)


def analyse_GPT4(LoD: List[Dict[str, str]], preprompt: str, postprompt: str, chapter_folder: str, fragment_count: str, rolling_totals: int) -> None:
    # print(f"Number of characters: {rolling_totals}")

    half_total = rolling_totals / 2
    new_dict = {"Speaker": "$$$", "Speech": "$$$"}
    i_counter = 0
    for e, i in enumerate(LoD):
        i_counter += len(i['Speech'])
        if i_counter > half_total:
            LoD.insert(e, new_dict)
            break

    p1 = LoD[0:e]
    p2 = LoD[e:]

    pp1 = f"List1, provide speakers for this: {p1}, List2, only use this for context: {p2}"
    pp2 = f"List2, provide speakers for this: {p2}, List1, only use this for context: {p1}"

    pp3 = f"Provide speakers for this: {p2}"

    gpt_folder = f'{chapter_folder}/dicts/'
    gpt_pre = f'{chapter_folder}/pre/'
    gpt_post = f'{chapter_folder}/post/'

    intermed_file = f'{gpt_folder}/gpt-ready-{fragment_count}.json'
    with open(intermed_file, 'w') as g:
        json.dump(LoD, g)

    chars = count_chars_in_json(LoD)
    # print(f"Number of characters: {chars} {intermed_file}")
    if chars >= 8000:
        print("Text too long, please shorten to less than 8000 characters.\n")

    pre_save_file = f'{gpt_pre}/GPT-4-pre-{fragment_count}.json'
    post_save_file = f'{gpt_post}/GPT-4-post-{fragment_count}.json'

    if len(p1) == 0:
        if not os.path.exists(pre_save_file):
            GPT_reply1 = call_GPT.direct_contact_GPT4(pp3, onlyprompt)
            the_reply1 = GPT_reply1['choices'][0]['message']['content']
            with open(pre_save_file, 'w') as f:
                json.dump([the_reply1], f)

    else:
        ## GPT-4 - API - might give more determinate replies
        if not os.path.exists(pre_save_file):
            GPT_reply1 = call_GPT.direct_contact_GPT4(pp1, preprompt)
            the_reply1 = GPT_reply1['choices'][0]['message']['content']
            with open(pre_save_file, 'w') as f:
                json.dump([the_reply1], f)

        if not os.path.exists(post_save_file):
            GPT_reply2 = call_GPT.direct_contact_GPT4(pp2, postprompt)
            the_reply2 = GPT_reply2['choices'][0]['message']['content']
            with open(post_save_file, 'w') as f:
                json.dump([the_reply2], f)

    # ##############################

    # ## GPT-4 - no API - replies are always highly indeterminate
    # if not os.path.exists(pre_save_file):
    #     the_reply1 = GPT4_call.process_message(pp1, preprompt, ACCESS_TOKEN)
    #     print(the_reply1, len(the_reply1))
    #     with open(pre_save_file, 'w') as f:
    #         json.dump([the_reply1], f)

    # ## GPT-4
    # if not os.path.exists(post_save_file):
    #     the_reply2 = GPT4_call.process_message(pp2, postprompt, ACCESS_TOKEN)
    #     print(the_reply2, len(the_reply2))
    #     with open(post_save_file, 'w') as f:
    #         json.dump([the_reply2], f)

    # ##############################

############################## run all

# chapter_count = 0

# while True:  # Infinite loop to go through all chapters
#     chapter_folder = os.path.join(folder, f'{savename}-chapter-{chapter_count}')

#     # Check if the chapter folder exists, if not, break the loop
#     if not os.path.exists(chapter_folder):
#         break

#     globs = glob.glob(f"{chapter_folder}/chunk/chunk-*.json")

#     for fragment_count, _glob_ in enumerate(globs):
#         with open(_glob_, 'r') as file:
#             print("\n", fragment_count, _glob_)

#             number = _glob_.split(".")[0].split("-")[-1]

#             content = json.load(file)
#             LoD, _ = process_text(content)

#             gpt_folder = f'{chapter_folder}/dicts/'
#             gpt_pre = f'{chapter_folder}/pre/'
#             gpt_post = f'{chapter_folder}/post/'

#             os.makedirs(gpt_folder, exist_ok=True)
#             os.makedirs(gpt_pre, exist_ok=True)
#             os.makedirs(gpt_post, exist_ok=True)

#             analyse_GPT4(LoD, preprompt, postprompt, chapter_folder, number, len(content))

#             fragment_count += 1

#     print(f"\nChapter_count: {chapter_count}")
#     chapter_count += 1

############################## run one chapter

chapter_count = 18

chapter_folder = os.path.join(folder, f'{savename}-chapter-{chapter_count}')

globs = glob.glob(f"{chapter_folder}/chunk/chunk-*.json")

for fragment_count, _glob_ in enumerate(globs):
    with open(_glob_, 'r') as file:
        print("\n", fragment_count, _glob_)

        number = _glob_.split(".")[0].split("-")[-1]

        content = json.load(file)
        LoD, _ = process_text(content)

        gpt_folder = f'{chapter_folder}/dicts/'
        gpt_pre = f'{chapter_folder}/pre/'
        gpt_post = f'{chapter_folder}/post/'

        os.makedirs(gpt_folder, exist_ok=True)
        os.makedirs(gpt_pre, exist_ok=True)
        os.makedirs(gpt_post, exist_ok=True)

        analyse_GPT4(LoD, preprompt, postprompt, chapter_folder, number, len(content))

        fragment_count += 1

print(f"\nChapter_count: {chapter_count}")

################### POST PROCESSING #####################

def replacer(match):
    s = match.group()
    return s.replace("'", '"')


def clean_up(i):
    result = re.sub(r"^.*:\s*\n", "", i, flags=re.MULTILINE)
    # print(result)
    result = re.sub(r'```python\nList1 = ', '', result)
    # print(result)
    result = re.sub(r'List1 = ', '', result)
    result = re.sub(r"\n\w.*?$", "", result, flags=re.MULTILINE)
    # print(result)
    # remove newlines
    s = re.sub(r'\n', '', result)
    # print(s)
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
    # print(s)
    s = re.sub(r'\`\`\`python    ', '[', s)
    s = re.sub(r'\`\`\`', '', s)
    s = re.sub(r'\–$', '"}]', s)

    s = re.sub(r'^\s*\{"', '[{"', s)
    # s = re.sub(r'(?<=\]\s)[\s\S]*', '[', s)
    # print(s)
    s = re.sub(r'python  {', '[{', s)
    s = re.sub(r'^python', '', s)
    s = re.sub(r'\},\s*$', '}]', s)
    s = re.sub(r'\}$', '}]', s)
    s = re.sub(r'\.$', '"}]', s)
    # print(s)
    return s


def check_original(s: str, ori: List[Dict[str, str]], _type_: str, fname: str) -> Optional[List[Dict[str, str]]]:
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
                # print(len(lst))

        print(len(lst) == len(ori), "identified:", len(lst), "input:", len(ori))
        if len(lst) == len(ori):
            cleaned_dicts = ori

            for r in range(len(ori)):
                # print(cleaned_dicts[r].values(), lst[r].values())
                if cleaned_dicts[r]['Speaker'] == 'unknown':
                    cleaned_dicts[r]['Speaker'] = lst[r]['Speaker']

            cleaned_list = [d for d in cleaned_dicts if d['Speaker'] != '$$$']

            return cleaned_list
    except:
        print(f"Broken string, thanks GPT-4 {fname}")
        return None


def audio_ready(pre_part, post_part, file, postfile, number):
    if pre_part is None:
        failed_files.append(f"\n{file} \n{pre_part}")
        if post_part is None:
            failed_files.append(f"\n{postfile} \n{post_part}")
    else:
        cleaned_json = f'{clean_files}/ready-for-audio-{number}.json'
        print(cleaned_json)
        with open(cleaned_json, 'w') as k:
            if post_part is not None:
                json.dump(pre_part + post_part, k)
            else:
                json.dump(pre_part, k)


chapter_count = len(chapters)

print(chapter_count)

for i in range(chapter_count):
    chapter_folder = os.path.join(folder, f'{savename}-chapter-{i}')

    files = glob.glob(f'{chapter_folder}/pre/*.json')

    clean_files = f'{chapter_folder}/clean/'
    os.makedirs(clean_files, exist_ok=True)

    print(f"\nChapter: {i} No. files: {len(files)}")

    failed_files = []
    for file in files:
        number = file.split(".")[0].split("-")[-1]

        ori_json = f'{chapter_folder}/dicts/gpt-ready-{number}.json'
        postfile = file.replace("pre", "post")

        print(f"{i}-Chunk-{number} {file} {postfile} {ori_json}")

        if os.path.exists(file) and os.path.exists(postfile):
            with open(file, 'r', encoding='utf-8') as f, open(ori_json, 'r') as g, open(postfile, 'r', encoding='utf-8') as h:

                ori = json.loads(g.read())
                predata = json.load(f)
                postdata = json.load(h)

                for i in range(len(predata)):

                    pre_s = clean_up(predata[i])
                    post_s = clean_up(postdata[i])

                    index = next(i for i, d in enumerate(ori) if d["Speaker"] == "$$$")

                    # # parse the JSON string into Python list of dictionaries
                    pre_part = check_original(pre_s, ori, "before", file)
                    post_part = check_original(post_s, ori, "after", postfile)

                    audio_ready(pre_part, post_part, file, postfile, number)

        else:
            with open(file, 'r', encoding='utf-8') as f, open(ori_json, 'r') as g:

                ori = json.loads(g.read())
                predata = json.load(f)

                for i in range(len(predata)):

                    pre_s = clean_up(predata[i])

                    index = next(i for i, d in enumerate(ori) if d["Speaker"] == "$$$")

                    # # parse the JSON string into Python list of dictionaries
                    pre_part = check_original(pre_s, ori, "after", file)

                    audio_ready(pre_part, None, file, "not-available", number)
