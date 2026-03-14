#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_BIN="${ROOT_DIR}/.venv/bin"
OUT_DIR="${ROOT_DIR}/outputs/smoke"

if [[ ! -x "${VENV_BIN}/panelforge" ]]; then
  "${ROOT_DIR}/scripts/bootstrap.sh"
fi

rm -rf "${OUT_DIR}"
mkdir -p "${OUT_DIR}"

printf "\n[panelforge] python smoke render\n"
"${VENV_BIN}/panelforge" render "${ROOT_DIR}/examples/specs/single_panel.yaml" --out "${OUT_DIR}/single"
"${VENV_BIN}/panelforge" render "${ROOT_DIR}/examples/specs/four_panel.yaml" --out "${OUT_DIR}/four"
test -f "${OUT_DIR}/single/single_panel_hist.pdf"
test -f "${OUT_DIR}/single/single_panel_hist.png"
test -f "${OUT_DIR}/single/single_panel.pdf"
test -f "${OUT_DIR}/single/single_panel.png"
test -f "${OUT_DIR}/single/run_manifest.json"
test -f "${OUT_DIR}/four/phase_panel_A.pdf"
test -f "${OUT_DIR}/four/phase_panel_A.png"
test -f "${OUT_DIR}/four/four_panel.pdf"
test -f "${OUT_DIR}/four/four_panel.png"
test -f "${OUT_DIR}/four/run_manifest.json"

printf "[panelforge] python tests\n"
"${VENV_BIN}/pytest" -q

if command -v Rscript >/dev/null 2>&1; then
  printf "[panelforge] R smoke render\n"
  Rscript "${ROOT_DIR}/R/panel_renderer.R" "${ROOT_DIR}/examples/specs/single_panel.yaml" "${OUT_DIR}/r-single"
  test -f "${OUT_DIR}/r-single/single_panel_hist.pdf"
  test -f "${OUT_DIR}/r-single/single_panel_hist.png"
  test -f "${OUT_DIR}/r-single/single_panel.pdf"
  test -f "${OUT_DIR}/r-single/single_panel.png"
else
  printf "[panelforge] Rscript not found, skipping R smoke render\n"
fi

printf "[panelforge] smoke checks complete\n"
