# coding=utf-8
import os
import sys
import glob
import re
import subprocess
import colorama
import spacy
from langdetect import detect

TO_FILTER = ["'s", '&lt', '&gt', "'ll", '</i', 'i>', '...', "'ve", "'re", 'anti-', 'self-',
             'semi-', 'ex-', 'non-', 'font', '<c>', '</c>', '--', 'color=', 'www', '.com', '.org', 'size=', '\\h']
EXT_SUBS = ['.srt', '.vtt']
EXT_VIDEOS = ['.mkv', '.mp4']

# set paths
VIDEOS_PATH = 'c:\\Users\\Artem\\YandexDisk\\video\\1'     # Use dual \\ in Windows. No trailing \\
WORK_PATH = 'c:\\Users\\Artem\\YandexDisk\\BU\\sub2learn'
TMP = WORK_PATH + '\\~sub2learn.srt'
SEEN_FILE = WORK_PATH + '\\seen_files.txt'
KNOWN_WORDS_FILE = WORK_PATH + '\\known_words.txt'
NEW_WORDS_FILE = WORK_PATH+'\\new_words.txt'

colorama.init(autoreset=True)
RED = colorama.Fore.RED
YELLOW = colorama.Fore.YELLOW
GREEN = colorama.Fore.GREEN

try:
    nlp = spacy.load('en_core_web_sm')
except OSError:
    sys.exit(f'{RED}Model not found. Install it with "python -m spacy download en_core_web_sm"')


def cleanup(words):
    words = [word.replace("’", "'") for word in words]
    words = [word.replace("—", "-") for word in words]
    words = [word.replace("&nbsp", ' ') for word in words]
    words = [word.replace(":", ' ') for word in words]
    for filter_item in TO_FILTER:
        words = [word.replace(filter_item, '') for word in words]

    words = [word for word in words if len(word) > 2]  # drop 1-2-letter words
    words = [word for word in words if word.count('-') < 2]  # drop words with two dashes (probably it is some tag)
    words = [word for word in words if word.count('.') < 2]  # drop words with two dots (probably it is some tag)
    words = [word for word in words if not bool(re.search('[\u0400-\uFFFFFF]', word))]  # drop far Unicode symbols

    # next filters are derived from practice
    words = [word.lstrip(' ;´–--\'‘&\'‘--') for word in words]
    words = [word.lstrip('-') for word in words]
    words = [word.rstrip('-') for word in words]
    words = [word.rstrip("'") for word in words]
    words = [word.strip(' …:•–="#$@*<>%"“”’’“,.!/^?/;()[]{}£₤€♪♫0123456789') for word in words]

    # change word to neutral form (lemmatize), e.g. ducks -> duck, changed -> change
    words = [token.lemma_ for token in nlp(' '.join(words))]
    # remove duplicates in list
    words = list(set(words))
    return words


def read_sub(fname):
    '''read subtitles file, split to words'''
    with open(fname, 'r', encoding="utf-8") as f:
        text = f.read()
        text = re.sub("<.*?>", " ", text)   # strip everything inside <tags>
        text = text.lower()
        words = text.split()
    return cleanup(words)


def main():
    try:
        with open(SEEN_FILE, 'r', encoding="utf-8") as f_seen_file:
            seen_files_list = [line.rstrip('\n') for line in f_seen_file]
    except FileNotFoundError:
        seen_files_list = []

    os.chdir(VIDEOS_PATH)
    print('Creating file list...', end='')
    files = glob.glob("**/*.*", recursive=True)
    print(f' {GREEN}{len(files)} file(s)')
    words_read = []
    processed_files = []
    toprocess_videos = []
    toprocess_subs = []

    to_skip = 0
    for f in files:
        extension = os.path.splitext(f)[1]
        name = os.path.basename(f)
        try:
            lang = detect(name)
        except Exception:
            lang = 'unknown'
        if name in seen_files_list:
            to_skip += 1
            continue
        if extension in EXT_VIDEOS and lang != 'ru':
            toprocess_videos.append(f)
        if extension in EXT_SUBS:
            toprocess_subs.append(f)

    # extract subtitles from video with ffmpeg, process resulting subtitles file
    for i, f in enumerate(toprocess_videos, 1):
        print(f'Video {i}/{len(toprocess_videos)}: {f}')
        subprocess.run(f"ffmpeg -i \"{f}\" -y -hide_banner -loglevel error " + TMP,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        try:
            words_read.extend(read_sub(TMP))
        except Exception:
            pass
        processed_files.append(os.path.basename(f))

    # process subtitles
    for i, f in enumerate(toprocess_subs, 1):
        print(f'Subtitle {i}/{len(toprocess_subs)}: {f}')
        words_read.extend(read_sub(f))
        processed_files.append(os.path.basename(f))

    words_read = list(set(words_read))
    words_read.sort()
    print(f'Words read: {GREEN}{len(words_read)}')

    try:
        with open(KNOWN_WORDS_FILE, 'r', encoding="utf-8") as f:
            known_words = [line.rstrip('\n') for line in f]
            print(f'Known words DB: {GREEN}{len(known_words)}')
    except FileNotFoundError:
        print(f'{YELLOW}Known words DB is empty, creating')
        open(KNOWN_WORDS_FILE, mode='a').close()
        known_words = []

    unknown_new_words = [x for x in words_read if not (x in known_words)]
    print(f'Unknown words in new files: {GREEN}{len(unknown_new_words)}')

    try:
        with open(NEW_WORDS_FILE, 'r', encoding="utf-8") as f:
            unknown_words_db = [line.rstrip('\n') for line in f]
            print(f'Unknown words in DB: {GREEN}{len(unknown_words_db)}')
    except FileNotFoundError:
        print(f'{YELLOW}Unknown words DB is empty. Will create later')
        unknown_words_db = []

    total_new_words = unknown_words_db + unknown_new_words
    total_new_words = list(set(total_new_words))
    total_new_words = cleanup(total_new_words)
    total_new_words = [item for item in total_new_words if item not in known_words]
    total_new_words.sort()
    print(f'Total unknown words: {GREEN}{len(total_new_words)}')

    with open(NEW_WORDS_FILE, 'w+', encoding="utf-8") as f:
        f.write('\n'.join(total_new_words))
        f.write('\n')

    with open(SEEN_FILE, 'a+', encoding="utf-8") as f:
        f.write('\n'.join(processed_files))
        f.write('\n')

    print(f'Skipped {to_skip} file(s)')
    print(f'Now review {GREEN}{os.path.basename(NEW_WORDS_FILE)} ', end='')
    print(f'and manually move words which you know to {GREEN}{os.path.basename(KNOWN_WORDS_FILE)}')


if __name__ == "__main__":
    main()
