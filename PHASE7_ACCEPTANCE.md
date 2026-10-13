# Phase 7 — Local acceptance and demonstration

Run this after Phase 6 launches successfully. No further Kaggle training is required.

## Final checks

1. Run `verify_artifacts.py --all-periods` using the same `.venv\Scripts\python.exe`.
   It must reproduce all 49 exported snapshots on CPU and end with ALL CHECKS PASSED.
2. Open each of the six sidebar pages. Confirm none produces a traceback.
3. In Transaction Analyzer, select time 42 and ID 73160850. Run inference twice.
   The score should agree within numerical tolerance and the observed label must remain
   Unknown. Also select a known-label transaction and a below-threshold transaction
   from the real exported CSV; do not relabel predictions as truth.
4. Enter an ID absent from the selected period. The app should explain the mismatch.
5. On Early Warnings, confirm zero frozen test flags. Explore sliders, then turn the
   what-if view off. The frozen count, metrics and downloaded artifacts must be unchanged.
6. Open Suspicious Network. The selected ID is highlighted and the neighbourhood is
   capped. The table shows observed labels separately from model predictions.
7. Check Model Performance against Cell 32. XGBoost AP is about 0.551237 and Temporal
   GNN AP about 0.457683. The frozen thresholds remain 0.81, 0.46, 0.60 and 0.63.
8. Stop the terminal with Ctrl+C, start the app again, and run one inference. It should
   load the same files without retraining.

Save the verified local environment after installation:

```powershell
.\.venv\Scripts\python.exe -m pip freeze > local_environment.txt
```

Keep your app source, original Phase 5 artifact ZIP, saved Kaggle notebook with outputs,
and local environment list together for reproducibility. The artifact manifest checks
integrity relative to your own export; it is not a digital signature or a proof that an
arbitrary downloaded checkpoint is trustworthy.

## Demonstration sequence

1. Dashboard: explain data size, unknown labels and the chronological split.
2. Transaction Analyzer: run a real inference, explain graph context and show the frozen threshold.
3. Future Risk: show period-level changes and explain why the population, rather than a
   persistent transaction, is tracked over time.
4. Early Warnings: show both conditions and explain the genuine zero-warning result.
   Optional what-if exploration must be called exploratory, not a new test result.
5. Suspicious Network: inspect real edges and distinguish a high model score from a known illicit label.
6. Model Performance: show baseline comparisons, confusion matrices and the small history effect.

## Evidence for the final report and presentation

Capture one screenshot of each page after loading the real artifacts, plus the successful
verification terminal output. Include the Kaggle GPU confirmation and actual training
curves already saved in your notebook/export.

The next submission phase should use these verified screenshots and the actual metric
files for the report, slides and viva preparation. Do not add invented UI screenshots,
invent warning events or claim the temporal model beats XGBoost.

When requesting the next phase, send the verifier output and whether all six pages opened.
If a page failed, send its full traceback and the action that triggered it.
