"""Embedding recipes for UMAP / t-SNE / PCA outputs.

Contains:
    umap_scatter           — categorical or continuous coloring with optional contours
    pca_biplot             — scores + loadings arrows
    trajectory_overlay     — pseudotime arrows on an embedding
"""
from __future__ import annotations

import numpy as np
from matplotlib import colormaps

from ..core.contract import PCABiplotInput, TrajectoryOverlayInput, UMAPInput
from ..core.palette import get_palette
from ..core.primitives import callout_box, halo_text, iter_palette


def umap_scatter(ax, contract, palette: str = "okabe_ito"):
    """Scatter of a 2D embedding with categorical or continuous coloring."""

    c = UMAPInput.model_validate(contract)
    emb = np.asarray(c.embedding)
    if emb.ndim != 2 or emb.shape[1] != 2:
        raise ValueError("embedding must be (n, 2)")
    x, y = emb[:, 0], emb[:, 1]
    if c.color_col and c.color_col in c.metadata.columns:
        vals = c.metadata[c.color_col]
        if c.continuous:
            cm = colormaps.get_cmap(get_palette(palette).continuous)
            sc = ax.scatter(x, y, s=6, c=vals.astype(float), cmap=cm,
                            alpha=0.85, linewidth=0)
            ax.figure.colorbar(sc, ax=ax, shrink=0.85, pad=0.02,
                               label=c.color_col)
        else:
            pal = iter_palette(get_palette(palette).categorical, 12)
            levels = list(vals.dropna().unique())
            for i, lvl in enumerate(levels):
                mask = vals == lvl
                ax.scatter(x[mask], y[mask], s=6, color=pal[i % len(pal)],
                           alpha=0.85, linewidth=0, label=str(lvl))
            ax.legend(fontsize=7, frameon=False, markerscale=1.3)
    else:
        ax.scatter(x, y, s=6, color=get_palette(palette).categorical[0],
                   alpha=0.7, linewidth=0)
    if c.density_contours and len(x) >= 3 and float(np.ptp(x)) > 0 and float(np.ptp(y)) > 0:
        from scipy.stats import gaussian_kde

        try:
            kde = gaussian_kde(np.vstack([x, y]))
        except (np.linalg.LinAlgError, ValueError):
            # Zero-variance / singular-covariance embedding — skip contours.
            kde = None
        if kde is not None:
            xgrid = np.linspace(x.min(), x.max(), 80)
            ygrid = np.linspace(y.min(), y.max(), 80)
            XX, YY = np.meshgrid(xgrid, ygrid)
            ZZ = kde(np.vstack([XX.ravel(), YY.ravel()])).reshape(XX.shape)
            ax.contour(XX, YY, ZZ, levels=5, colors="#455A64",
                       linewidths=0.6, alpha=0.6)
    if c.highlight_ids:
        # Match against whichever column actually carries IDs in the caller's
        # metadata — the DataFrame index by default (typical for single-cell
        # adata.obs-style tables), falling back to an explicit ``id`` column.
        wanted = set(c.highlight_ids)
        meta = c.metadata
        if "id" in meta.columns:
            id_series = meta["id"]
        else:
            id_series = meta.index.to_series()
        mask = id_series.isin(wanted).to_numpy()
        matches = np.flatnonzero(mask)
        if matches.size:
            ax.scatter(x[matches], y[matches], s=25, facecolor="none",
                       edgecolor="#111", linewidth=1.0)
    ax.set_xlabel("UMAP-1"); ax.set_ylabel("UMAP-2")
    ax.set_xticks([]); ax.set_yticks([])
    return ax


def demo_umap_scatter() -> UMAPInput:
    import pandas as pd
    rng = np.random.default_rng(50)
    n = 300
    centers = np.array([[0, 0], [3, 1], [-1, 3]])
    labels = rng.integers(0, 3, size=n)
    emb = centers[labels] + rng.normal(0, 0.6, size=(n, 2))
    meta = pd.DataFrame({"cluster": labels.astype(str),
                         "score": rng.uniform(0, 1, size=n)})
    return UMAPInput(embedding=emb, metadata=meta, color_col="cluster",
                     continuous=False, density_contours=True)


