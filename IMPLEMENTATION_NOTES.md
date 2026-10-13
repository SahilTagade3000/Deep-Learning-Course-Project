# Understanding and presenting this implementation

The project is an academic prototype for temporal graph-based illicit transaction
detection and population risk monitoring. The saved experiment is the source of every
result shown in the app. No example scores or generated transactions are substituted.

## How a prediction is produced

Each transaction is a node with 165 numerical features. Original edges connect
transactions in the same time step. Two GCN layers mix neighbourhood information into
a 64-dimensional node representation. The mean of those node representations summarizes
the current graph. A GRU combines that summary with the previous graph's hidden state.
Each node's representation is concatenated with the updated graph context, and the
classifier produces licit/illicit logits. Softmax gives the displayed illicit-class score.

The GRU represents **population-level history**, not a transaction that persists across
49 periods. The dataset has no cross-period transaction edges. The model sees the current
snapshot before scoring it, so these are out-of-time predictions on observed later
graphs, not forecasts of unseen future events.

The GCN uses deduplicated undirected edges. The network page displays original directed
edges. It is a small visual subset; the analyzer still uses the complete snapshot.

## What the weights are

Weights are the numerical parameters learned by the GCN, GRU and classifier during
gradient-based training. The `.pth` file stores their state dictionary. The local app
constructs the same architecture and loads those parameters with `strict=True`.
It switches the model to evaluation mode and disables gradient tracking. There is no
training in Streamlit.

The `memory_before` array contains the graph context produced by the frozen model on
earlier snapshots. For period 42, the app restores context from periods 1–41, then runs
the model on period 42. It copies this context for each inference call, so repeatedly
clicking Analyze does not advance or contaminate history. These contexts must remain
with their matching checkpoint, scaler and feature ordering.

## Labels and evaluation

Original class `1` means illicit (target 1); original class `2` means licit (target 0).
`unknown` maps to -1 and is never a negative supervised example. Unknown nodes remain
available as graph context and are scored, but they are excluded from loss and metrics.

The chronological split is train 1–34, validation 35–41, test 42–49. Scaling was fitted
on training-period features only. Class weights come from known training labels.
Checkpoints were selected by validation Average Precision, and decision thresholds by
validation F1. The 50-epoch review used the same maximum budget for all neural models.
GCN was selected at epoch 48; both temporal and reset-history models at epoch 50.
Reaching the epoch limit does not establish convergence.

Static GCN and temporal training use different optimizer update schedules: one update
per snapshot for GCN, and one per four-snapshot truncated-backpropagation chunk for the
temporal model. Equal epochs therefore do not imply identical optimizer-step counts.

Average Precision summarizes positive-class ranking and is not trapezoidal PR-AUC.
F1 balances precision and recall at the frozen threshold. Accuracy alone is weak evidence
because only 408 of the 8,841 labelled test transactions are illicit (about 4.61%).
An always-licit classifier would already reach about 95.39% accuracy while detecting no
illicit transactions.

## What your measured test results support

These rounded figures are transcribed from your Phase 5 outputs for discussion only;
the application reads full-precision values from your export.

| Model | Average Precision | F1 | Illicit recall |
|---|---:|---:|---:|
| XGBoost | 0.551237 | 0.609105 | 0.475490 |
| GCN | 0.475542 | 0.487370 | 0.401961 |
| Temporal GNN | 0.457683 | 0.492980 | 0.387255 |
| Reset-history control | 0.455205 | 0.489600 | 0.375000 |

XGBoost is strongest on these test metrics. Temporal GNN has slightly higher F1 but
lower AP than static GCN. Its AP advantage over the reset-history control is about
0.00248, which is small. One seed does not establish a statistically reliable advantage.
The validation-to-test decline is a generalization gap; these figures alone do not prove
a particular cause such as concept drift.

This is still a valid project: it implements and evaluates the hypothesis rather than
guaranteeing that the more complex model wins. Do not change thresholds or train again
to improve these already-observed test results while calling them an untouched test.

## How the warnings work

Population risk is the average model score across all transactions in a snapshot.
Escalation is the change from the previous snapshot. The frozen rule requires both:

- Mean score at least 0.21321828067302703.
- Increase at least 0.03071744441986084.

These thresholds were derived from validation periods before test evaluation. All test
means remain below the level threshold, so the correct test warning count is zero.
Periods 44 and 46 have sizable increases but still fail the level condition. Individual
high scores and known illicit transactions can coexist with zero population flags.

Weighted training makes score calibration particularly important; it was not established
in this experiment. Call the output an uncalibrated score rather than a real-world crime
probability. No labelled advance-warning events or lead-time evaluation were supplied,
so the warning module is an experimental review rule rather than validated early detection.

## Make the project your own through understanding

Read the small modules and trace one real transaction through the graph, model and UI.
Use your own explanation of the design decisions and the limitations. Add your name and
course details where appropriate, and follow your institution's disclosure requirements
for coding assistance. Do not claim improvements or independent work that you cannot
demonstrate. The genuine dataset, measured results and an explanation you understand
matter more than generic presentation language.
