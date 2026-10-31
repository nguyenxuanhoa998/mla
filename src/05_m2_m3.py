"""RQ1/RQ2: M2 = M1 + gold argument structure, M3 = M1 + predicted structure (nested, leave-one-prompt-out).

Predicted structure for every essay never uses a Step-1 model trained on the essay's own prompt, and
for a Step-3 held-out prompt p it never uses labels from p:
  - test essays (prompt p): Step-1 model trained on the 7 other prompts
  - train essays (prompt q != p): Step-1 model trained on the 6 prompts other than p and q
Segment boundaries are the gold ones; only the role label is predicted.
"""
import json
import numpy as np, pandas as pd, scipy.sparse as sp
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.svm import LinearSVC
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.metrics import f1_score
from common import PROC, RES, SEED, qwk, to_level, regression_report
from structure import structure_features

ess = pd.read_pickle(PROC / "essays.pkl")
ess = ess[ess.task == "Independent"].reset_index(drop=True)
X1 = pd.read_pickle(PROC / "features_independent.pkl")
y = ess.holistic_essay_score.values
groups = ess.prompt_name.values
prompts = sorted(set(groups))

seg = pd.read_pickle(PROC / "segments.pkl")
seg = seg[seg.task == "Independent"].merge(ess[["essay_id_comp", "full_text"]], on="essay_id_comp").reset_index(drop=True)
seg["role"] = seg.discourse_type.replace({"Unannotated": "none"})
seg["rel_pos"] = seg.discourse_start / seg.full_text.str.len()
seg["rank_in_essay"] = seg.groupby("essay_id_comp").discourse_start.rank(method="first")
seg["n_in_essay"] = seg.groupby("essay_id_comp").discourse_start.transform("count")
seg["rank_rel"] = seg.rank_in_essay / seg.n_in_essay
seg["is_first"] = (seg.rank_in_essay == 1).astype(float)
seg["is_last"] = (seg.rank_in_essay == seg.n_in_essay).astype(float)
seg["log_len"] = np.log1p(seg.seg_len)
P = seg[["rel_pos", "rank_rel", "is_first", "is_last", "log_len"]].values
P = (P - P.mean(0)) / (P.std(0) + 1e-9)
H = HashingVectorizer(n_features=2 ** 18, ngram_range=(1, 2), alternate_sign=False, norm="l2").transform(seg.discourse_text)
XS = sp.hstack([H, sp.csr_matrix(P)]).tocsr()
sg = seg.prompt_name.values
role = seg.role.values


def fit_roles(train_mask):
    return LinearSVC(C=0.5, class_weight="balanced").fit(XS[train_mask], role[train_mask])


# --- nested out-of-fold role predictions: pred[p] is a full-length vector valid for Step-3 held-out prompt p
pred_roles = {}
inner_cache = {}
for p in prompts:
    pr = np.empty(len(seg), dtype=object)
    m = fit_roles(sg != p)
    te = sg == p
    pr[te] = m.predict(XS[te])
    for q in prompts:
        if q == p:
            continue
        key = frozenset((p, q))
        if key not in inner_cache:
            inner_cache[key] = fit_roles((sg != p) & (sg != q))
        tq = sg == q
        pr[tq] = inner_cache[key].predict(XS[tq])
    pred_roles[p] = pr
    print("roles done", p, flush=True)

# Step-1 quality of the held-out-prompt predictions
role_pred_test = np.empty(len(seg), dtype=object)
for p in prompts:
    role_pred_test[sg == p] = pred_roles[p][sg == p]
step1_f1 = f1_score(role, role_pred_test, average="macro")
print("Step-1 macro-F1 (held-out prompt):", round(step1_f1, 3))

F_gold = structure_features(seg, role, ess.essay_id_comp)
F_pred = {p: structure_features(seg, pred_roles[p], ess.essay_id_comp) for p in prompts}

