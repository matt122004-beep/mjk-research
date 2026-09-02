#!/usr/bin/env python3
"""Build the experimental homepage figures from explicit counts.

Destination: responsive web figures in SVG format.
Estimator: observed binomial proportion, count / n.
Uncertainty: two-sided 95% Wilson score interval, z = 1.959963984540054.
Transformations: rate calculation, declared series grouping, and declared release ordering.
Missing or excluded observations: none in the supplied homepage table.

The script writes opaque, white-background SVGs and records input/output hashes
in a manifest. Lines connect measured cells only; they are not fitted trends and
do not imply that release sequence caused the observed differences.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "assets" / "data" / "homepage_graph_data.csv"
OUTPUT_DIR = ROOT / "assets" / "img" / "figures"
MANIFEST_PATH = OUTPUT_DIR / "homepage_graph_manifest.json"

UPSTREAM_SOURCE = (
    "Machine Prayer Study/prospective/_v7_comprehensive_results_20260817/"
    "01_RATES_MASTER_V1.json"
)
UPSTREAM_SOURCE_SHA256 = "47cd32bb6fcebacf5928029f83bd7e798b83d84811f8a97acbbc234560ba4692"

WHITE = "#FFFFFF"
INK = "#202126"
MUTED = "#6F7177"
AXIS = "#A9ABB0"
GRID = "#E2E3E5"
RUBRIC = "#A23B2A"
OPENAI = "#4F7184"

SERIES_STYLES = {
    "Qwen 27B": {"color": "#7357A6", "marker": "o", "linestyle": "-"},
    "Mistral Medium": {"color": "#C46E25", "marker": "s", "linestyle": "--"},
    "DeepSeek": {"color": "#256A93", "marker": "D", "linestyle": "-."},
    "Gemini Flash": {"color": "#2B806D", "marker": "^", "linestyle": ":"},
}

TRAJECTORY_SUMMARIES = {
    "Qwen 27B": "Sharp decline",
    "Mistral Medium": "Steady rise",
    "DeepSeek": "Rise, then reversal",
    "Gemini Flash": "Rise, then zero",
}

Z_95 = 1.959963984540054


@dataclass(frozen=True)
class Cell:
    view: str
    series: str
    provider: str
    model: str
    label: str
    sequence: int
    count: int
    n: int
    status: str
    released: str
    origin: str
    thinking: str
    source: str

    @property
    def rate(self) -> float:
        return 100.0 * self.count / self.n

    @property
    def interval(self) -> tuple[float, float]:
        """Return the 95% Wilson score interval in percentage points."""
        p = self.count / self.n
        denominator = 1.0 + (Z_95**2 / self.n)
        center = (p + Z_95**2 / (2.0 * self.n)) / denominator
        half = (
            Z_95
            * math.sqrt((p * (1.0 - p) / self.n) + Z_95**2 / (4.0 * self.n**2))
            / denominator
        )
        return 100.0 * (center - half), 100.0 * (center + half)

    @property
    def released_date(self) -> datetime:
        if not self.released:
            raise ValueError(f"Missing release date for trajectory cell: {self.model}")
        return datetime.strptime(self.released, "%Y-%m-%d")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_cells() -> list[Cell]:
    cells: list[Cell] = []
    with DATA_PATH.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            cell = Cell(
                view=row["view"],
                series=row["series"],
                provider=row["provider"],
                model=row["model"],
                label=row["label"],
                sequence=int(row["sequence"]),
                count=int(row["count"]),
                n=int(row["n"]),
                status=row["status"],
                released=row["released"],
                origin=row["origin"],
                thinking=row["thinking"],
                source=row["source"],
            )
            if cell.n <= 0 or not 0 <= cell.count <= cell.n:
                raise ValueError(f"Invalid binomial cell: {cell}")
            cells.append(cell)

    by_view = {view: [cell for cell in cells if cell.view == view] for view in {c.view for c in cells}}
    if len(by_view.get("decline", [])) != 10:
        raise ValueError("Expected 10 decline rows")
    if len(by_view.get("trajectory", [])) != 15:
        raise ValueError("Expected 15 trajectory rows")
    if {cell.series for cell in by_view["trajectory"]} != set(SERIES_STYLES):
        raise ValueError("Trajectory series do not match the declared visual styles")
    return cells


STYLE = {
    "font.family": "sans-serif",
    "font.sans-serif": ["Avenir Next", "Avenir", "DejaVu Sans"],
    "font.size": 10.5,
    "axes.facecolor": WHITE,
    "axes.edgecolor": AXIS,
    "axes.labelcolor": INK,
    "axes.titlecolor": INK,
    "axes.titlesize": 13.0,
    "axes.titleweight": 600,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "figure.facecolor": WHITE,
    "savefig.facecolor": WHITE,
    "svg.fonttype": "none",
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
}


def style_percent_axis(ax: mpl.axes.Axes, *, show_ylabel: bool = True) -> None:
    ax.set_ylim(-3.0, 103.0)
    ticks = [0, 20, 40, 60, 80, 100]
    ax.set_yticks(ticks, labels=[f"{value}%" for value in ticks])
    ax.grid(True, color=GRID, linewidth=0.75, zorder=0)
    ax.set_axisbelow(True)
    ax.tick_params(axis="both", length=3.5, width=0.7, color=AXIS, pad=6)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(AXIS)
    ax.spines["bottom"].set_color(AXIS)
    ax.spines["left"].set_linewidth(0.8)
    ax.spines["bottom"].set_linewidth(0.8)
    if not show_ylabel:
        ax.tick_params(labelleft=False)


def plot_interval_line(
    ax: mpl.axes.Axes,
    x: list[float] | list[datetime],
    rows: list[Cell],
    *,
    color: str,
    marker: str,
    linestyle: str,
) -> None:
    rates = [cell.rate for cell in rows]
    lower = [max(0.0, cell.rate - cell.interval[0]) for cell in rows]
    upper = [max(0.0, cell.interval[1] - cell.rate) for cell in rows]
    ax.plot(
        x,
        rates,
        color=color,
        linewidth=1.8,
        linestyle=linestyle,
        marker=marker,
        markersize=6.8,
        markerfacecolor=WHITE,
        markeredgecolor=color,
        markeredgewidth=1.6,
        zorder=3,
    )
    ax.errorbar(
        x,
        rates,
        yerr=[lower, upper],
        fmt="none",
        ecolor=color,
        elinewidth=0.85,
        alpha=0.48,
        capsize=2.5,
        capthick=0.85,
        zorder=2,
    )


def annotate_rate(
    ax: mpl.axes.Axes,
    x: float | datetime,
    row: Cell,
    *,
    color: str,
    offset: tuple[float, float] = (0.0, 10.0),
    label: str | None = None,
    align: str = "center",
) -> None:
    text = f"{row.rate:.1f}%" if label is None else f"{label}\n{row.rate:.1f}%"
    ax.annotate(
        text,
        xy=(x, row.rate),
        xytext=offset,
        textcoords="offset points",
        ha=align,
        va="bottom" if offset[1] >= 0 else "top",
        color=color,
        fontsize=8.3 if label else 9.0,
        fontweight=600,
        linespacing=1.12,
        bbox={"facecolor": WHITE, "edgecolor": "none", "alpha": 0.86, "pad": 0.5},
        zorder=5,
    )


def build_decline(cells: list[Cell]) -> Path:
    rows = [cell for cell in cells if cell.view == "decline"]
    panels = [
        ("Claude", RUBRIC, "o", "-"),
        ("OpenAI", OPENAI, "s", "--"),
    ]

    with mpl.rc_context(STYLE):
        fig, axes = plt.subplots(1, 2, figsize=(12.4, 5.8), sharey=True, layout="constrained")
        fig.set_constrained_layout_pads(w_pad=0.08, h_pad=0.08, wspace=0.06, hspace=0.02)

        for index, (series, color, marker, linestyle) in enumerate(panels):
            ax = axes[index]
            series_rows = sorted((row for row in rows if row.series == series), key=lambda row: row.sequence)
            x = list(range(len(series_rows)))
            plot_interval_line(
                ax,
                x,
                series_rows,
                color=color,
                marker=marker,
                linestyle=linestyle,
            )
            style_percent_axis(ax, show_ylabel=index == 0)
            ax.set_xlim(-0.45, len(series_rows) - 0.55)
            ax.set_xticks(x, labels=[row.label for row in series_rows])
            ax.tick_params(axis="x", labelrotation=31, labelsize=8.8)
            for label in ax.get_xticklabels():
                label.set_ha("right")
                label.set_rotation_mode("anchor")
            ax.set_title(series, loc="left", pad=14)
            ax.text(
                1.0,
                1.025,
                f"{len(series_rows)} measured releases",
                transform=ax.transAxes,
                ha="right",
                va="bottom",
                fontsize=8.5,
                color=MUTED,
            )
            for x_value, row in zip(x, series_rows, strict=True):
                offset_y = 10.0 if row.rate < 82.0 else -12.0
                annotate_rate(ax, x_value, row, color=color, offset=(0.0, offset_y))

        fig.supylabel("Conversations reaching spiritual bliss (%)", color=INK, fontsize=11.0)
        fig.supxlabel("Tested release sequence within provider  ·  earlier to later", color=INK, fontsize=10.5)
        return save_svg(
            fig,
            "bliss-decline-v1.svg",
            title="Spiritual-bliss rates decline across tested Claude and OpenAI releases",
            description=(
                "Two benchmark-style line panels show observed spiritual-bliss rates with 95 percent "
                "Wilson intervals. Claude declines from 87.8 percent in Opus 4 to zero in Opus 5; "
                "OpenAI declines from 20 percent in GPT-4o to zero in the tested GPT-5.6 cell."
            ),
        )


def build_trajectories(cells: list[Cell]) -> Path:
    rows = [cell for cell in cells if cell.view == "trajectory"]

    with mpl.rc_context(STYLE):
        fig, axes = plt.subplots(
            2,
            2,
            figsize=(12.4, 7.25),
            sharey=True,
            layout="constrained",
        )
        fig.set_constrained_layout_pads(w_pad=0.07, h_pad=0.08, wspace=0.08, hspace=0.12)

        for panel_index, ((series, style), ax) in enumerate(zip(SERIES_STYLES.items(), axes.flat, strict=True)):
            series_rows = sorted(
                (row for row in rows if row.series == series),
                key=lambda row: row.sequence,
            )
            x = list(range(len(series_rows)))
            plot_interval_line(
                ax,
                x,
                series_rows,
                color=style["color"],
                marker=style["marker"],
                linestyle=style["linestyle"],
            )
            style_percent_axis(ax, show_ylabel=panel_index % 2 == 0)
            ax.set_xlim(-0.42, len(series_rows) - 0.58)
            ax.set_xticks(x, labels=[row.label for row in series_rows])
            ax.tick_params(axis="x", labelrotation=24, labelsize=8.4)
            for label in ax.get_xticklabels():
                label.set_ha("right")
                label.set_rotation_mode("anchor")

            ax.set_title(series, loc="left", pad=12, color=style["color"])
            ax.text(
                1.0,
                1.025,
                f"{TRAJECTORY_SUMMARIES[series]}  ·  {len(series_rows)} releases",
                transform=ax.transAxes,
                ha="right",
                va="bottom",
                fontsize=8.3,
                color=MUTED,
            )
            for x_value, row in zip(x, series_rows, strict=True):
                offset_y = -13.0 if row.rate >= 86.0 else 9.0
                annotate_rate(ax, x_value, row, color=style["color"], offset=(0.0, offset_y))

        fig.supylabel("Conversations reaching spiritual bliss (%)", color=INK, fontsize=11.0)
        fig.supxlabel("Tested release sequence within each model family  ·  earlier to later", color=INK, fontsize=10.5)
        return save_svg(
            fig,
            "bliss-trajectories-v1.svg",
            title="Spiritual-bliss rates follow different trajectories across four model families",
            description=(
                "Four aligned line-chart panels trace repeated measured cells for Qwen 27B, "
                "Mistral Medium, DeepSeek, and Gemini Flash on a shared percentage scale. "
                "Qwen declines, Mistral rises, DeepSeek rises sharply and reverses, and Gemini "
                "rises before falling to zero. Points show observed rates and vertical whiskers "
                "show 95 percent Wilson intervals."
            ),
        )


def save_svg(fig: mpl.figure.Figure, filename: str, *, title: str, description: str) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    destination = OUTPUT_DIR / filename
    temporary = destination.with_suffix(".tmp.svg")
    fig.savefig(
        temporary,
        format="svg",
        facecolor=WHITE,
        edgecolor=WHITE,
        bbox_inches=None,
        metadata={
            "Title": title,
            "Description": description,
            "Creator": "Matplotlib via build_homepage_figures.py",
            "Date": "2026-08-29",
        },
    )
    plt.close(fig)
    temporary.replace(destination)
    return destination


def write_manifest(outputs: list[Path]) -> None:
    manifest = {
        "status": "experimental_v1",
        "source_data": str(DATA_PATH.relative_to(ROOT)),
        "source_sha256": sha256(DATA_PATH),
        "upstream_source": UPSTREAM_SOURCE,
        "upstream_source_sha256": UPSTREAM_SOURCE_SHA256,
        "estimator": "count / n",
        "uncertainty": "two-sided 95% Wilson score interval; z=1.959963984540054",
        "transformations": [
            "calculate percentage from count and n",
            "sort each line by declared sequence or release date",
            "connect observed cells with straight segments; no fitted trend or smoothing",
        ],
        "missing_data": "none in supplied homepage table",
        "outputs": [
            {"path": str(path.relative_to(ROOT)), "sha256": sha256(path)} for path in outputs
        ],
    }
    temporary = MANIFEST_PATH.with_suffix(".tmp.json")
    temporary.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    temporary.replace(MANIFEST_PATH)


def main() -> None:
    cells = load_cells()
    outputs = [build_decline(cells), build_trajectories(cells)]
    write_manifest(outputs)
    for path in outputs:
        print(path.relative_to(ROOT))
    print(MANIFEST_PATH.relative_to(ROOT))


if __name__ == "__main__":
    main()
