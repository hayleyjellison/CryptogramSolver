def load_words():
    with open("/usr/share/dict/words") as word_file:
        valid_words = set(word_file.read().split())

    return valid_words


def load_words_of_certain_length(word_len: int):
    with open("/usr/share/dict/words") as word_file:
        all_words = set(word_file.read().split())
        valid_words = {word for word in all_words if len(word) == word_len}

    return valid_words
