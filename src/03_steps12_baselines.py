"""Steps 1-2 baselines (segment role, segment effectiveness), leave-one-prompt-out."""
import numpy as np, pandas as pd, scipy.sparse as sp
from sklearn.dummy import DummyClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score, recall_score
from common import PROC, RES, SEED

seg = pd.read_pickle(PROC / "segments.pkl")
ess = pd.read_pickle(PROC / "essays.pkl")[["essay_id_comp", "full_text"]]
seg = seg[seg.task == "Independent"].merge(ess, on="essay_id_comp")
seg["rel_pos"] = seg.discourse_start / seg.full_text.str.len()
seg["rank_in_essay"] = seg.groupby("essay_id_comp").discourse_start.rank(method="first")
seg["n_in_essay"] = seg.groupby("essay_id_comp").discourse_start.transform("count")
seg["rank_rel"] = seg.rank_in_essay / seg.n_in_essay
seg["is_first"] = (seg.rank_in_essay == 1).astype(float)
seg["is_last"] = (seg.rank_in_essay == seg.n_in_essay).astype(float)
seg["log_len"] = np.log1p(seg.seg_len)
POS = ["rel_pos", "rank_rel", "is_first", "is_last", "log_len"]
seg["role"] = seg.discourse_type.replace({"Unannotated": "none"})
print("segments (independent):", len(seg))

def run(task, y_col, df):
    y = df[y_col].values; g = df.prompt_name.values
    res = {k: [] for k in ["majority", "LR position+length", "LR TF-IDF + position"]}
    oof = {k: np.empty(len(df), dtype=object) for k in res}
    for p in sorted(set(g)):
        te = g == p; tr = ~te
        Xp = df[POS].values
        mu, sd = Xp[tr].mean(0), Xp[tr].std(0) + 1e-9
        Xp = (Xp - mu) / sd
        m = DummyClassifier(strategy="most_frequent").fit(Xp[tr], y[tr]); oof["majority"][te] = m.predict(Xp[te])
        m = LogisticRegression(max_iter=300, class_weight="balanced").fit(Xp[tr], y[tr]); oof["LR position+length"][te] = m.predict(Xp[te])
        tf = TfidfVectorizer(ngram_range=(1, 2), min_df=5, max_features=30000, sublinear_tf=True)
        Xt = tf.fit_transform(df.discourse_text.values[tr])
        Xtr = sp.hstack([Xt, sp.csr_matrix(Xp[tr])]).tocsr()
        Xte = sp.hstack([tf.transform(df.discourse_text.values[te]), sp.csr_matrix(Xp[te])]).tocsr()
        m = LogisticRegression(max_iter=300, class_weight="balanced", C=1.0).fit(Xtr, y[tr]); oof["LR TF-IDF + position"][te] = m.predict(Xte)
        print(task, "done", p, flush=True)
    labels = sorted(set(y)); rows = []
    for k, pred in oof.items():
        per_p = [f1_score(y[g == p], pred[g == p], average="macro", labels=labels, zero_division=0) for p in sorted(set(g))]
        row = {"task": task, "model": k, "macroF1_pooled": f1_score(y, pred, average="macro", labels=labels, zero_division=0),
               "macroF1_mean_prompts": np.mean(per_p), "std": np.std(per_p), "accuracy": float(np.mean(pred == y))}
        if task == "Step2":
            row["recall_Ineffective"] = recall_score(y, pred, labels=["Ineffective"], average=None, zero_division=0)[0]
        else:
            row["recall_Rebuttal"] = recall_score(y, pred, labels=["Rebuttal"], average=None, zero_division=0)[0]
        rows.append(row)
    per_class = pd.DataFrame({"class": labels, "n": [int((y == l).sum()) for l in labels],
        "recall_LR_tfidf": recall_score(y, oof["LR TF-IDF + position"], labels=labels, average=None, zero_division=0),
        "f1_LR_tfidf": f1_score(y, oof["LR TF-IDF + position"], labels=labels, average=None, zero_division=0)})
    per_class.round(3).to_csv(RES / f"{task}_per_class.csv", index=False)
    return pd.DataFrame(rows), per_class

r1, c1 = run("Step1", "role", seg)
r2, c2 = run("Step2", "discourse_effectiveness", seg.dropna(subset=["discourse_effectiveness"]).reset_index(drop=True))
out = pd.concat([r1, r2]).round(3); out.to_csv(RES / "step12_summary.csv", index=False)
print(out.to_string(index=False)); print(c1.round(3)); print(c2.round(3))
