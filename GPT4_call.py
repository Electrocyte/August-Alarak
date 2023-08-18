# from os import environ
# environ['CHATGPT_BASE_URL'] = "https://bypass.churchless.tech/"
# from revChatGPT.V1 import Chatbot
import argparse
import json
import call_GPT
import glob
import os
import openai
import whisper


def read_api_key(file_path: str = "gpt4_api") -> str:
    with open(file_path, "r") as f:
        return f.read().strip()


# def process_message(text: str, prompt: str, ACCESS_TOKEN: str) -> str:

#     access = {
#         "access_token": ACCESS_TOKEN,
#         # "api_key ": ACCESS_TOKEN,
#         "model": "gpt-4",
#         # "temperature": 0.5,
#     }

#     chatbot = Chatbot(access)
#     data = chatbot.ask(f"{prompt} {text}")
#     res = ""
#     for i in data:
#         res = i["message"]
#     return res


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='GPT-4.')

    parser.add_argument('-a', '--accessToken', help='Location of api key.')
    parser.add_argument('-t', '--text', help='Input text.')
    parser.add_argument('-d', '--directory', help='Save location.')
    # parser.add_argument('-p', '--prompt', help='Prompt.')

    args = parser.parse_args()

    accessToken = args.accessToken
    text = args.text
    directory = args.directory
    # prompt = args.prompt

    try:
        # ACCESS_TOKEN = GPT4_call.read_api_key(f"{apiKeyPath}/gpt4_api2")
        ACCESS_TOKEN = read_api_key(f"{accessToken}/gpt4_api")
    except:
        ACCESS_TOKEN = read_api_key()

    try:
        api_key = whisper.read_api_key(f"{accessToken}/api_key")
    except:
        api_key = whisper.read_api_key()

    openai.api_key = api_key

    # try:
    #     ACCESS_TOKEN = read_api_key(f"{accessToken}/gpt4_api")
    # except:
    #     ACCESS_TOKEN = read_api_key()

    json_globs = glob.glob(text)
    print(text)
    print(json_globs, "\n")

    clean_out = f"{directory}/clean/"
    os.makedirs(clean_out, exist_ok=True)

    for i in range(0, len(json_globs), 2):
        print(i,i+2)
        texts = json_globs[i:i+2]
        print(texts)
        text1 = texts[0]
        if len(texts) > 1:
            text2 = texts[1]

        with open(text1, 'r', encoding='utf-8') as f:
            json_text1 = json.load(f)

        if len(texts) > 1:
            with open(text2, 'r', encoding='utf-8') as f:
                json_text2 = json.load(f)

        prompt_polish = "You are a great story teller, Alarak, please polish the following text to make it have greater flow. The following is a summary from an audio recording:"
        prompt_spelling = "Polish the spelling of the falling names. The city is called Arenor. There is another city called Algibar. \
                           Characters include Selim, Zalora Zamzahra, Kaksys, Arkris, Thraldir, Solas, Bakar, \
                           Novemnine, Belisarius, Roxelana, Freya, Ravenna, Yonarr, Eren, Mikasa, Hela, Melo, \
                           Mira, Atara, Selendis. Please correct any spelling mistakes, where required:"
        prompt_bullets = "Now convert this into the most salient 10 bullet points."

        if len(texts) > 1:
            list_of_text = list(json_text1.values()) + list(json_text2.values())
        else:
            list_of_text = list(json_text1.values())
        no_chars = len(list_of_text[0])
        print(f"Characters in text: {no_chars}")

        if no_chars > 8000:
            print("Text too long, please shorten to less than 8000 characters.")
            print(texts)
            break

        save_flow = f"{clean_out}/clean-flow-{i}.json"
        save_spelling = f"{clean_out}/clean-spelling-{i}.json"
        save_bullets = f"{clean_out}/clean-summary-{i}.json"

        if not os.path.exists(save_flow):
            GPT_reply1 = call_GPT.direct_contact_GPT4(list_of_text, prompt_polish)
            pol_res = GPT_reply1['choices'][0]['message']['content']
            with open(save_flow, 'w') as f:
                json.dump(pol_res, f)
        else:
            with open(save_flow, 'r', encoding='utf-8') as f:
                pol_res = json.load(f)

        # if not os.path.exists(save_flow):
        #     pol_res = process_message(list_of_text, prompt_polish, ACCESS_TOKEN)
        #     with open(save_flow, 'w', encoding='utf-8') as f:
        #         json.dump(pol_res, f)
        # else:
        #     with open(save_flow, 'r', encoding='utf-8') as f:
        #         pol_res = json.load(f)

        # print("Polish result: ", pol_res)

        if not os.path.exists(save_spelling):
            GPT_reply1 = call_GPT.direct_contact_GPT4(pol_res, prompt_spelling)
            spe_res = GPT_reply1['choices'][0]['message']['content']
            with open(save_spelling, 'w') as f:
                json.dump(spe_res, f)
        else:
            with open(save_spelling, 'r', encoding='utf-8') as f:
                spe_res = json.load(f)

        # if not os.path.exists(save_spelling):
        #     spe_res = process_message(pol_res, prompt_spelling, ACCESS_TOKEN)
        #     with open(save_spelling, 'w', encoding='utf-8') as f:
        #         json.dump(spe_res, f)
        # else:
        #     with open(save_spelling, 'r', encoding='utf-8') as f:
        #         spe_res = json.load(f)

        # print("Spelling result: ", spe_res)

        if not os.path.exists(save_bullets):
            GPT_reply1 = call_GPT.direct_contact_GPT4(spe_res, prompt_bullets)
            bul_res = GPT_reply1['choices'][0]['message']['content']
            with open(save_bullets, 'w') as f:
                json.dump(bul_res, f)
        else:
            with open(save_bullets, 'r', encoding='utf-8') as f:
                bul_res = json.load(f)

        # if not os.path.exists(save_bullets):
        #     bul_res = process_message(spe_res, prompt_bullets, ACCESS_TOKEN)
        #     with open(save_bullets, 'w', encoding='utf-8') as f:
        #         json.dump(bul_res, f)
        # else:
        #     with open(save_bullets, 'r', encoding='utf-8') as f:
        #         bul_res = json.load(f)

        print("Bullets result: ", bul_res)


    final_bullets = f"{clean_out}/final-summary-take.json"
    prompt_final = "Take these bullet points from a dungeons and dragons game and pick the 25 bullet points that make the best story."
    clean_json_globs = glob.glob(f"{clean_out}/*summary*.json")
    print(clean_json_globs, "\n")

    parts = []
    for cjg in clean_json_globs:
        with open(cjg, 'r', encoding='utf-8') as f:
            part = json.loads(f.read())
            part = part.replace("\n\n", "\n")
            parts.append(part)

    # Process any remaining parts if the character count doesn't exceed 7000
    chunk_size = 7500

    split_parts = parts
    if len(parts) == 1:
        split_parts = [parts[0][i:i+chunk_size] for i in range(0, len(parts[0]), chunk_size)]
    print(split_parts)

    print(f"\n{final_bullets}")
    if not os.path.exists(final_bullets):
        GPT_reply1 = call_GPT.direct_contact_GPT4(split_parts, prompt_final)
        save_parts = GPT_reply1['choices'][0]['message']['content']
        with open(final_bullets, 'w') as f:
            json.dump(save_parts, f)
    else:
        with open(final_bullets, 'r', encoding='utf-8') as f:
            save_parts = json.load(f)

    # if not os.path.exists(final_bullets):
    #     save_parts = process_message(split_parts, prompt_final, ACCESS_TOKEN)
    #     with open(final_bullets, 'w', encoding='utf-8') as f:
    #         json.dump(save_parts, f)
    # else:
    #     with open(final_bullets, 'r', encoding='utf-8') as f:
    #         save_parts = json.load(f)
