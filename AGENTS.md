# Repository Guidelines

## Project Structure & Module Organization
This repository is a flat Python workspace for stock concept analysis and a small Flask UI. Core scripts live in the root: `app.py` serves the web app, `process_stock_concepts.py` builds `stock_to_concepts.csv` and `concept_to_stocks.csv`, `concept_stock_analyzer.py` queries concept weights, and `stock_knowledge_graph.py` / `multi_stock_correlation_matrix.py` generate graph and correlation outputs. HTML lives in `templates/index.html`. Generated CSV, PNG, TXT, and Excel data files are also stored in the root, so avoid committing regenerated artifacts unless they are intentional fixtures.

## Build, Test, and Development Commands
Use Python 3.10+ in a virtual environment.

```bash
pip install flask pandas openpyxl networkx akshare numpy scipy matplotlib seaborn requests psycopg2 pymysql
python app.py
python process_stock_concepts.py -i 板块涨停_关系型_全量_org.xlsx -o .
python concept_stock_analyzer.py -l
python concept_stock_analyzer.py -c 锂电池 -n 20
python stock_knowledge_graph.py
python multi_stock_correlation_matrix.py -s 301308:江波龙 300475:香农芯创
```

`app.py` starts the Flask server on port `8080`. Most scripts write outputs into the current directory.

## Coding Style & Naming Conventions
Follow PEP 8 with 4-space indentation. Keep module names snake_case, functions lowercase with underscores, and classes in PascalCase such as `StockCorrelationAnalyzer`. Prefer small, script-friendly functions and keep user-facing CLI messages in Chinese to match the existing codebase and datasets. There is no configured formatter or linter, so run a manual readability pass before submitting.

## Testing Guidelines
No automated test suite or coverage gate is checked in today. Validate each change by running the affected script or endpoint and confirming expected CSV, JSON, or PNG outputs. For new reusable logic, add `pytest` tests under `tests/test_<module>.py` and keep sample inputs small.

## Commit & Pull Request Guidelines
This workspace does not include `.git` history, so no local commit convention can be inferred. Use short, imperative, single-purpose commit messages such as `Add concept filter to related stocks API`. PRs should describe the data source used, list changed scripts, include screenshots for `templates/index.html` or API response examples for backend changes, and note any regenerated data artifacts.

## Security & Configuration Tips
Do not commit credentials or fixed hostnames. `update_document_metadata.py` currently contains hardcoded database and API secrets; move them to environment variables before sharing or deploying changes.
