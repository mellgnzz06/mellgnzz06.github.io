"""Correlation and regression: asthma ED visits vs. air pollution and poverty, 59 NYC community districts."""
import sys
import pandas as pd
from scipy import stats
import numpy as np


class OLS:
    """Ordinary least squares with HC1 (heteroskedasticity-robust) standard errors, written out with numpy."""
    def __init__(self, formula, data):
        y, xs = formula.split("~")
        xs = [x.strip() for x in xs.split("+")]
        Y = data[y.strip()].to_numpy(float)
        X = np.column_stack([np.ones(len(data))] + [data[x].to_numpy(float) for x in xs])
        n, k = X.shape
        XtX_inv = np.linalg.inv(X.T @ X)
        b = XtX_inv @ X.T @ Y
        e = Y - X @ b
        meat = X.T @ (X * (e ** 2)[:, None])
        cov = XtX_inv @ meat @ XtX_inv * n / (n - k)
        se = np.sqrt(np.diag(cov))
        names = ["Intercept"] + xs
        self.params = dict(zip(names, b))
        self.bse = dict(zip(names, se))
        self.pvalues = dict(zip(names, 2 * stats.t.sf(np.abs(b / se), n - k)))
        self.rsquared = 1 - (e @ e) / ((Y - Y.mean()) @ (Y - Y.mean()))
        self.fittedvalues = pd.Series(X @ b, index=data.index)
        self.resid = pd.Series(e, index=data.index)

    def fit(self, **kw):
        return self


class smf:
    ols = OLS

df = pd.read_csv(sys.argv[1])
df["bronx"] = (df.borough == "Bronx").astype(int)
outcomes = {"asthma_ed_adult_ageadj": "Adult", "asthma_ed_child_5_17": "Child 5-17"}

print("== Borough means ==")
print(df.groupby("borough")[list(outcomes) + ["pm25", "no2", "poverty_pct"]].mean().round(1).to_string())
print("\nCitywide means:", df[list(outcomes) + ["pm25", "no2", "poverty_pct"]].mean().round(2).to_dict())

print("\n== Pearson correlations (r, p) ==")
for y, lab in outcomes.items():
    for x in ["pm25", "no2", "poverty_pct"]:
        r, p = stats.pearsonr(df[x], df[y]); rs, ps = stats.spearmanr(df[x], df[y])
        print(f"{lab:10s} vs {x:12s} r={r:+.3f} p={p:.4f} | spearman={rs:+.3f} p={ps:.4f}")
r, p = stats.pearsonr(df.pm25, df.poverty_pct); print(f"pm25 vs poverty r={r:+.3f} p={p:.4f}")
r, p = stats.pearsonr(df.no2, df.poverty_pct); print(f"no2 vs poverty r={r:+.3f} p={p:.4f}")
r, p = stats.pearsonr(df.pm25, df.no2); print(f"pm25 vs no2 r={r:+.3f} p={p:.4f}")

print("\n== Excluding Manhattan (commercial core skews PM2.5) ==")
nm = df[df.borough != "Manhattan"]
for y, lab in outcomes.items():
    r, p = stats.pearsonr(nm.pm25, nm[y]); print(f"{lab} vs pm25 (n={len(nm)}): r={r:+.3f} p={p:.4f}")

print("\n== Regressions ==")
for y, lab in outcomes.items():
    for f in [f"{y} ~ pm25", f"{y} ~ poverty_pct", f"{y} ~ pm25 + poverty_pct", f"{y} ~ no2 + poverty_pct", f"{y} ~ pm25 + poverty_pct + bronx"]:
        m = smf.ols(f, data=df).fit(cov_type="HC1")
        terms = " ".join(f"{k}={v:+.2f}(p={m.pvalues[k]:.3f})" for k, v in m.params.items() if k != "Intercept")
        print(f"[{lab}] {f.split('~')[1].strip():28s} R2={m.rsquared:.2f} | {terms}")

print("\n== Bronx residuals, model: rate ~ pm25 + poverty ==")
for y, lab in outcomes.items():
    m = smf.ols(f"{y} ~ pm25 + poverty_pct", data=df).fit()
    df[f"pred_{y}"] = m.fittedvalues; df[f"resid_{y}"] = m.resid
    b = df[df.bronx == 1][["district", y, f"pred_{y}", f"resid_{y}"]].sort_values(f"resid_{y}", ascending=False)
    print(f"-- {lab}"); print(b.round(1).to_string(index=False))
    print("Bronx mean residual:", round(df.loc[df.bronx == 1, f'resid_{y}'].mean(), 1), "| districts above prediction:", int((df.loc[df.bronx==1, f'resid_{y}']>0).sum()), "of 12")

print("\n== Top 10 districts, adult rate ==")
print(df.sort_values("asthma_ed_adult_ageadj", ascending=False)[["district","borough","asthma_ed_adult_ageadj","asthma_ed_child_5_17","pm25","poverty_pct"]].head(10).round(1).to_string(index=False))
print("\n== Top 10 districts, child rate ==")
print(df.sort_values("asthma_ed_child_5_17", ascending=False)[["district","borough","asthma_ed_child_5_17","pm25","poverty_pct"]].head(10).round(1).to_string(index=False))
df.to_csv(sys.argv[2], index=False)

print("\n== Sensitivity: excluding Manhattan, with poverty ==")
for y, lab in outcomes.items():
    m = smf.ols(f"{y} ~ pm25 + poverty_pct", data=nm).fit()
    print(f"[{lab}] n={len(nm)} R2={m.rsquared:.2f} pm25={m.params['pm25']:+.2f} (95% CI {m.params['pm25']-1.96*m.bse['pm25']:+.1f} to {m.params['pm25']+1.96*m.bse['pm25']:+.1f}, p={m.pvalues['pm25']:.3f}) poverty={m.params['poverty_pct']:+.2f} (p={m.pvalues['poverty_pct']:.3f})")
r, p = stats.pearsonr(nm.pm25, nm.poverty_pct); print(f"non-Manhattan pm25 vs poverty r={r:+.3f} p={p:.4f}")
print("\nPM2.5 range:", df.pm25.min().round(2), "-", df.pm25.max().round(2), "| highest 5:")
print(df.sort_values("pm25", ascending=False)[["district", "borough", "pm25", "asthma_ed_adult_ageadj"]].head(5).round(2).to_string(index=False))
print("\nFull-model coefficient CIs (all 59):")
for y, lab in outcomes.items():
    m = smf.ols(f"{y} ~ pm25 + poverty_pct", data=df).fit()
    for k in ["pm25", "poverty_pct"]:
        print(f"[{lab}] {k}: {m.params[k]:+.2f} (95% CI {m.params[k]-1.96*m.bse[k]:+.2f} to {m.params[k]+1.96*m.bse[k]:+.2f})")
