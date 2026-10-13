# Redesign verification

## Final package acceptance — 26 September 2026

The final installer was exercised against an isolated copy of the actual existing
project. It installed all 17 presentation/support files, then completed dependency
checks, all 49 CPU inference checks and the six-page Streamlit acceptance test.
The result was `FINAL PACKAGE ACCEPTANCE PASSED`.

Separate installer checks passed for incomplete-project rejection, Windows paths with
spaces, Python environment selection, repeated installation without unnecessary changes,
backup of an older UI file, and preservation of every existing backend/artifact file.
The user's D: project was read for this work; this final upgrade has not yet been
installed there. INSTALL_UI.cmd performs that step when the user runs it.

The final package pins the tested Streamlit 1.64.0 and Plotly 6.9.0 versions.

Checks were run against the actual artifacts in the user's existing project. No
synthetic model outputs were used for application-page testing.

## Passed checks

- Verified all 44 manifest-listed artifact files and frozen checkpoint fingerprints.
- Recomputed all four models' test metrics and confusion matrices from saved predictions.
- Ran the unchanged Temporal GNN on CPU for **all 49 snapshots** and compared every
  output with the exported Kaggle scores. All checks passed. Largest reported absolute
  difference was approximately **8.03 × 10^-7**.
- Ran Streamlit AppTest for each of the six new pages without view errors or exceptions.
- Verified the final monitoring cursor shows 36,824 replayed test transactions,
  1,578 above-threshold transaction predictions and zero frozen escalation flags.
- Clicked Analyze in the redesigned Transaction Intelligence page and completed an
  actual saved-model CPU prediction with the existing verification check.
- Tested invalid transaction-reference handling.
- Tested all four models' evaluation/history selection.
- Tested alternative warning thresholds while the original frozen alert list stayed empty.
- Tested replay interval behavior, Start, Pause, Reset, one-period advancement, sidebar
  synchronization and stopping at period 49.
- Tested presentation-band boundary behavior.
- Confirmed that the frozen rule has ten triggers in training periods and zero in
  held-out test periods; historical examples are labelled separately in the UI.

The comprehensive application tests completed with `ALL REDESIGN APP TESTS PASSED`;
the final packaged application's checks completed with `ALL UI CHECKS PASSED`.

## Test environment

Windows, isolated workspace environment; the user's installed project environment was
not changed during testing.

| Dependency | Tested version |
|---|---|
| Python | 3.12.14 |
| PyTorch | 2.10.0+cpu |
| PyTorch Geometric | 2.8.0.post1 |
| NumPy | 2.0.2 |
| pandas | 2.3.3 |
| scikit-learn | 1.6.1 |
| Streamlit | 1.64.0 |
| Plotly | 6.9.0 |

The user's working Python 3.11 environment remains the intended installation target;
it was not directly used by the test runner. Only presentation dependencies need adding.

## Remaining visual acceptance

A local Streamlit server started successfully. Browser automation had no available
browser, so a screenshot-based layout review and real-browser timer interaction could
not be completed in this session. Automated Streamlit rendering/state tests passed,
but they are not a substitute for checking spacing, charts and responsive layout in
the user's browser. Follow the short page-by-page sequence in START_HERE.md.

The original app.py and all training/inference artifacts remain unchanged. The upgrade
ZIP contains only new presentation files; it contains no trained data or replacement
model implementation.
