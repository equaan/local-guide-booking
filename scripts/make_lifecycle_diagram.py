"""Draws the DevOps lifecycle diagram used in docs/task-02.md.

Run: python scripts/make_lifecycle_diagram.py
Output: docs/evidence/task-02/devops-lifecycle.png
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

OUT = Path(__file__).resolve().parent.parent / "docs" / "evidence" / "task-02" / "devops-lifecycle.png"

DEV = "#1F3864"
OPS = "#1E6B52"

# (title, tool lines) in flow order
DEV_STAGES = [
    ("1 PLAN", ["GitHub Issues + Projects", "PRD, user stories"]),
    ("2 CODE", ["Git, feature branches", "Pull requests + review", "AI assistant (logged)"]),
    ("3 BUILD", ["Jenkins pipeline", "pip install, Docker build", "(multi-stage, non-root)"]),
    ("4 TEST + SCAN", ["pytest, Selenium", "SonarQube quality gate", "Trivy image scan"]),
]
OPS_STAGES = [
    ("5 RELEASE", ["Versioned Docker Hub image", "Tag bump in GitOps repo"]),
    ("6 DEPLOY", ["ArgoCD sync + Helm", "Kubernetes (k3s / k3d)"]),
    ("7 OPERATE", ["Ansible-built environment", "Rollback = git revert"]),
    ("8 MONITOR", ["Prometheus + Grafana", "/health, /ready, /metrics", "Logs to stdout"]),
]

W, H = 2.55, 1.55
GAP = 0.55
X0 = 0.6
Y_TOP, Y_BOT = 4.2, 1.35


def box(ax, x, y, title, lines, color):
    ax.add_patch(FancyBboxPatch((x, y), W, H, boxstyle="round,pad=0.02,rounding_size=0.12",
                                fc="white", ec=color, lw=2.2))
    ax.add_patch(FancyBboxPatch((x, y + H - 0.42), W, 0.42, boxstyle="round,pad=0.02,rounding_size=0.12",
                                fc=color, ec=color, lw=2.2))
    ax.text(x + W / 2, y + H - 0.21, title, ha="center", va="center", color="white",
            fontsize=11, fontweight="bold")
    for i, line in enumerate(lines):
        ax.text(x + W / 2, y + H - 0.68 - i * 0.28, line, ha="center", va="center",
                fontsize=8.6, color="#222222")


def arrow(ax, p1, p2, color, style="-|>", rad=0.0, lw=2.0):
    ax.add_patch(FancyArrowPatch(p1, p2, arrowstyle=style, mutation_scale=16, color=color,
                                 lw=lw, connectionstyle=f"arc3,rad={rad}"))


fig, ax = plt.subplots(figsize=(13.6, 6.6))
ax.set_xlim(0, 13.6)
ax.set_ylim(0, 6.6)
ax.axis("off")

xs = [X0 + i * (W + GAP) for i in range(4)]

ax.text(0.15, 6.2, "DevOps lifecycle: Local Guide Booking System", fontsize=14, fontweight="bold", color="#111111")
ax.text(0.15, 5.9, "Development loop (top, left to right)  |  Operations loop (bottom, right to left)",
        fontsize=9.5, color="#555555")

for x, (t, l) in zip(xs, DEV_STAGES):
    box(ax, x, Y_TOP, t, l, DEV)
for x, (t, l) in zip(xs[::-1], OPS_STAGES):
    box(ax, x, Y_BOT, t, l, OPS)

# Dev row arrows (left to right)
for i in range(3):
    arrow(ax, (xs[i] + W + 0.03, Y_TOP + H / 2), (xs[i + 1] - 0.03, Y_TOP + H / 2), DEV)
# Ops row arrows (right to left)
for i in range(3, 0, -1):
    arrow(ax, (xs[i] - 0.03, Y_BOT + H / 2), (xs[i - 1] + W + 0.03, Y_BOT + H / 2), OPS)
# Hand-off: TEST -> RELEASE (down on the right)
arrow(ax, (xs[3] + W / 2, Y_TOP - 0.03), (xs[3] + W / 2, Y_BOT + H + 0.03), "#B03A2E", lw=2.4)
ax.text(xs[3] + W / 2 + 0.12, (Y_TOP + Y_BOT + H) / 2, "gates pass?\nno: stop", fontsize=8.6,
        color="#B03A2E", va="center", ha="left")
# Feedback: MONITOR -> PLAN (up on the left)
arrow(ax, (xs[0] + W / 2, Y_BOT + H + 0.03), (xs[0] + W / 2, Y_TOP - 0.03), "#7D6608", lw=2.4)
ax.text(xs[0] + W / 2 - 0.12, (Y_TOP + Y_BOT + H) / 2, "feedback: metrics,\nincidents, new issues",
        fontsize=8.6, color="#7D6608", va="center", ha="right")

ax.text(6.8, 0.72, "Source of truth: two Git repositories. App repo (code, tests, Jenkinsfile) and GitOps repo (Kubernetes/Helm config).",
        ha="center", fontsize=9.2, color="#333333")
ax.text(6.8, 0.38, "Jenkins never deploys by hand: it publishes an image and commits the new tag; ArgoCD applies it to the cluster.",
        ha="center", fontsize=9.2, color="#333333")

OUT.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(OUT, dpi=170, bbox_inches="tight", facecolor="white")
print("wrote", OUT)
