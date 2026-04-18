"""Omics recipes.

Contains:
    volcano              — −log10(p) vs log2FC with top-hit labels
    ma_plot              — log fold-change vs mean expression
    heatmap_annotated    — clustered heatmap with row/col annotation bars
    gsea_bubble          — pathway vs NES, size by gene count, color by FDR
    enrichment_dotplot   — ORA results grouped by ontology
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from matplotlib import colormaps
from matplotlib.gridspec import GridSpecFromSubplotSpec
from scipy.cluster.hierarchy import leaves_list, linkage

from ..core.contract import (
    AnnotatedHeatmapInput,
    EnrichmentDotInput,
    GSEABubbleInput,
    MAInput,
    VolcanoInput,
)
from ..core.palette import get_palette
from ..core.primitives import callout_box, dashed_reference, halo_text, iter_palette


def _significance_mask(df: pd.DataFrame, lfc_col: str, sig_col: str,
                       lfc_thr: float, sig_thr: float) -> pd.Series:
    return (np.abs(df[lfc_col]) >= lfc_thr) & (df[sig_col] <= sig_thr)


def volcano(ax, contract, palette: str = "journal_neutral"):
    """Volcano plot with significance thresholds and top-n label overlay."""

    c = VolcanoInput.model_validate(contract)
    pal = iter_palette(get_palette(palette).categorical, 6)
    df = c.df.copy()
    sig_col = c.fdr_col or c.pval_col
    df["_neglog"] = -np.log10(df[c.pval_col].clip(lower=1e-300))
    mask = _significance_mask(df, c.lfc_col, sig_col, c.lfc_threshold, c.fdr_threshold)
    ax.scatter(df.loc[~mask, c.lfc_col], df.loc[~mask, "_neglog"],
               s=8, color="#B0BEC5", alpha=0.6, linewidth=0)
    up_mask = mask & (df[c.lfc_col] > 0)
    down_mask = mask & (df[c.lfc_col] < 0)
    ax.scatter(df.loc[up_mask, c.lfc_col], df.loc[up_mask, "_neglog"],
               s=14, color="#C62828", alpha=0.85, linewidth=0)
    ax.scatter(df.loc[down_mask, c.lfc_col], df.loc[down_mask, "_neglog"],
               s=14, color="#1565C0", alpha=0.85, linewidth=0)
    dashed_reference(ax, c.lfc_threshold, axis="x")
    dashed_reference(ax, -c.lfc_threshold, axis="x")
    dashed_reference(ax, -np.log10(c.fdr_threshold), axis="y")
    if c.label_col and c.label_col in df.columns:
        hits = df[mask].nlargest(c.top_n_labels, "_neglog")
        for _, row in hits.iterrows():
            halo_text(ax, row[c.lfc_col], row["_neglog"], str(row[c.label_col]),
                      color="#111", fontsize=7, fontweight="regular",
                      ha="left", va="bottom")
    ax.set_xlabel(c.lfc_col)
    ax.set_ylabel("−log10 p")
    return ax


def demo_volcano() -> VolcanoInput:
    rng = np.random.default_rng(40)
    n = 800
    lfc = rng.normal(0, 1, size=n)
    pval = 10 ** (-rng.exponential(2, size=n))
    pval = np.clip(pval, 1e-10, 1.0)
    labels = [f"GENE{i:03d}" for i in range(n)]
    df = pd.DataFrame({"log2FC": lfc, "pvalue": pval, "gene": labels})
    return VolcanoInput(df=df, label_col="gene", lfc_threshold=1.5, fdr_threshold=0.01)


def ma_plot(ax, contract, palette: str = "journal_neutral"):
    """MA plot with significant-gene highlight."""

    c = MAInput.model_validate(contract)
    df = c.df
    if c.sig_col and c.sig_col in df.columns:
        sig = df[c.sig_col].astype(bool)
    else:
        sig = pd.Series(False, index=df.index)
    ax.scatter(df.loc[~sig, c.a_col], df.loc[~sig, c.m_col],
               s=8, color="#B0BEC5", alpha=0.5, linewidth=0)
    ax.scatter(df.loc[sig, c.a_col], df.loc[sig, c.m_col],
               s=12, color="#C62828", alpha=0.9, linewidth=0)
    ax.axhline(0.0, color="#111", linewidth=0.8)
    ax.set_xlabel(c.a_col); ax.set_ylabel(c.m_col)
    return ax


def demo_ma_plot() -> MAInput:
    rng = np.random.default_rng(41)
    n = 500
    A = rng.uniform(-1, 8, size=n)
    M = rng.normal(0, 0.8, size=n)
    sig = np.abs(M) > 1.5
    return MAInput(df=pd.DataFrame({"A": A, "M": M, "sig": sig}), sig_col="sig")


def heatmap_annotated(ax, contract, palette: str = "journal_neutral"):
    """Clustered heatmap with optional row/col annotation bars."""

    c = AnnotatedHeatmapInput.model_validate(contract)
    matrix = np.asarray(c.matrix, dtype=float)
    if matrix.size == 0:
        return ax
    ax.set_axis_off()
    child = GridSpecFromSubplotSpec(2, 2, subplot_spec=ax.get_subplotspec(),
                                    width_ratios=(0.04, 1.0),
                                    height_ratios=(0.04, 1.0),
                                    hspace=0.02, wspace=0.02)
    main = ax.figure.add_subplot(child[1, 1])
    try:
        row_order = leaves_list(linkage(matrix, method="average"))
        col_order = leaves_list(linkage(matrix.T, method="average"))
    except (ValueError, IndexError):
        row_order = np.arange(matrix.shape[0])
        col_order = np.arange(matrix.shape[1])
    ordered = matrix[np.ix_(row_order, col_order)]
    main.imshow(ordered, cmap=c.cmap, aspect="auto")
    main.set_xticks(range(len(col_order)))
    main.set_xticklabels([c.col_labels[i] for i in col_order], rotation=75,
                         fontsize=6)
    main.set_yticks(range(len(row_order)))
    main.set_yticklabels([c.row_labels[i] for i in row_order], fontsize=6)
    for side in ("top", "right", "left", "bottom"):
        main.spines[side].set_visible(False)
    if c.row_annotation:
        row_ax = ax.figure.add_subplot(child[1, 0], sharey=main)
        values = pd.Categorical([c.row_annotation[i] for i in row_order])
        cm = colormaps.get_cmap("tab10")
        row_ax.imshow(values.codes.reshape(-1, 1), aspect="auto",
                      cmap=cm)
        row_ax.set_xticks([]); row_ax.set_yticks([])
        for side in ("top", "right", "left", "bottom"):
            row_ax.spines[side].set_visible(False)
    if c.col_annotation:
        col_ax = ax.figure.add_subplot(child[0, 1], sharex=main)
        values = pd.Categorical([c.col_annotation[i] for i in col_order])
        cm = colormaps.get_cmap("tab20")
        col_ax.imshow(values.codes.reshape(1, -1), aspect="auto",
                      cmap=cm)
        col_ax.set_xticks([]); col_ax.set_yticks([])
        for side in ("top", "right", "left", "bottom"):
            col_ax.spines[side].set_visible(False)
    return ax


def demo_heatmap_annotated() -> AnnotatedHeatmapInput:
    rng = np.random.default_rng(42)
    matrix = rng.normal(size=(10, 12))
    rows = [f"g{i}" for i in range(10)]
    cols = [f"s{i}" for i in range(12)]
    row_ann = ["A"] * 5 + ["B"] * 5
    col_ann = ["WT"] * 6 + ["KO"] * 6
    return AnnotatedHeatmapInput(matrix=matrix, row_labels=rows, col_labels=cols,
                                 row_annotation=row_ann, col_annotation=col_ann)


def gsea_bubble(ax, contract, palette: str = "journal_neutral"):
    """Pathway vs NES bubble plot — size by gene count, color by FDR."""

    c = GSEABubbleInput.model_validate(contract)
    df = c.df.sort_values("NES").tail(c.max_pathways)
    pal = colormaps.get_cmap("viridis")
    sizes = 20 + 8 * df["n_genes"].to_numpy()
    colors = pal(1.0 - df["FDR"].clip(0, 1).to_numpy())
    ax.scatter(df["NES"], range(len(df)), s=sizes, color=colors,
               edgecolor="#222", linewidth=0.4)
    ax.set_yticks(range(len(df)))
    ax.set_yticklabels(df["pathway"].astype(str).values, fontsize=7)
    ax.set_xlabel("NES")
    callout_box(ax, 0.02, 0.03, "color: 1 − FDR", ha="left", va="bottom",
                color="#333333")
    return ax


def demo_gsea_bubble() -> GSEABubbleInput:
    rng = np.random.default_rng(43)
    n = 14
    df = pd.DataFrame({
        "pathway": [f"pathway_{i}" for i in range(n)],
        "NES": rng.uniform(-2.5, 2.5, size=n),
        "FDR": rng.uniform(0.001, 0.3, size=n),
        "n_genes": rng.integers(10, 120, size=n),
    })
    return GSEABubbleInput(df=df)


def enrichment_dotplot(ax, contract, palette: str = "okabe_ito"):
    """Enrichment dotplot grouped by ontology, sized by gene ratio."""

    c = EnrichmentDotInput.model_validate(contract)
    df = c.df.copy()
    df["_mlp"] = -np.log10(df["pvalue"].clip(lower=1e-300))
    ontos = list(df["ontology"].dropna().unique())
    pal = iter_palette(get_palette(palette).categorical, len(ontos) or 1)
    y = 0
    for onto_idx, onto in enumerate(ontos):
        sub = df[df["ontology"] == onto].sort_values("_mlp", ascending=True)
        for _, row in sub.iterrows():
            ax.scatter(row["_mlp"], y, s=30 + 120 * float(row["ratio"]),
                       color=pal[onto_idx % len(pal)], edgecolor="#222",
                       linewidth=0.4)
            ax.text(-0.02, y, str(row["term"]), transform=ax.get_yaxis_transform(),
                    ha="right", va="center", fontsize=7)
            y += 1
    ax.set_xlabel("−log10 p")
    ax.set_yticks([])
    return ax


def demo_enrichment_dotplot() -> EnrichmentDotInput:
    rng = np.random.default_rng(44)
    rows = []
    for onto in ("BP", "MF", "CC"):
        for i in range(4):
            rows.append({
                "ontology": onto,
                "term": f"{onto} term {i}",
                "ratio": float(rng.uniform(0.1, 0.6)),
                "pvalue": float(10 ** -rng.uniform(1, 5)),
            })
    return EnrichmentDotInput(df=pd.DataFrame(rows))


DEMOS = {
    "volcano": (volcano, demo_volcano),
    "ma_plot": (ma_plot, demo_ma_plot),
    "heatmap_annotated": (heatmap_annotated, demo_heatmap_annotated),
    "gsea_bubble": (gsea_bubble, demo_gsea_bubble),
    "enrichment_dotplot": (enrichment_dotplot, demo_enrichment_dotplot),
}
