# sub2learn
Convert subtitles to words for learning. Supports .vtt and .srt, also can get subtitles from .mkv and .mp4 videos
(using ffmpeg) and then process text.

TODO use sqlite. Words: word, translation, sourcefile, bool known, timestamp; seen_files: name, timestamp
TODO new words with status ToProcess, toLearn, ...
TODO use counter?
TODO add translation for unknown words (use Google Translate API or analogue)
TODO add support for youtube links processing
TODO process videos in parallel
TODO add e-book support: txt, fb2, epub, fb2.zip


Загрузить known_words в sqlite
переделать логику под sql
выкидывать слова длиной 1-2
