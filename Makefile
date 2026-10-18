# Amoxcalli · comandos de desarrollo. Solo biblioteca estándar de Python; Node.js para la suite DOM.
PYTHON ?= python3
PORT ?= 8766

.PHONY: help test test-py test-ui eval check reports data derived demo

help:
	@echo "make test        Suite Python + suite DOM (requiere: npm ci --ignore-scripts)"
	@echo "make eval        Evaluación única: reports/EVALUACION.md (morfología, términos, Preguntar, fichas)"
	@echo "make check       Vuelve a medir y falla si una cifra cambió sin regenerar (no escribe)"
	@echo "make reports     make eval + informes de cobertura (unidades, glifos)"
	@echo "make demo        Prepara los análisis derivados y sirve en http://127.0.0.1:$(PORT)"

test: test-py test-ui

test-py: data
	$(PYTHON) -m unittest discover -s tests

# Presentación: se verifica aquí, no con hashes en reports/.
test-ui: node_modules data derived
	$(PYTHON) scripts/test-platform-ui.py
	$(PYTHON) scripts/test-community-ui.py
	$(PYTHON) scripts/test-reading-continuity.py
	$(PYTHON) scripts/test-reading-documentary.py
	$(PYTHON) scripts/test-units-ui.py
	$(PYTHON) scripts/test-spelling-ui.py
	$(PYTHON) scripts/test-gods-ui.py
	node tests/pwa_worker.cjs

node_modules: package-lock.json
	npm ci --ignore-scripts
	@touch node_modules

# Una sola evaluación (sin modelo ni red). La batería documental se reconstruye aparte, solo si cambian
# sus datos: python -m nahuatl_local.documentary_evaluation.
eval:
	$(PYTHON) -m nahuatl_local.evaluate_all

# Compuerta: vuelve a medir; solo cuentan las cifras (entradas medidas), no tiempos ni interfaz.
check:
	$(PYTHON) -m nahuatl_local.documentary_evaluation --check
	$(PYTHON) -m nahuatl_local.evaluate_all --check

# glyph_linker escribe el lote en un temporal: aquí solo se regenera su informe de cobertura.
reports: eval
	$(PYTHON) -m nahuatl_local.units
	$(PYTHON) -m nahuatl_local.glyph_linker --output "$$(mktemp -d)/glyph-associations.json"

# El laboratorio del LLM (entrenamiento, banco de pruebas, pesos) está archivado en experiments/llm/.

# Preparación del corpus clásico (byte a byte reproducible desde corpus/axolotl/axolotl.csv).
# Solo si falta: no sobrescribe una preparación local (p. ej. con estadísticas del tokenizador).
data:
	@test -f data/prepared/train.jsonl || $(PYTHON) -m nahuatl_local.data > /dev/null

derived:
	$(PYTHON) -c "from nahuatl_local.stems import WordStudy; WordStudy()._build()"

demo: derived
	bash scripts/amoxcalli.sh serve --port $(PORT)
