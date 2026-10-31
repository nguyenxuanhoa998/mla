"""Step 2 (segment effectiveness) - improved pipeline, leave-one-prompt-out (LOPO) on the 8 independent prompts.

Why this file exists: the Week-9 Step-2 baseline (LR on TF-IDF + position) reached macro-F1 0.43 and
Ineffective F1 0.07. Group 6 (CLC02) reports macro-F1 0.52 (RF) / 0.58 (DeBERTa) on a random 80/20 essay split of all
15 prompts, so we copy their PROCEDURE (role + length + position + n-grams, class-imbalance handling, threshold tuning)
and re-run it under OUR protocol (LOPO, 8 independent prompts); their numbers are not reusable.

Ladder (each row adds one block, same algorithm HistGradientBoosting, same folds):
  S0 majority | S1 role+length+position | S2 +essay context (neighbour roles, share of essay)
  S3 +essay-level M1 linguistic features | S4 +TF-IDF text signal (stacked, out-of-fold) | each with/without tuned class weights.
Class weights w_k (multiply predicted probabilities before argmax) are tuned ONLY on inner out-of-fold predictions of the
7 training prompts, never on the held-out prompt.
"""
import os
os.environ.setdefault("OMP_NUM_THREADS", "2")
import time
import numpy as np, pandas as pd, scipy.sparse as sp
from joblib import Parallel, delayed
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score, precision_recall_fscore_support
from common import PROC, RES

LABELS = ["Adequate", "Effective", "Ineffective"]
SEG_STATS = ["rank_rel", "is_first", "is_last", "rel_pos", "log_len", "n_chars", "seg_len", "n_sent", "avg_wlen",
             "n_comma", "caps", "has_digit", "i_cnt", "you_cnt", "lower_start", "no_end"]
CONTEXT = ["n_in_essay", "len_share", "essay_words"]


def build_table():
    seg = pd.read_pickle(PROC / "segments.pkl")
    ess = pd.read_pickle(PROC / "essays.pkl")
    ind = ess[ess.task == "Independent"].reset_index(drop=True)
    X1 = pd.read_pickle(PROC / "features_independent.pkl").fillna(0)
    X1.insert(0, "essay_id_comp", ind.essay_id_comp.values)
    seg = seg[seg.task == "Independent"].merge(ind[["essay_id_comp", "full_text"]], on="essay_id_comp")
    seg = seg.sort_values(["essay_id_comp", "discourse_start"]).reset_index(drop=True)
    seg["role"] = seg.discourse_type
    g = seg.groupby("essay_id_comp")
    seg["rank"] = g.cumcount(); seg["n_all"] = g.discourse_start.transform("count")
    seg["prev_role"] = g.role.shift(1).fillna("START"); seg["next_role"] = g.role.shift(-1).fillna("END")
    seg["prev_role2"] = g.role.shift(2).fillna("START")
    seg = seg[(seg.role != "Unannotated") & seg.discourse_effectiveness.notna()].copy()
    g = seg.groupby("essay_id_comp")
    seg["n_in_essay"] = g.discourse_start.transform("count")
    seg["rank_rel"] = seg["rank"] / seg.n_all
    seg["is_first"] = (seg["rank"] == 0) * 1.0; seg["is_last"] = (seg["rank"] == seg.n_all - 1) * 1.0
    seg["rel_pos"] = seg.discourse_start / seg.full_text.str.len()
    seg["log_len"] = np.log1p(seg.seg_len)
    t = seg.discourse_text
    seg["n_chars"] = t.str.len()
    seg["essay_words"] = seg.full_text.str.split().str.len()
    seg["len_share"] = seg.seg_len / seg.essay_words
    seg["n_sent"] = t.str.count(r"[.!?]+") + 1
    seg["avg_wlen"] = seg.n_chars / seg.seg_len.clip(lower=1)
    seg["n_comma"] = t.str.count(",")
    seg["caps"] = t.str.count(r"[A-Z]") / seg.n_chars.clip(lower=1)
    seg["has_digit"] = t.str.contains(r"\d") * 1.0
    tl = t.str.lower()
    seg["i_cnt"] = tl.str.count(r"\bi\b") / seg.seg_len.clip(lower=1)
    seg["you_cnt"] = tl.str.count(r"\byou\b") / seg.seg_len.clip(lower=1)
    seg["lower_start"] = t.str.strip().str[:1].str.islower() * 1.0
    seg["no_end"] = (~t.str.strip().str[-1:].isin([".", "!", "?"])) * 1.0
    seg = seg.merge(X1.add_prefix("e_").rename(columns={"e_essay_id_comp": "essay_id_comp"}), on="essay_id_comp")
    return seg.reset_index(drop=True), [c for c in seg.columns if c.startswith("e_") and c != "essay_words"]


