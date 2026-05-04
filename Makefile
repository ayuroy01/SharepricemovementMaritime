.PHONY: install test smoke run run-demo run-live run-auto launch \
        compile lint clean doctor security-check screenshot \
        docker-build docker-run

PY ?= python3
PORT ?= 8501

install:
	$(PY) -m pip install -r requirements.txt

test:
	$(PY) -m pytest -q

compile:
	$(PY) -m py_compile dashboard.py maritime_data.py config.py providers.py \
	  indicators.py signals.py backtest.py demo_data.py route_economics.py \
	  launcher.py scripts/smoke_test.py scripts/doctor.py \
	  scripts/security_check.py SharepricemovementMaritime.py

smoke:
	APP_MODE=demo $(PY) scripts/smoke_test.py

doctor:
	$(PY) scripts/doctor.py

security-check:
	$(PY) scripts/security_check.py

launch:
	$(PY) launcher.py

run:
	$(PY) -m streamlit run dashboard.py --server.port $(PORT)

run-demo:
	APP_MODE=demo $(PY) -m streamlit run dashboard.py --server.port $(PORT)

run-live:
	APP_MODE=live $(PY) -m streamlit run dashboard.py --server.port $(PORT)

run-auto:
	APP_MODE=auto $(PY) -m streamlit run dashboard.py --server.port $(PORT)

screenshot:
	@echo "Manual capture workflow — see docs/screenshots/README.md"
	APP_MODE=demo $(PY) -m streamlit run dashboard.py --server.port $(PORT)

lint:
	@command -v ruff >/dev/null 2>&1 && ruff check . || \
	  echo "ruff not installed; skip ('pip install ruff' to enable)"

clean:
	rm -rf __pycache__ */__pycache__ .pytest_cache .cache .coverage htmlcov

docker-build:
	docker build -t open-maritime-quant:latest .

docker-run:
	docker run --rm -p $(PORT):8501 \
	  -e APP_MODE=$(APP_MODE) \
	  -e NEWSAPI_KEY=$(NEWSAPI_KEY) \
	  open-maritime-quant:latest
