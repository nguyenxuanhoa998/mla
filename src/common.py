"""Shared paths, data loading and metrics for the AFP project (Group 04)."""
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.metrics import cohen_kappa_score, mean_absolute_error

ROOT = Path(__file__).resolve().parents[1]
RAW_TRAIN = ROOT.parent / "persuade_corpus_2.0_train.csv"
PROC = ROOT / "data" / "processed"
RES = ROOT / "results"
FIGS = ROOT / "figs"
SEED = 42


def qwk(y_true, y_pred):
    return cohen_kappa_score(y_true, y_pred, weights="quadratic", labels=[1, 2, 3, 4, 5, 6])


def to_level(x):
    """Round a continuous prediction to the 1-6 scale."""
    return np.clip(np.rint(x), 1, 6).astype(int)


def regression_report(y_true, y_cont):
    y_pred = to_level(y_cont)
    return {"QWK": qwk(y_true, y_pred), "MAE": mean_absolute_error(y_true, y_pred),
            "adj_acc": float(np.mean(np.abs(y_true - y_pred) <= 1))}