def dense_blocks(seg, ess_cols):
    roles = pd.get_dummies(seg.role).astype(float)
    nb = pd.concat([pd.get_dummies(seg.prev_role, prefix="prev"), pd.get_dummies(seg.next_role, prefix="next"),
                    pd.get_dummies(seg.prev_role2, prefix="prev2")], axis=1).astype(float)
    return {
        "S1 role+length+position": pd.concat([roles, seg[SEG_STATS]], axis=1),
        "S2 +essay context": pd.concat([roles, seg[SEG_STATS], seg[CONTEXT], nb], axis=1),
        "S3 +essay M1 features": pd.concat([roles, seg[SEG_STATS], seg[CONTEXT], nb, seg[ess_cols]], axis=1),
    }


def tfidf_lr_proba(text, y, tr, te):
    """Fit TF-IDF (word 1-2 + char 3-5) + LR on rows `tr`, return probabilities for rows `te` (columns = LABELS)."""
    w = TfidfVectorizer(ngram_range=(1, 2), min_df=5, max_features=40000, sublinear_tf=True)
    c = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=10, max_features=40000, sublinear_tf=True)
    Xtr = sp.hstack([w.fit_transform(text[tr]), c.fit_transform(text[tr])]).tocsr()
    Xte = sp.hstack([w.transform(text[te]), c.transform(text[te])]).tocsr()
    m = LogisticRegression(max_iter=200, C=1.0).fit(Xtr, y[tr])
    return m.predict_proba(Xte)


def hgb(seed=0):
    return HistGradientBoostingClassifier(max_iter=300, learning_rate=0.05, max_depth=6, l2_regularization=1.0, random_state=seed)


def tune_weights(P, y):
    """Grid-search class weights (Adequate fixed to 1) maximising macro-F1 on inner out-of-fold probabilities."""
    best, bw = -1, (1.0, 1.0, 1.0)
    for a in np.linspace(0.5, 5, 10):
        for b in np.linspace(0.5, 40, 40):
            s = f1_score(y, np.array(LABELS)[(P * np.array([1, a, b])).argmax(1)], average="macro", labels=LABELS)
            if s > best: best, bw = s, (1.0, a, b)
    return np.array(bw)


def outer_fold(p, idx, blocks, text, y, gp):
    t0 = time.time()
    te = gp == p; tr = ~te; tr_prompts = sorted(set(gp[tr]))
    # text signal: inner out-of-fold probabilities for training rows, full-train model for held-out rows
    lr_tr = np.zeros((len(idx), 3)); lr_te = tfidf_lr_proba(text, y, tr, te)
    for q in tr_prompts:
        iq = gp == q
        lr_tr[iq] = tfidf_lr_proba(text, y, tr & ~iq, iq)
    lr_all = lr_tr.copy(); lr_all[te] = lr_te
    lr_cols = pd.DataFrame(lr_all, columns=[f"lr_{l}" for l in LABELS], index=idx)
    blocks = dict(blocks); blocks["S4 +TF-IDF text signal"] = pd.concat([blocks["S3 +essay M1 features"], lr_cols], axis=1)
    out = {}
    for name, X in blocks.items():
        m = hgb().fit(X[tr], y[tr]); P_te = m.predict_proba(X[te])
        P_in = np.zeros((int(tr.sum()), 3)); Xtr, ytr, gtr = X[tr], y[tr], gp[tr]
        for q in tr_prompts:
            iq = gtr == q
            P_in[iq] = hgb().fit(Xtr[~iq], ytr[~iq]).predict_proba(Xtr[iq])
        out[name] = (P_te, tune_weights(P_in, ytr))
    out["LR TF-IDF only"] = (lr_te, tune_weights(lr_tr[tr], y[tr]))
    print(f"{p:40s} done in {time.time()-t0:.0f}s", flush=True)
    return p, out


