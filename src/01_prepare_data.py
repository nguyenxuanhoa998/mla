"""Build essay-level and segment-level tables from the PERSUADE 2.0 train file."""
import pandas as pd
from common import RAW_TRAIN, PROC

COLS_SEG = ["essay_id_comp", "prompt_name", "task", "discourse_id", "discourse_start",
            "discourse_end", "discourse_text", "discourse_type", "discourse_effectiveness"]
COLS_ESSAY = ["essay_id_comp", "full_text", "holistic_essay_score", "prompt_name", "task",
              "ell_status", "grade_level", "gender", "essay_word_count"]

raw = pd.read_csv(RAW_TRAIN)
essays = raw[COLS_ESSAY].drop_duplicates("essay_id_comp").reset_index(drop=True)
essays["ell"] = essays["ell_status"].map({"Yes": 1, "No": 0})  # fairness checks only
segs = raw[COLS_SEG].dropna(subset=["discourse_text"]).reset_index(drop=True)
segs["seg_len"] = segs["discourse_text"].str.split().str.len()

PROC.mkdir(parents=True, exist_ok=True)
essays.to_pickle(PROC / "essays.pkl")
segs.to_pickle(PROC / "segments.pkl")
print("essays:", len(essays), "| segments:", len(segs))
print(essays.groupby("task").size().to_string())
print(segs.discourse_type.value_counts().to_string())
print(segs.discourse_effectiveness.value_counts(normalize=True).round(3).to_string())
