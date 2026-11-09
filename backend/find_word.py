import argparse
import json
import re
from collections import defaultdict

import enchant
import requests
from wordfreq import zipf_frequency

from .load_words import load_words_of_certain_length


def find_possible_matches(sample_word: str, known_letters: str | None) -> list[str]:
    n_letters = len(sample_word)
    known_letter_mapping = {}
    if known_letters:
        known_letter_combos = known_letters.strip().split(",")
        for letter_combo in known_letter_combos:
            letter_combo = letter_combo.split("=")
            known_letter_mapping[letter_combo[0]] = letter_combo[1]
    possible_words = load_words_of_certain_length(n_letters)
    d_us_e = enchant.Dict("en_US")
    d_gb_e = enchant.Dict("en_GB")

    n_unique_letters = len(set(sample_word))
    possible_words = [
        word for word in possible_words if len(set(word)) == n_unique_letters
    ]

    letter_frequency = defaultdict(dict)
    """
    {
        letter: {
            frequency: x,
            indeces: []
        }
    }
    """
    for letter in sample_word:
        letter_frequency[letter]["frequency"] = (
            letter_frequency.get(letter, {}).get("frequency", 0) + 1
        )
        letter_frequency[letter]["indeces"] = [
            l.start() for l in re.finditer(letter, sample_word)
        ]

    updated_possible_words = set()
    repeated_letter_indeces = [
        letter_dict["indeces"]
        for letter_dict in letter_frequency.values()
        if len(letter_dict["indeces"]) > 1
    ]
    for word in possible_words:
        invalid = False
        if not ((d_us_e.check(word) or d_gb_e.check(word)) and word[0].islower()):
            continue

        for letter_index, letter in enumerate(word):
            if letter == sample_word[letter_index].lower():
                invalid = True
                break

        for code_letter, matched_letter in known_letter_mapping.items():
            if invalid:
                break

            invalid = (
                code_letter in sample_word and matched_letter.lower() not in word
            ) or (code_letter not in sample_word and matched_letter.lower() in word)

            if invalid:
                break

            if code_letter in letter_frequency:
                code_letter_indeces = letter_frequency[code_letter]["indeces"]
                for index in code_letter_indeces:
                    if word[index] != matched_letter.lower():
                        invalid = True
                        break

        if invalid:
            continue

        for repeated_indeces in repeated_letter_indeces:
            num_indeces = len(repeated_indeces)
            i = 0
            while i < num_indeces - 1:
                if word[repeated_indeces[i]] != word[repeated_indeces[i + 1]]:
                    invalid = True
                    break
                i += 1
            if invalid:
                break
        if not invalid:
            updated_possible_words.add(word)

    ranked_possible_words = rank_possible_matches(updated_possible_words)
    return ranked_possible_words


def rank_possible_matches(possible_matches: list[str]) -> list[str]:
    sorted_matches = sorted(
        possible_matches,
        key=lambda word: zipf_frequency(word.lower(), "en"),
        reverse=True,
    )
    return sorted_matches


def possible_letter_frequency(
    sample_word: str, known_letters: str | None
) -> dict[int, dict[str, int]]:
    possible_words = find_possible_matches(sample_word, known_letters)
    possible_letter_freq = defaultdict(dict)
    for word in possible_words:
        for letter_index, letter in enumerate(list(word)):
            possible_letter_freq[letter_index][letter] = (
                possible_letter_freq.get(letter_index, {}).get(letter, 0) + 1
            )

    for letter_index, letter_freq_dict in possible_letter_freq.items():
        possible_letter_freq[letter_index] = dict(
            sorted(letter_freq_dict.items(), key=lambda item: item[1], reverse=True)
        )

    return possible_letter_freq


def check_word_def(word):
    dict_url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
    response = requests.get(dict_url)

    json_data = json.loads(response.content.decode("utf-8"))
    return json_data


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process numbers and export results.")
    parser.add_argument("sample_word", type=str, help="word needing decoding")
    parser.add_argument(
        "-known_letters", type=str, default=None, help="known letters from sample word"
    )
    args = parser.parse_args()

    sample_word = args.sample_word
    known_letters = args.known_letters
    find_possible_matches(sample_word, known_letters)
    # check_word_def("Telegu")
