"""Essay-level argument-structure features built from segment role labels (gold or predicted)."""
import numpy as np
import pandas as pd

ROLES = ["Lead", "Position", "Claim", "Counterclaim", "Rebuttal", "Evidence", "Concluding Statement"]


def structure_features(seg: pd.DataFrame, roles, essay_order) -> pd.DataFrame:
    """One row per essay, in the order of `essay_order` (essay_id_comp)."""
    d = pd.DataFrame({"eid": seg.essay_id_comp.values, "role": np.asarray(roles), "len": seg.seg_len.values,
                      "rank": seg.rank_rel.values})
    d = d[d.role != "none"]
    cnt = d.pivot_table(index="eid", columns="role", values="len", aggfunc="count", fill_value=0).reindex(columns=ROLES, fill_value=0)
    wds = d.pivot_table(index="eid", columns="role", values="len", aggfunc="sum", fill_value=0).reindex(columns=ROLES, fill_value=0)
    n = cnt.sum(1).clip(lower=1)
    out = pd.DataFrame(index=cnt.index)
    for r in ROLES:
        k = r.split()[0].lower()
        out[f"n_{k}"] = cnt[r]
        out[f"share_{k}"] = cnt[r] / n
        out[f"words_{k}"] = wds[r]
    out["n_segments"] = cnt.sum(1)
    out["has_counterclaim"] = (cnt["Counterclaim"] > 0).astype(float)
    out["has_rebuttal"] = (cnt["Rebuttal"] > 0).astype(float)
    out["has_position"] = (cnt["Position"] > 0).astype(float)
    out["evidence_per_claim"] = cnt["Evidence"] / cnt["Claim"].clip(lower=1)
    out["rebuttal_per_counterclaim"] = cnt["Rebuttal"] / cnt["Counterclaim"].clip(lower=1)
    out["n_distinct_roles"] = (cnt > 0).sum(1)
    return out.reindex(essay_order.values).fillna(0).reset_index(drop=True)