def pca_biplot(ax, contract, palette: str = "okabe_ito"):
    """PCA scores scatter with feature-loading arrows."""

    c = PCABiplotInput.model_validate(contract)
    scores = np.asarray(c.scores); loadings = np.asarray(c.loadings)
    pal = iter_palette(get_palette(palette).categorical, 3)
    ax.scatter(scores[:, 0], scores[:, 1], s=8, color=pal[0], alpha=0.7, linewidth=0)
    arrow_scale = 0.7 * max(np.abs(scores).max(), 1e-9) / max(np.abs(loadings).max(), 1e-9)
    for i, name in enumerate(c.feature_names):
        dx, dy = loadings[i, 0] * arrow_scale, loadings[i, 1] * arrow_scale
        ax.annotate("", xy=(dx, dy), xytext=(0, 0),
                    arrowprops=dict(arrowstyle="-|>", color="#111", lw=0.8))
        halo_text(ax, dx, dy, name, color="#111", fontsize=7,
                  fontweight="regular", ha="left", va="bottom")
    ax.axhline(0.0, color="#B0BEC5", linewidth=0.5, linestyle="--")
    ax.axvline(0.0, color="#B0BEC5", linewidth=0.5, linestyle="--")
    ax.set_xlabel("PC1"); ax.set_ylabel("PC2")
    return ax


def demo_pca_biplot() -> PCABiplotInput:
    rng = np.random.default_rng(51)
    scores = rng.normal(0, 1, size=(120, 2))
    loadings = rng.normal(0, 0.5, size=(5, 2))
    names = [f"feat{i}" for i in range(5)]
    return PCABiplotInput(scores=scores, loadings=loadings, feature_names=names)


def trajectory_overlay(ax, contract, palette: str = "timepoint_gradient"):
    """Embedding scatter with pseudotime coloring + quiver toward next neighbour."""

    c = TrajectoryOverlayInput.model_validate(contract)
    emb = np.asarray(c.embedding); pt = np.asarray(c.pseudotime)
    pal = get_palette(palette)
    cm = colormaps.get_cmap(pal.continuous)
    ax.scatter(emb[:, 0], emb[:, 1], c=pt, cmap=cm, s=10, linewidth=0, alpha=0.85)
    # Quiver toward next-pseudotime neighbour of each point. We use adjacent
    # pairs in sorted pseudotime order (src -> dst) instead of wrapping, so
    # the terminal point does not generate a spurious long arrow back to the
    # start — pseudotime is not cyclic by default.
    order = np.argsort(pt)
    if len(order) >= 2:
        src = order[:-1]
        dst = order[1:]
        dx = emb[dst, 0] - emb[src, 0]
        dy = emb[dst, 1] - emb[src, 1]
        step = max(1, len(src) // 40)
        ax.quiver(emb[src[::step], 0], emb[src[::step], 1],
                  dx[::step], dy[::step], angles="xy", scale_units="xy", scale=1.0,
                  color="#111", width=0.003, alpha=0.6)
    ax.set_xticks([]); ax.set_yticks([])
    callout_box(ax, 0.02, 0.96, "pseudotime →", ha="left", va="top",
                color="#333333")
    return ax


def demo_trajectory_overlay() -> TrajectoryOverlayInput:
    rng = np.random.default_rng(52)
    t = np.linspace(0, 1, 200)
    emb = np.column_stack([np.cos(2 * np.pi * t) + rng.normal(0, 0.05, size=t.size),
                           np.sin(2 * np.pi * t) + rng.normal(0, 0.05, size=t.size)])
    return TrajectoryOverlayInput(embedding=emb, pseudotime=t)


DEMOS = {
    "umap_scatter": (umap_scatter, demo_umap_scatter),
    "pca_biplot": (pca_biplot, demo_pca_biplot),
    "trajectory_overlay": (trajectory_overlay, demo_trajectory_overlay),
}
