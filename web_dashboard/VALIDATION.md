# Validation of the separate web dashboard

Validated on 6 October 2026 against the actual project at:

`D:\III_TY All Sub\DL\DL_CP\Temporal_GNN_Streamlit`

## Completed checks

`check_web.py` completed **100 checks** using FastAPI's HTTP test client and the actual original project modules and Phase 5 artifacts.

- All eight replay dashboards matched `DataAdapter.dashboard` exactly.
- Full held-out coverage: 36,824 transactions; 1,578 high-risk predictions; zero frozen escalation flags.
- Fresh CPU inference for TX-73160850 matched the saved Kaggle score. Maximum difference across its complete period-42 snapshot: approximately **3.23e-07**.
- Selected transaction features, recorded label, filtered searches and pagination matched the actual tables.
- Displayed network edges matched the original directed edge set; full-neighbourhood statistics and the view's 31-node maximum were checked.
- Period visibility excluded future test transactions relative to the replay cursor.
- All 49 population observations were readable; missing period-1 history was serialized as JSON null.
- Frozen test warnings remained zero while exploratory conditions could trigger independently.
- Actual earlier-period triggers matched periods 9, 11, 13, 17, 19, 20, 24, 25, 30 and 34.
- All four models' AP values and confusion matrices were recomputed from saved labelled test predictions; PR/ROC curve endpoints and recorded histories loaded successfully.
- Invalid periods, references, filters and threshold parameters returned appropriate errors.
- The static frontend and bundled Plotly resource were reachable; the original checkpoint was not exposed as a downloadable route.
- Streamlit was absent from the test process's imported modules.
- SHA-256 fingerprints of existing source, documentation, launch scripts and artifacts were identical before and after the checks.

The launcher also started successfully on localhost port 8060 and served the actual full-test overview through HTTP. Python and frontend JavaScript syntax checks passed.

## Environment

Tests used a separate workspace environment with Python 3.12.14, CPU PyTorch 2.10.0, PyG 2.8.0.post1, NumPy 2.0.2, pandas 2.3.3 and scikit-learn 1.6.1. The web dependencies were FastAPI 0.142.2, Uvicorn 0.54.0 and HTTPX 0.28.1. The user's original environment was not altered. The installation guide uses the user's existing working Python environment.

The charts bundle is Plotly.js 3.7.0, distributed with its MIT notice. The website requires no external fonts or chart CDN after setup.

## Remaining visual review

Browser automation was stopped with Escape during development. A complete real-browser review of layout, all interactions, responsive widths and both themes was therefore **not completed**. Responsive CSS and frontend controls are implemented, but syntax and HTTP checks do not establish visual correctness. Open the Command Center first to approve its appearance, then use the demonstration steps in READ_ME_FIRST.md to review all six pages.

This report confirms the checks listed above; it does not guarantee that every possible laptop configuration or browser condition will be error-free.
