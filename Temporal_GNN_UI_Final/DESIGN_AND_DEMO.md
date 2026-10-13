# Design decisions and a defensible demonstration

## Presentation architecture

Existing verified artifacts → unchanged model/data loader → DataAdapter → six new views.

The raw model outputs remain the source of truth. Display formatting changes units and
labels without changing scores, class thresholds, preprocessing or evaluation scope.
No personal names, wallet identities, transaction amounts or feature meanings are invented.

## Terminology

| Underlying field | Executive display |
|---|---|
| `txId` | Transaction Reference, with the reversible prefix TX- |
| `time_step` | Monitoring Period |
| `temporal_score` | Transaction risk score / 100 |
| `predicted_class` | Flagged for review / Below review threshold |
| `label = -1` | Recorded label: Unlabelled |
| Unique adjacent nodes | Network Connections |
| Snapshot mean score | Population risk score / 100 |
| Difference in adjacent means | Change in score points |

Scores are uncalibrated. Displaying 87 / 100 is not a claim of an 87% real-world crime
probability. True dataset labels remain distinct from model outputs. A risk indicator is
not a feature attribution or a causal explanation.

## Transaction review bands

The existing binary classification threshold is read from the frozen export (0.60).
Presentation bands are configured separately in `intelligence/config.py`:

- Low: below half the decision threshold, currently score 30 / 100.
- Watch: from 30 up to, but not including, 60.
- High: from 60 up to, but not including, 90.
- Critical: 90 or above.

These labels are conveniences for browsing scores, not new trained classes or official
financial risk standards. The configured critical cutoff is 0.90. The frozen 0.60 model
decision boundary always controls the high-risk transaction count and model metrics.
Do not change exported config files to customize presentation colors or labels.

## Population review levels

The experimental frozen warning rule has two conditions: population mean level and
one-period score increase. The original frozen binary flag still requires **both**.

| Conditions met | Presentation level | Original frozen flag |
|---|---|---|
| Neither | Normal | False |
| Increase only | Watch | False |
| Level only | High | False |
| Both | Critical | True |

The test periods produce zero frozen flags. Watch periods can still appear. Exploratory
sliders compute a separate view and never rewrite model scores, rules or result files.
Historical triggers from periods before 42 are labelled training/validation examples;
they are not counted as held-out successes. These flags do not establish advance warning.

## Replay contract

- Source: complete observed test snapshots and frozen predictions, periods 42–49.
- Start: advance one period after each configured interval; restarting at 49 returns to 42.
- Pause: retain the current cursor and stop automatic advancement.
- Reset: return to period 42, paused.
- Cursor: manual movement pauses the replay.
- Processing speed: seconds per period, not model latency or blockchain throughput.
- Last Update: local UI replay update time, not a blockchain timestamp.
- Replay state, selected reference, thresholds and alert list live in Streamlit session state.
- Counts and queues reflect only test records through the cursor. No randomized records.
- The queue is ranked by model score within the current period; no within-period arrival
  order is claimed because the dataset does not supply that timing here.
- The full benchmark remains separately visible in Model Intelligence.

The timer runs while the Streamlit session is active. Browsers can throttle background
tabs; missed intervals are not presented as measured real-time throughput.

## Demonstration story

1. **Command Center:** “This is a historical transaction-risk monitoring simulation.
   Every changing value comes from our trained model's actual dataset predictions.”
   Start the replay and show counts/trajectory updating. Pause before investigation.
2. **Transaction Intelligence:** choose a real example, run Analyze, show the gauge,
   recorded label and network indicators. The unknown high-score case is not confirmed illicit.
3. **Temporal Risk:** “Now we inspect how the surrounding transaction population's
   score changes across periods.” Do not say the same transaction persists across periods.
4. **Early Warning Center:** explain both frozen conditions and the zero-flag result.
   Show a Watch period or a clearly labelled historical trigger. If using sliders,
   identify them as exploratory and keep the frozen result visible.
5. **Network Investigation:** hover on actual anonymous references and explain the
   directional links and capped view. Connections are not proof of criminal ownership.
6. **Model Intelligence:** show XGBoost's stronger baseline performance, the small
   temporal-versus-reset difference, and the architecture. A working implementation and
   honest comparison are the result; superiority of the temporal model is not claimed.

Open Advanced Model Information for numerical inputs and the CPU/Kaggle prediction
comparison during technical questions. The executive view avoids raw tensor terminology.
