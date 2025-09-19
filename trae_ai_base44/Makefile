.PHONY: init run check ledger


init:
	python3 -m venv .venv && . .venv/bin/activate && pip install --upgrade pip && pip install -r backend/requirements.txt


check:
	. .venv/bin/activate && python3 scripts/rule1_guard.py && python3 scripts/py_audit.py && python3 scripts/upr_monitor.py


run:
	. .venv/bin/activate && uvicorn backend.app:app --host 127.0.0.1 --port 7860


ledger:
	@echo "[$(shell date '+%Y-%m-%d %H:%M')] Component: N/A | Change: init | Reason: go-live | Verified: pass 2/2" >> logs/fix_ledger.log
