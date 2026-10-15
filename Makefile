# Amoxcalli · comandos de desarrollo. Solo biblioteca estándar de Python; Node.js para la suite DOM.
PYTHON ?= python3
PORT ?= 8766

.PHONY: help test test-py test-ui check reports reports-model data derived demo

help:
	@echo "make test        Suite Python + suite DOM (requiere: npm ci --ignore-scripts)"
	@echo "make check       Comprueba que los informes medidos siguen vigentes (sin escribir)"
	@echo "make reports     Regenera los informes medidos de reports/ (sin modelo ni red)"
	@echo "make demo        Prepara los análisis derivados y sirve en http://127.0.0.1:$(PORT)"

test: test-py test-ui

test-py: data
	$(PYTHON) -m unittest discover -s tests

# Presentación: se verifica aquí, no con hashes en reports/.
test-ui: node_modules
	$(PYTHON) scripts/test-platform-ui.py
	$(PYTHON) scripts/test-community-ui.py
	$(PYTHON) scripts/test-reading-continuity.py
	$(PYTHON) scripts/test-reading-documentary.py
	node tests/pwa_worker.cjs

node_modules: package-lock.json
	npm ci --ignore-scripts
	@touch node_modules

# Compuertas: solo entradas medidas (ranking, datos, batería, evaluador).
check:
	$(PYTHON) -m nahuatl_local.documentary_evaluation --check
	$(PYTHON) -m nahuatl_local.documentary_retrieval_evaluation --check
	$(PYTHON) -m nahuatl_local.documentary_laboratory --check

# Orden: batería → recuperación medida → comparación del Laboratorio → evaluaciones de Preguntar y morfología.
# glyph_linker escribe el lote en un temporal: aquí solo se regenera su informe de cobertura.
reports:
	$(PYTHON) -m nahuatl_local.documentary_evaluation
	$(PYTHON) -m nahuatl_local.documentary_retrieval_evaluation
	$(PYTHON) -m nahuatl_local.documentary_laboratory
	$(PYTHON) -m nahuatl_local.evidence_evaluation
	$(PYTHON) -m nahuatl_local.morphology_evaluation
	$(PYTHON) -m nahuatl_local.glyph_linker --output "$$(mktemp -d)/glyph-associations.json"

# Requiere requirements.txt, data/prepared/ y los pesos (models/base, outputs/): ver MODEL_CARD.md.
reports-model:
	$(PYTHON) -m nahuatl_local.benchmark --retrieval-only --split validation --output reports/benchmark-retrieval-validation-current-full.json
	$(PYTHON) scripts/check-local-model.py

# Preparación del corpus clásico (byte a byte reproducible desde corpus/axolotl/axolotl.csv).
# Solo si falta: no sobrescribe una preparación local (p. ej. con estadísticas del tokenizador).
data:
	@test -f data/prepared/train.jsonl || $(PYTHON) -m nahuatl_local.data > /dev/null

derived:
	$(PYTHON) -c "from nahuatl_local.stems import WordStudy; WordStudy()._build()"

demo: derived
	bash scripts/amoxcalli.sh serve --port $(PORT)
