"""Measure retrieval quality on questions with well-known answer verses.

Usage (from the project root):
    python scripts/eval_retrieval.py            # compare semantic vs hybrid
    python scripts/eval_retrieval.py --verbose  # also list the misses

A question counts as a hit when any expected verse appears among the top-k
unique verses. MRR rewards ranking the first expected verse higher.
"""

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from rag import retrieve  # noqa: E402


# (question, expected verses as "chapter.verse")
EVAL_SET = [
    ("How can I control anger?", ["2.62", "2.63", "16.21", "5.23", "5.26"]),
    ("What happens to the soul when the body dies?", ["2.13", "2.20", "2.22"]),
    ("Should I work without caring about the results?", ["2.47", "2.48", "3.19"]),
    ("What are the qualities of a sthita-prajna, a man of steady wisdom?", ["2.54", "2.55", "2.56"]),
    ("Abandon all varieties of religion and just surrender unto Me", ["18.66"]),
    ("How should one sit when practising meditation?", ["6.11", "6.12", "6.13"]),
    ("Why does Krishna descend whenever religion declines?", ["4.7", "4.8"]),
    ("What impels a person to sinful acts even unwillingly?", ["3.36", "3.37"]),
    ("What are the three modes of material nature?", ["14.5"]),
    ("Which qualities make a devotee very dear to Krishna?", ["12.13", "12.14", "12.15", "12.16", "12.17", "12.18", "12.19", "12.20"]),
    ("What kind of food is dear to those in the mode of goodness?", ["17.8"]),
    ("What is the brahma-bhuta stage?", ["18.54"]),
    ("Why did Arjuna cast aside his bow and arrows?", ["1.46", "2.9"]),
    ("Who sees inaction in action and action in inaction?", ["4.18"]),
    ("Krishna is the source of all spiritual and material worlds", ["10.8"]),
    ("Knowing Me as the enjoyer of all sacrifices and friend of all beings, one attains peace", ["5.29"]),
    ("What did Dhritarashtra ask Sanjaya at Kurukshetra?", ["1.1"]),
    ("Offer Me a leaf, a flower, fruit or water with devotion", ["9.26"]),
    ("man-mana bhava mad-bhakto", ["9.34", "18.65"]),
    ("What is the banyan tree with its roots upward?", ["15.1"]),
    ("What happens if one remembers Krishna at the time of death?", ["8.5", "8.6"]),
    ("Which four kinds of pious men render devotional service?", ["7.16"]),
    ("What are the transcendental qualities of the divine nature?", ["16.1", "16.2", "16.3"]),
    ("Why is Krishna not manifest to everyone, covered by yoga-maya?", ["7.25"]),
    ("The wise see with equal vision a brahmana, a cow, an elephant, a dog and a dog-eater", ["5.18"]),
    ("Is the mind a friend or an enemy?", ["6.5", "6.6"]),
    ("The mahatmas are under the protection of the divine nature", ["9.13"]),
    # Everyday phrasing that shares few words with the translation.
    ("How do I stay calm through both happiness and distress?", ["2.14", "2.15", "2.38", "2.56"]),
    ("Should I quit my job and become a monk?", ["3.4", "3.8", "5.2", "18.47", "18.48"]),
    ("How do I stop overthinking and calm my restless mind?", ["6.26", "6.34", "6.35"]),
    ("What should I eat?", ["3.13", "9.26", "17.8", "17.9", "17.10"]),
    ("How can I become free from fear?", ["4.10", "6.14", "10.4", "16.1", "18.30", "18.66"]),
    ("How do I cope with grief after someone I love has died?", ["2.11", "2.13", "2.25", "2.26", "2.27", "2.28"]),
]


def _verse_numbers(verse):
    """'21-22' -> {21, 22}; '5' -> {5}."""
    numbers = [int(part) for part in re.findall(r"\d+", str(verse))]
    if len(numbers) == 2 and numbers[0] < numbers[1]:
        return set(range(numbers[0], numbers[1] + 1))
    return set(numbers)


def _matches(result, expected):
    document = result.get("document") or {}
    chapter = document.get("chapter", result.get("chapter"))
    verses = _verse_numbers(document.get("verse", result.get("verse")))
    for item in expected:
        exp_chapter, exp_verse = map(int, item.split("."))
        if chapter is not None and int(chapter) == exp_chapter and exp_verse in verses:
            return True
    return False


def evaluate(search, k):
    hits, reciprocal_ranks, misses = 0, [], []
    for question, expected in EVAL_SET:
        results = search(question, k)
        rank = next((i for i, r in enumerate(results, 1) if _matches(r, expected)), None)
        if rank:
            hits += 1
            reciprocal_ranks.append(1 / rank)
        else:
            reciprocal_ranks.append(0.0)
            misses.append((question, expected, [r.get("reference") for r in results[:3]]))
    total = len(EVAL_SET)
    return hits / total, sum(reciprocal_ranks) / total, misses


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("-k", type=int, default=8)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    strategies = {
        "semantic": lambda q, k: retrieve.retrieve_semantic(q, k=k),
        "keyword (BM25)": lambda q, k: retrieve.retrieve_keyword(q, k=k),
        "hybrid": lambda q, k: retrieve.retrieve_hybrid(q, k=k),
    }
    print(f"\n{len(EVAL_SET)} questions, top-{args.k} unique verses\n")
    print(f"{'strategy':<16}{'recall@k':>10}{'MRR':>8}")
    for name, search in strategies.items():
        recall, mrr, misses = evaluate(search, args.k)
        print(f"{name:<16}{recall:>10.1%}{mrr:>8.3f}")
        if args.verbose:
            for question, expected, top in misses:
                print(f"    miss: {question!r} expected {expected}, got {top}")


if __name__ == "__main__":
    main()
