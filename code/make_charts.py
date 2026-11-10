"""Figures for the report and poster."""
import sys
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats

df = pd.read_csv(sys.argv[1]); out = sys.argv[2]
BRONX, OTHER, INK, MUTED, GRID = "#2a78d6", "#b9b8b2", "#0b0b0b", "#52514e", "#e6e5e0"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11, "axes.edgecolor": MUTED,
                     "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED})

def panel(ax, x, y, xlabel, ylabel, title):
    o, b = df[df.borough != "Bronx"], df[df.borough == "Bronx"]
    ax.scatter(o[x], o[y], s=48, color=OTHER, edgecolor="white", linewidth=1.2, zorder=3, label="Other boroughs (47)")
    ax.scatter(b[x], b[y], s=58, color=BRONX, edgecolor="white", linewidth=1.2, zorder=4, label="Bronx (12)")
    s = stats.linregress(df[x], df[y]); xs = pd.Series([df[x].min(), df[x].max()])
    ax.plot(xs, s.intercept + s.slope * xs, color=INK, lw=1.5, ls="--", zorder=2)
    r, p = stats.pearsonr(df[x], df[y])
    ax.text(0.03, 0.96, f"r = {r:+.2f}, p {'< 0.001' if p < 0.001 else '= ' + format(p, '.2f')}", transform=ax.transAxes, va="top", fontsize=11, color=INK, fontweight="bold")
    ax.set_xlabel(xlabel); ax.set_ylabel(ylabel); ax.set_title(title, loc="left", fontsize=12, color=INK, pad=10)
    ax.grid(color=GRID, lw=0.8); ax.set_axisbelow(True)
    for sp in ["top", "right"]: ax.spines[sp].set_visible(False)

# Figure 1: the main finding, two panels on the same y-axis
for y, ylab, fname, who in [("asthma_ed_adult_ageadj", "Adult asthma ED visits per 10,000 (age-adjusted)", "fig1_adult_pm25_vs_poverty.png", "adult"),
                            ("asthma_ed_child_5_17", "Child (5-17) asthma ED visits per 10,000", "fig2_child_pm25_vs_poverty.png", "child")]:
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.8), sharey=True)
    panel(axes[0], "pm25", y, "PM2.5 annual mean (µg/m³), 2023", ylab, "Air pollution (PM2.5)")
    panel(axes[1], "poverty_pct", y, "Residents below poverty line (%), 2019-23", "", "Neighborhood poverty")
    mid = df[df.district.str.startswith("Midtown")].iloc[0]
    axes[0].annotate("Midtown Manhattan", (mid.pm25, mid[y]), xytext=(-10, 28), textcoords="offset points", ha="right", fontsize=9.5, color=MUTED, arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
    mh = df[df.district.str.startswith("Mott Haven")].iloc[0]
    axes[1].annotate("Mott Haven (Bronx CD1)", (mh.poverty_pct, mh[y]), xytext=(-10, -4), textcoords="offset points", ha="right", fontsize=9.5, color=MUTED)
    axes[1].legend(loc="lower right", frameon=False, fontsize=10)
    fig.suptitle(f"{'Adult' if who=='adult' else 'Child'} asthma ED visits track poverty, not PM2.5, across 59 NYC community districts", x=0.01, ha="left", fontsize=13.5, fontweight="bold", color=INK)
    fig.text(0.01, 0.005, "Source: NYC Dept. of Health and Mental Hygiene, Environment & Health Data Portal (2023 asthma ED visits and PM2.5; 2019-23 poverty). Dashed line = best fit.", fontsize=8.5, color=MUTED)
    fig.tight_layout(rect=(0, 0.03, 1, 0.97)); fig.savefig(f"{out}/{fname}", dpi=200, facecolor="white"); plt.close(fig)

# Figure 3: borough averages
order = ["Bronx", "Brooklyn", "Manhattan", "Queens", "Staten Island"]
g = df.groupby("borough")[["asthma_ed_adult_ageadj", "asthma_ed_child_5_17"]].mean().loc[order]
fig, axes = plt.subplots(1, 2, figsize=(11, 4.0))
for ax, col, lab in [(axes[0], "asthma_ed_adult_ageadj", "Adults (age-adjusted)"), (axes[1], "asthma_ed_child_5_17", "Children 5-17")]:
    colors = [BRONX if b == "Bronx" else OTHER for b in order]
    bars = ax.barh(order[::-1], g[col][::-1], color=colors[::-1], height=0.62)
    for bar, v in zip(bars, g[col][::-1]):
        ax.text(v + g[col].max() * 0.015, bar.get_y() + bar.get_height() / 2, f"{v:.0f}", va="center", fontsize=10.5, color=INK)
    ax.set_title(lab, loc="left", fontsize=12, color=INK); ax.set_xlim(0, g[col].max() * 1.15)
    ax.set_xlabel("Asthma ED visits per 10,000 (mean of districts)")
    for sp in ["top", "right"]: ax.spines[sp].set_visible(False)
    ax.grid(axis="x", color=GRID, lw=0.8); ax.set_axisbelow(True)
fig.suptitle("The Bronx has the highest asthma ED visit rates of any borough", x=0.01, ha="left", fontsize=13.5, fontweight="bold", color=INK)
fig.text(0.01, 0.005, "Source: NYC DOHMH Environment & Health Data Portal, 2023. Unweighted mean of community districts in each borough.", fontsize=8.5, color=MUTED)
fig.tight_layout(rect=(0, 0.03, 1, 0.96)); fig.savefig(f"{out}/fig3_borough_averages.png", dpi=200, facecolor="white"); plt.close(fig)
print("done")
