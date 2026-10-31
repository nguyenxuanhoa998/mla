"""Week-9 requests from the lecturer.
(1) Delta QWK of structure inside five word-count groups (keeps length roughly fixed).
(2) QWK as a function of controlled corruption of gold role labels (boundaries kept), M2 re-run on the same LOPO folds.
Run after the notebook has produced results/nb_predictions.npz.
"""
import os
os.environ.setdefault("OMP_NUM_THREADS", "1")
import numpy as np, pandas as pd
from joblib import Parallel, delayed
from sklearn.ensemble import GradientBoostingRegressor
from common import PROC, RES, FIGS, qwk, to_level
from structure import structure_features, ROLES

ess = pd.read_pickle(PROC / "essays.pkl"); ess = ess[ess.task == "Independent"].reset_index(drop=True)
X1 = pd.read_pickle(PROC / "features_independent.pkl").fillna(0)
y = ess.holistic_essay_score.values; groups = ess.prompt_name.values; prompts = sorted(set(groups))
z = np.load(RES / "nb_predictions.npz", allow_pickle=True)
assert (z["essay_id"] == ess.essay_id_comp.values).all() and (z["y"] == y).all()
P = {k.split("__")[1].strip(): z[k] for k in z.files if k.startswith("GB__")}
LV = {k: to_level(v) for k, v in P.items()}
rng = np.random.default_rng(0)

# ---------------------------------------------------------------- (1) Delta by word-count quintile
q = pd.qcut(X1.n_words, 5, labels=False)
edges = pd.qcut(X1.n_words, 5).cat.categories
comps = [("M2 - M1", "M2 (gold)", "M1"), ("M3 - M1", "M3 (pred)", "M1"), ("M1+boundary - M1", "M1 +B(boundary only)", "M1"),
         ("M2 - M1+boundary", "M2 (gold)", "M1 +B(boundary only)")]
rows = []
for b in range(5):
    m = (q == b).values
    for lab, A, B in comps:
        yy, a, c = y[m], LV[A][m], LV[B][m]
        d = qwk(yy, a) - qwk(yy, c)
        idx = rng.integers(0, m.sum(), size=(500, m.sum()))
        bs = np.array([qwk(yy[i], a[i]) - qwk(yy[i], c[i]) for i in idx])
        rows.append({"group": f"Q{b+1} {edges[b]}", "n": int(m.sum()), "comparison": lab, "QWK_A": qwk(yy, a), "QWK_B": qwk(yy, c),
                     "dQWK": d, "ci_lo": np.percentile(bs, 2.5), "ci_hi": np.percentile(bs, 97.5),
                     "dMAE": np.abs(c - yy).mean() - np.abs(a - yy).mean(), "mean_score": yy.mean()})
bins = pd.DataFrame(rows).round(4); bins.to_csv(RES / "w10_delta_by_length.csv", index=False)
print(bins.to_string(index=False))

# ---------------------------------------------------------------- (2) corruption curve
seg = pd.read_pickle(PROC / "segments.pkl")
seg = seg[seg.task == "Independent"].merge(ess[["essay_id_comp"]], on="essay_id_comp").reset_index(drop=True)
seg["role"] = seg.discourse_type.replace({"Unannotated": "none"}); seg["rank_rel"] = 0.0
ann = (seg.role != "none").values
GB = dict(n_estimators=300, max_depth=3, learning_rate=0.05, subsample=0.8)


def corrupt(role, rate, seed):
    r = np.random.default_rng(seed); out = role.copy()
    hit = ann & (r.random(len(out)) < rate)
    for i in np.where(hit)[0]:                                    # swap to a different annotated role, uniform
        out[i] = r.choice([x for x in ROLES if x != out[i]])
    return out


def run(rate, cseed, p):
    roles = corrupt(seg.role.values, rate, 1000 * cseed + int(rate * 100)) if rate > 0 else seg.role.values
    F = structure_features(seg, roles, ess.essay_id_comp)
    X = pd.concat([X1, F], axis=1); te = groups == p
    m = GradientBoostingRegressor(**GB, random_state=0).fit(X[~te], y[~te])
    return rate, cseed, p, m.predict(X[te])


RATES = [0, 0.1, 0.2, 0.4, 0.6, 0.8]; CS = [1, 2, 3]
jobs = [(r, c, p) for r in RATES for c in (CS if r > 0 else [0]) for p in prompts]
res = Parallel(n_jobs=8)(delayed(run)(*j) for j in jobs)
pred = {}
for r, c, p, v in res: pred.setdefault((r, c), np.full(len(y), np.nan))[groups == p] = v
mean_q = lambda lv: np.mean([qwk(y[groups == p], lv[groups == p]) for p in prompts])
base = {k: mean_q(LV[k]) for k in ["M1", "M1 +B(boundary only)", "M2 (gold)"]}
crow = []
for (r, c), v in sorted(pred.items()):
    lv = to_level(v)
    d_vs_b = np.array([qwk(y[groups == p], lv[groups == p]) - qwk(y[groups == p], LV["M1 +B(boundary only)"][groups == p]) for p in prompts])
    crow.append({"corruption": r, "draw": c, "meanQWK": mean_q(lv), "d_vs_M1": mean_q(lv) - base["M1"],
                 "d_vs_M1+boundary": d_vs_b.mean(), "prompts_above_M1+boundary": int((d_vs_b > 0).sum())})
curve = pd.DataFrame(crow).round(4); curve.to_csv(RES / "w10_corruption_curve.csv", index=False)
summ = curve.groupby("corruption").agg(meanQWK=("meanQWK", "mean"), sd_draws=("meanQWK", "std"),
                                       d_vs_M1=("d_vs_M1", "mean"), d_vs_boundary=("d_vs_M1+boundary", "mean")).round(4)
summ.to_csv(RES / "w10_corruption_summary.csv")
print(base); print(summ)

import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
fig, ax = plt.subplots(1, 2, figsize=(12, 4))
ax[0].errorbar(summ.index * 100, summ.meanQWK, yerr=summ.sd_draws.fillna(0), marker="o", c="#3b6ea5", label="M2 with corrupted roles")
for k, c in [("M1", "#999"), ("M1 +B(boundary only)", "#d98c00")]: ax[0].axhline(base[k], ls="--", c=c, label=k)
ax[0].set_xlabel("% role labels corrupted (boundaries kept)"); ax[0].set_ylabel("mean QWK / prompt"); ax[0].legend(fontsize=8)
ax[0].set_title("Role-label corruption curve (GB, LOPO)")
g = bins[bins.comparison.isin(["M2 - M1", "M1+boundary - M1"])]
for lab, sub in g.groupby("comparison"): ax[1].plot(range(1, 6), sub.dQWK.values, marker="o", label=lab)
ax[1].axhline(0, c="k", lw=.6); ax[1].set_xlabel("word-count quintile (short -> long)"); ax[1].set_ylabel("dQWK within group"); ax[1].legend(fontsize=8)
ax[1].set_title("Structure gain inside length groups")
plt.tight_layout(); plt.savefig(FIGS / "w10_length_groups_and_corruption.png", dpi=150)
