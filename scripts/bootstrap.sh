#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${ROOT_DIR}/.venv"

printf "\n[panelforge] bootstrap starting in %s\n" "${ROOT_DIR}"

if [[ ! -d "${VENV_DIR}" ]]; then
  python3 -m venv "${VENV_DIR}"
fi

"${VENV_DIR}/bin/pip" install --upgrade pip
"${VENV_DIR}/bin/pip" install -r "${ROOT_DIR}/requirements.txt"
"${VENV_DIR}/bin/pip" install -e "${ROOT_DIR}"

printf "[panelforge] bootstrap complete\n"
printf "[panelforge] activate with: source .venv/bin/activate\n"
