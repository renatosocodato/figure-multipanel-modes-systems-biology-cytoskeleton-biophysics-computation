.DEFAULT_GOAL := help

PYTHON ?= python3
VENV ?= .venv
PIP := $(VENV)/bin/pip
PANELFORGE := $(VENV)/bin/panelforge
PYTEST := $(VENV)/bin/pytest
OUTPUT_DIR ?= outputs

.PHONY: help bootstrap test inspect discover render-single render-four demo-single demo-four smoke clean

help:
	@printf "\nPanelforge local tasks\n\n"
	@printf "  make bootstrap      Create .venv and install dependencies\n"
	@printf "  make test           Run Python tests\n"
	@printf "  make inspect        Inspect the four-panel example spec\n"
	@printf "  make discover       Scan the default local root for analysis-style repos\n"
	@printf "  make render-single  Render the single-panel example\n"
	@printf "  make render-four    Render the four-panel example\n"
	@printf "  make demo-single    Bootstrap if needed, then render single-panel example\n"
	@printf "  make demo-four      Bootstrap if needed, then render four-panel example\n"
	@printf "  make smoke          Run end-to-end smoke checks for Python and R\n"
	@printf "  make clean          Remove generated outputs\n\n"

bootstrap:
	@./scripts/bootstrap.sh

test:
	@$(PYTEST) -q

inspect:
	@$(PANELFORGE) inspect examples/specs/four_panel.yaml

discover:
	@mkdir -p $(OUTPUT_DIR)
	@$(PANELFORGE) discover --roots /Users/renatosocodato --output $(OUTPUT_DIR)/discovery.json

render-single:
	@mkdir -p $(OUTPUT_DIR)
	@$(PANELFORGE) render examples/specs/single_panel.yaml --out $(OUTPUT_DIR)/single

render-four:
	@mkdir -p $(OUTPUT_DIR)
	@$(PANELFORGE) render examples/specs/four_panel.yaml --out $(OUTPUT_DIR)/four

demo-single:
	@test -x $(PANELFORGE) || ./scripts/bootstrap.sh
	@$(MAKE) render-single

demo-four:
	@test -x $(PANELFORGE) || ./scripts/bootstrap.sh
	@$(MAKE) render-four

smoke:
	@./scripts/run-smoke.sh

clean:
	@rm -rf $(OUTPUT_DIR)
