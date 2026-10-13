"""Run before launching Streamlit; no training or changes to artifacts."""
import argparse
from pathlib import Path

import numpy as np
from sklearn.metrics import (accuracy_score, precision_score, recall_score, f1_score,
                             average_precision_score, roc_auc_score, confusion_matrix)
from project_data import ProjectData, InferenceEngine


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--artifacts', type=Path, default=Path(__file__).resolve().parent / 'artifacts')
    parser.add_argument('--all-periods', action='store_true', help='Check CPU inference on all 49 periods.')
    args = parser.parse_args()
    print('1/3 Checking file fingerprints and table alignment...', flush=True)
    data = ProjectData(args.artifacts)
    print(f'PASS: {len(data.manifest)} files verified; {len(data.transactions):,} transactions.', flush=True)
    print('2/3 Recomputing frozen test metrics...', flush=True)
    y = data.test_predictions.label.to_numpy()
    for row in data.metrics.itertuples():
        scores = data.test_predictions[row.model + '_score'].to_numpy()
        predicted = scores >= data.frozen['thresholds'][row.model]
        metrics = dict(accuracy=accuracy_score(y, predicted),
            precision=precision_score(y, predicted, zero_division=0),
            recall=recall_score(y, predicted, zero_division=0),
            f1=f1_score(y, predicted, zero_division=0),
            average_precision=average_precision_score(y, scores), roc_auc=roc_auc_score(y, scores))
        for name, value in metrics.items():
            np.testing.assert_allclose(value, getattr(row, name), rtol=1e-5, atol=1e-6,
                                       err_msg=f'{row.model}: {name}')
        np.testing.assert_array_equal(confusion_matrix(y, predicted, labels=[0, 1]), data.confusions[row.model])
        print(f'PASS: {row.model} test metrics match.', flush=True)
    print('3/3 Running actual CPU model inference...', flush=True)
    engine = InferenceEngine(data)
    periods = range(1, 50) if args.all_periods else [1, 35, 42, 49]
    for period in periods:
        scores, _, difference = engine.predict_period(period)
        print(f'PASS: period {period}, {len(scores):,} nodes, max difference {difference:.3g}', flush=True)
    print('ALL CHECKS PASSED. Ready to run Streamlit.', flush=True)


if __name__ == '__main__':
    main()
