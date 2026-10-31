"""Step 3 baselines M0 (word count) and M1 (linguistic features), leave-one-prompt-out."""
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from common import PROC, RES, FIGS, SEED, regression_report, to_level
from features import build_feature_frame

ess = pd.read_pickle(PROC / "essays.pkl")
ess = ess[ess.task == "Independent"].reset_index(drop=True)   # source-based prompts excluded
print("independent essays:", len(ess))
print("r(word count, score) =", round(ess.essay_word_count.corr(ess.holistic_essay_score), 3))

X1 = build_feature_frame(ess.full_text).fillna(0)
X1.to_pickle(PROC / "features_independent.pkl")
y = ess.holistic_essay_score.values
groups = ess.prompt_name.values
X0 = ess[["essay_word_count"]].astype(float)

models = {
    "M0 LinearReg (word count)": (lambda: LinearRegression(), X0),
    "M0 GradBoost (word count)": (lambda: GradientBoostingRegressor(n_estimators=100, max_depth=2, random_state=SEED), X0),
    "M1 RandomForest (linguistic)": (lambda: RandomForestRegressor(300, min_samples_leaf=3, n_jobs=-1, random_state=SEED), X1),
    "M1 GradBoost (linguistic)": (lambda: GradientBoostingRegressor(n_estimators=300, max_depth=3, learning_rate=0.05, subsample=0.8, random_state=SEED), X1),
}
prompts = sorted(set(groups))
rows, oof = [], {k: np.zeros(len(y)) for k in models}
unc = np.zeros(len(y))
for p in prompts:
    te = groups == p
    for name, (mk, X) in models.items():
        m = mk().fit(X[~te], y[~te])
        pred = m.predict(X[te])
        oof[name][te] = pred
        if name.startswith("M1 RandomForest"):
            unc[te] = np.std([t.predict(X[te].values) for t in m.estimators_], axis=0)
        rows.append({"held_out_prompt": p, "model": name, "n": int(te.sum()), **regression_report(y[te], pred)})
per_prompt = pd.DataFrame(rows)
per_prompt.to_csv(RES / "step3_per_prompt.csv", index=False)

summ = []
for name in models:
    r = regression_report(y, oof[name])
    pp = per_prompt[per_prompt.model == name]
    summ.append({"model": name, "pooled_QWK": r["QWK"], "pooled_MAE": r["MAE"], "adj_acc": r["adj_acc"],
                 "mean_QWK_over_prompts": pp.QWK.mean(), "std_QWK": pp.QWK.std(), "worst_QWK": pp.QWK.min()})
summ = pd.DataFrame(summ).round(3)
summ.to_csv(RES / "step3_summary.csv", index=False)
print(summ.to_string(index=False))

# fairness by ELL (best M1 = RF): mean error at same true score
best = "M1 RandomForest (linguistic)"
df = pd.DataFrame({"y": y, "pred": oof[best], "ell": ess.ell.values, "unc": unc}).dropna(subset=["ell"])
df["err"] = df.pred - df.y
fair = df.groupby(["y", "ell"]).err.mean().unstack().round(3)
fair.columns = ["non-ELL", "ELL"]
fair["gap (ELL - nonELL)"] = (fair["ELL"] - fair["non-ELL"]).round(3)
fair.to_csv(RES / "step3_fairness_ell.csv")
maed = float(np.mean(np.abs(fair["gap (ELL - nonELL)"].values)))
print(fair, "\nMAED over score levels:", round(maed, 3))
print("mean score ELL / non-ELL:", ess.groupby("ell").holistic_essay_score.mean().round(2).to_dict())

# uncertainty: do high-spread essays have larger error?
df["abs_err"] = np.abs(to_level(df.pred) - df.y)
df["unc_q"] = pd.qcut(df.unc, 4, labels=["Q1 low", "Q2", "Q3", "Q4 high"])
uq = df.groupby("unc_q", observed=True).abs_err.mean().round(3)
uq.to_csv(RES / "step3_uncertainty.csv")
print(uq)

# robustness: length-shortcut test (duplicate text -> does predicted score jump?)
from sklearn.ensemble import RandomForestRegressor as RF
rf = RF(300, min_samples_leaf=3, n_jobs=-1, random_state=SEED).fit(X1, y)
rf0 = LinearRegression().fit(X0, y)
samp = ess.sample(300, random_state=SEED)
Xs = build_feature_frame(samp.full_text).fillna(0)
Xd = build_feature_frame((samp.full_text + "\n\n" + samp.full_text)).fillna(0)
shortcut = {"M1_RF_mean_shift_after_duplication": float((rf.predict(Xd) - rf.predict(Xs)).mean()),
            "M0_LR_mean_shift_after_duplication": float((rf0.predict(Xd[["n_words"]].rename(columns={"n_words": "essay_word_count"})) - rf0.predict(Xs[["n_words"]].rename(columns={"n_words": "essay_word_count"}))).mean())}
print(shortcut)

imp = pd.Series(rf.feature_importances_, index=X1.columns).sort_values(ascending=False)
imp.to_csv(RES / "step3_feature_importance.csv", header=["importance"])
json.dump({"shortcut": shortcut, "maed": maed, "r_len_score": float(ess.essay_word_count.corr(ess.holistic_essay_score))},
          open(RES / "step3_extra.json", "w"), indent=1)

# figures
fig, ax = plt.subplots(figsize=(6, 4))
imp.head(12)[::-1].plot.barh(ax=ax, color="#3b6ea5"); ax.set_title("Top-12 feature importance (M1 RF)"); plt.tight_layout()
plt.savefig(FIGS / "feature_importance.png", dpi=150); plt.close()
fig, ax = plt.subplots(figsize=(8, 4))
pv = per_prompt.pivot(index="held_out_prompt", columns="model", values="QWK")
pv.plot.bar(ax=ax); ax.set_ylabel("QWK"); ax.set_xlabel(""); ax.legend(fontsize=7)
plt.xticks(rotation=30, ha="right", fontsize=7); plt.title("Leave-one-prompt-out QWK"); plt.tight_layout()
plt.savefig(FIGS / "qwk_per_prompt.png", dpi=150); plt.close()
fig, ax = plt.subplots(figsize=(4.5, 4))
ax.scatter(ess.essay_word_count, y + np.random.default_rng(0).uniform(-.2, .2, len(y)), s=2, alpha=.25)
ax.set_xlabel("word count"); ax.set_ylabel("score"); ax.set_title("Word count vs score"); plt.tight_layout()
plt.savefig(FIGS / "length_vs_score.png", dpi=150); plt.close()