# --- Step 3 models: same algorithm (Gradient Boosting) and RF, only the inputs differ
def gb():
    return GradientBoostingRegressor(n_estimators=300, max_depth=3, learning_rate=0.05, subsample=0.8, random_state=SEED)


def rf():
    return RandomForestRegressor(300, min_samples_leaf=3, n_jobs=-1, random_state=SEED)


algos = {"GB": gb, "RF": rf}
oof = {(a, v): np.zeros(len(y)) for a in algos for v in ["M1", "M2", "M3"]}
for p in prompts:
    te = groups == p
    inputs = {"M1": (X1, X1),
              "M2": (pd.concat([X1, F_gold], axis=1), pd.concat([X1, F_gold], axis=1)),
              "M3": (pd.concat([X1, F_pred[p]], axis=1), pd.concat([X1, F_pred[p]], axis=1))}
    for a, mk in algos.items():
        for v, (Xtr_all, Xte_all) in inputs.items():
            m = mk().fit(Xtr_all[~te], y[~te])
            oof[(a, v)][te] = m.predict(Xte_all[te])
    print("step3 done", p, flush=True)

rows, per_prompt = [], []
for (a, v), pred in oof.items():
    r = regression_report(y, pred)
    qs = [regression_report(y[groups == p], pred[groups == p])["QWK"] for p in prompts]
    rows.append({"algo": a, "model": v, "pooled_QWK": r["QWK"], "pooled_MAE": r["MAE"],
                 "mean_QWK_prompts": np.mean(qs), "std_QWK": np.std(qs), "worst_QWK": np.min(qs)})
    for p, q in zip(prompts, qs):
        per_prompt.append({"algo": a, "model": v, "prompt": p, "QWK": q})
res = pd.DataFrame(rows).round(3)
res.to_csv(RES / "rq12_summary.csv", index=False)
pd.DataFrame(per_prompt).to_csv(RES / "rq12_per_prompt.csv", index=False)
print(res.to_string(index=False))

# --- paired comparison: essay-level bootstrap of the pooled-QWK difference (predictions fixed)
rng = np.random.default_rng(SEED)
lv = {k: to_level(v) for k, v in oof.items()}
comps = [("M2 - M1  (RQ1: gain from gold structure)", "M2", "M1"),
         ("M3 - M1  (RQ1: gain from predicted structure)", "M3", "M1"),
         ("M2 - M3  (RQ2: loss from using predicted structure)", "M2", "M3")]
boot_rows = []
idx = rng.integers(0, len(y), size=(1000, len(y)))
for a in algos:
    for label, v1, v2 in comps:
        d = np.array([qwk(y[i], lv[(a, v1)][i]) - qwk(y[i], lv[(a, v2)][i]) for i in idx])
        point = qwk(y, lv[(a, v1)]) - qwk(y, lv[(a, v2)])
        pdiff = []
        for p in prompts:
            m = groups == p
            pdiff.append(qwk(y[m], lv[(a, v1)][m]) - qwk(y[m], lv[(a, v2)][m]))
        boot_rows.append({"algo": a, "comparison": label, "dQWK": point, "ci_lo": np.percentile(d, 2.5),
                          "ci_hi": np.percentile(d, 97.5), "prompts_higher": int(np.sum(np.array(pdiff) > 0))})
boot = pd.DataFrame(boot_rows).round(3)
boot.to_csv(RES / "rq12_paired.csv", index=False)
print(boot.to_string(index=False))

# --- feature importance of structure features in GB M2 (trained on all)
m = gb().fit(pd.concat([X1, F_gold], axis=1), y)
imp = pd.Series(m.feature_importances_, index=list(X1.columns) + list(F_gold.columns)).sort_values(ascending=False)
imp.head(15).to_csv(RES / "rq12_m2_importance.csv", header=["importance"])
print(imp.head(10))
json.dump({"step1_macroF1_heldout": step1_f1}, open(RES / "rq12_extra.json", "w"))
