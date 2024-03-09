import collections

import more_itertools


def get_training_data(include_end_markers):
    with open("/tmp/##learnpython.log") as file:
        for line in file:
            try:
                timestamp, sender, message = line.split('\t')
            except ValueError:
                continue

            if sender == "*":
                continue

            for word in message.split():
                yield word
            if include_end_markers:
                yield None


HOW_MANY_WORDS_BACK = 5


def train(allow_none) -> dict[tuple[str | None, ...], str | None]:
    counts_by_key = collections.defaultdict(lambda: collections.defaultdict(int))
    for n in range(1, HOW_MANY_WORDS_BACK + 2):
        for words in more_itertools.windowed(get_training_data(allow_none), n):
            key = words[:-1]
            prediction = words[-1]
            counts_by_key[key][prediction] += 1

    return {key: max(counts, key=counts.get) for key, counts in counts_by_key.items()}


DATA_WITHOUT_NONE = train(False)
DATA_WITH_NONE = train(True)


def predict_next_word(prev_words, can_end_here):
    prev_words = list(prev_words[-10:])
    while None in prev_words:
        prev_words.remove(None)

    if can_end_here:
        data = DATA_WITH_NONE
    else:
        data = DATA_WITHOUT_NONE
        assert () in data

    for n in range(HOW_MANY_WORDS_BACK, -1, -1):
        key = tuple(prev_words[len(prev_words) - n:])
        if key in data:
            if not can_end_here:
                assert data[key] is not None
            return data[key]

    return None


def predict_next_message(message):
    prev_words = message.split() + [None]

    start_len = len(prev_words)
    while len(prev_words) < start_len + 10 and prev_words.count(None) < 2:
        can_end_here = len(prev_words) >= start_len + 2
        prev_words.append(predict_next_word(prev_words, can_end_here))
    return " ".join(w for w in prev_words[start_len:] if w is not None).capitalize()


if __name__ == "__main__":
    while True:
        print(predict_next_message(input("> ")))