def metrics(y, pred, gp):
    per = [f1_score(y[gp == p], pred[gp == p], average="macro", labels=LABELS, zero_division=0) for p in sorted(set(gp))]
    pr, rc, f1, _ = precision_recall_fscore_support(y, pred, labels=LABELS, zero_division=0)
    return {"macroF1_pooled": f1_score(y, pred, average="macro", labels=LABELS, zero_division=0),
            "macroF1_mean_prompts": np.mean(per), "SD_prompts": np.std(per, ddof=1), "worst_prompt": np.min(per),
            "accuracy": float(np.mean(pred == y)),
            "F1_Adequate": f1[0], "F1_Effective": f1[1], "F1_Ineffective": f1[2],
            "P_Ineffective": pr[2], "R_Ineffective": rc[2]}


if __name__ == "__main__":
    seg, ess_cols = build_table()
    y = seg.discourse_effectiveness.values; gp = seg.prompt_name.values
    text = seg.discourse_text.values
    print("segments:", len(seg), dict(zip(*np.unique(y, return_counts=True))))
    blocks = dense_blocks(seg, ess_cols)
    prompts = sorted(set(gp))
    res = dict(Parallel(n_jobs=4)(delayed(outer_fold)(p, seg.index, blocks, text, y, gp) for p in prompts))
    names = list(res[prompts[0]].keys())
    rows, oof_pred = [], {}
    rows.append({"model": "S0 majority (Adequate)", "weights": "-", **metrics(y, np.array(["Adequate"] * len(y), dtype=object), gp)})
    for n in names:
        for tuned in (False, True):
            pred = np.empty(len(y), dtype=object)
            for p in prompts:
                P, w = res[p][n]
                pred[gp == p] = np.array(LABELS)[(P * (w if tuned else 1)).argmax(1)]
            oof_pred[(n, tuned)] = pred
            rows.append({"model": n, "weights": "tuned on inner OOF" if tuned else "argmax", **metrics(y, pred, gp)})
    tab = pd.DataFrame(rows).round(3)
    tab.to_csv(RES / "step2_improved_summary.csv", index=False)
    print(tab.to_string(index=False))
    best = "S4 +TF-IDF text signal"
    pp = pd.DataFrame({p: {"n": int((gp == p).sum()),
                           "macroF1": f1_score(y[gp == p], oof_pred[(best, True)][gp == p], average="macro", labels=LABELS, zero_division=0),
                           "F1_Ineffective": f1_score(y[gp == p], oof_pred[(best, True)][gp == p], labels=["Ineffective"], average=None, zero_division=0)[0],
                           "n_Ineffective": int((y[gp == p] == "Ineffective").sum())} for p in prompts}).T.round(3)
    pp.to_csv(RES / "step2_improved_per_prompt.csv"); print(pp)
    pd.DataFrame({"w_Effective": [res[p][best][1][1] for p in prompts], "w_Ineffective": [res[p][best][1][2] for p in prompts]},
                 index=prompts).round(2).to_csv(RES / "step2_improved_weights.csv")
    np.savez_compressed(RES / "step2_improved_pred.npz", discourse_id=seg.discourse_id.values, prompt=gp, y=y,
                        pred=oof_pred[(best, True)], pred_argmax=oof_pred[(best, False)])
