"""Hand-crafted linguistic features for Step 3 (M1). No external NLP models needed."""
import re
import numpy as np
import pandas as pd

WORD = re.compile(r"[A-Za-z']+")
SENT = re.compile(r"[.!?]+(?:\s|$)")
CONNECTIVES = {
    "addition": ["also", "furthermore", "moreover", "additionally", "besides", "in addition"],
    "contrast": ["however", "but", "although", "though", "while", "whereas", "nevertheless", "on the other hand", "yet"],
    "cause": ["because", "since", "therefore", "thus", "consequently", "so that", "as a result", "due to"],
    "example": ["for example", "for instance", "such as", "like", "in fact"],
    "conclusion": ["in conclusion", "to conclude", "overall", "in summary", "finally", "to sum up"],
    "sequence": ["first", "second", "third", "next", "then", "lastly"],
}
HEDGES = ["maybe", "perhaps", "might", "could", "probably", "possibly", "may"]
FIRST_PERSON = ["i", "my", "me", "we", "our", "us"]
SECOND_PERSON = ["you", "your", "u"]


def _syllables(w):
    w = w.lower()
    n = len(re.findall(r"[aeiouy]+", w))
    if w.endswith("e") and n > 1:
        n -= 1
    return max(n, 1)


def _count(text_l, phrases):
    return sum(len(re.findall(r"\b" + re.escape(p) + r"\b", text_l)) for p in phrases)


def essay_features(text: str) -> dict:
    words = WORD.findall(text)
    n = max(len(words), 1)
    lw = [w.lower() for w in words]
    sents = [s for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s.strip()]
    ns = max(len(sents), 1)
    paras = [p for p in re.split(r"\n\s*\n|\n", text) if p.strip()]
    sent_lens = np.array([len(WORD.findall(s)) for s in sents] or [0])
    wlen = np.array([len(w) for w in words] or [0])
    syl = sum(_syllables(w) for w in words)
    text_l = text.lower()
    uniq = len(set(lw))
    f = {
        # length / volume
        "n_words": len(words), "n_chars": len(text), "n_sents": ns, "n_paras": len(paras),
        "log_words": np.log1p(len(words)),
        # sentence structure
        "avg_sent_len": sent_lens.mean(), "std_sent_len": sent_lens.std(),
        "max_sent_len": sent_lens.max(), "short_sent_ratio": np.mean(sent_lens < 6),
        "long_sent_ratio": np.mean(sent_lens > 25),
        "avg_para_len": len(words) / max(len(paras), 1),
        # lexical
        "avg_word_len": wlen.mean(), "long_word_ratio": np.mean(wlen >= 7),
        "n_unique": uniq, "ttr": uniq / n, "root_ttr": uniq / np.sqrt(n),
        "hapax_ratio": sum(1 for w in set(lw) if lw.count(w) == 1) / n if n < 2500 else np.nan,
        # readability
        "flesch": 206.835 - 1.015 * (n / ns) - 84.6 * (syl / n),
        "fk_grade": 0.39 * (n / ns) + 11.8 * (syl / n) - 15.59,
        "syl_per_word": syl / n,
        # punctuation
        "n_commas": text.count(","), "commas_per_sent": text.count(",") / ns,
        "n_questions": text.count("?"), "n_exclaim": text.count("!"),
        "n_quotes": text.count('"'), "n_semicolon_colon": text.count(";") + text.count(":"),
        "n_apostrophe": text.count("'"), "caps_ratio": sum(c.isupper() for c in text) / max(len(text), 1),
        # surface errors (proxies)
        "lowercase_i": len(re.findall(r"\bi\b", text)),
        "no_end_punct": float(not text.rstrip().endswith((".", "!", "?", '"'))),
        "repeated_word": len(re.findall(r"\b(\w+)\s+\1\b", text_l)),
        "double_space": text.count("  "),
        # voice
        "first_person": _count(text_l, FIRST_PERSON) / n, "second_person": _count(text_l, SECOND_PERSON) / n,
        "hedges": _count(text_l, HEDGES) / n,
    }
    for k, v in CONNECTIVES.items():
        f[f"conn_{k}"] = _count(text_l, v)
    f["conn_total"] = sum(f[f"conn_{k}"] for k in CONNECTIVES)
    f["conn_per_sent"] = f["conn_total"] / ns
    return f


def build_feature_frame(texts) -> pd.DataFrame:
    return pd.DataFrame([essay_features(t) for t in texts])
