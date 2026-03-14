# Contributing to Panelforge

Panelforge is designed to be cloned into active analysis repositories, so changes should keep first-run setup simple, deterministic, and easy to debug.

## Local development

```bash
git clone https://github.com/renatosocodato/figure-multipanel-modes-systems-biology-cytoskeleton-biophysics-computation.git
cd figure-multipanel-modes-systems-biology-cytoskeleton-biophysics-computation
make bootstrap
make smoke
```

## What to update with code changes

- Update `examples/specs/` when behavior or schema expectations change.
- Add or adjust tests under `tests/` for new render paths, chart plugins, and manifests.
- Keep Python and R output contracts aligned: every panel and assembled figure should emit both `pdf` and `png`.
- Preserve the style contract: minimal visual baseline, Arial-first behavior, and tile metadata for each panel.

## Pull requests

- Keep commits focused and easy to review.
- Include the command(s) you used for verification.
- If rendering behavior changes, mention the expected output naming and manifest impact.
- If a new chart family or adapter is introduced, add at least one example spec.
