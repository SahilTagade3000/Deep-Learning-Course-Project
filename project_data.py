"""Load one frozen Kaggle export and reproduce its CPU inference path."""
import hashlib
import json
from pathlib import Path
from threading import Lock

import numpy as np
import pandas as pd

from analytics import snapshot_bounds, warning_flags

REQUIRED = (
    'artifact_manifest.json', 'frozen_evaluation.json', 'model_config.json',
    'preprocessing_config.json', 'project_summary.json', 'scaler.pkl',
    'temporal_gnn_weights.pth', 'inference_data.npz',
    'transaction_predictions.csv', 'risk_trajectory.csv', 'test_metrics.csv',
    'test_model_predictions.csv', 'test_period_metrics.csv',
    'test_confusion_matrices.json', 'phase4_validation_metrics.csv',
    'gcn_history.csv', 'temporal_gnn_history.csv', 'reset_history_history.csv',
    'xgboost_history.csv',
)


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def verify_manifest(root):
    root = Path(root).resolve()
    missing = [name for name in REQUIRED if not (root / name).is_file()]
    if missing:
        raise FileNotFoundError('Missing artifact files: ' + ', '.join(missing))
    manifest = read_json(root / 'artifact_manifest.json')
    require(set(REQUIRED) - {'artifact_manifest.json'} <= set(manifest),
            'The manifest does not cover all required files.')
    for name, entry in manifest.items():
        require(Path(name).name == name and '/' not in name and '\\' not in name,
                'The manifest must contain plain filenames.')
        path = root / name
        require(path.is_file(), f'Manifest file missing: {name}')
        require(path.stat().st_size == entry['bytes'], f'File size mismatch: {name}')
        require(sha256(path) == entry['sha256'], f'File fingerprint mismatch: {name}')
    frozen = read_json(root / 'frozen_evaluation.json')
    for name, digest in frozen['checkpoint_sha256'].items():
        require(name in manifest and manifest[name]['sha256'] == digest,
                f'Checkpoint differs from the frozen experiment: {name}')
    return manifest


class ProjectData:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.manifest = verify_manifest(self.root)
        self.config = read_json(self.root / 'model_config.json')
        self.frozen = read_json(self.root / 'frozen_evaluation.json')
        self.summary = read_json(self.root / 'project_summary.json')
        self.transactions = pd.read_csv(self.root / 'transaction_predictions.csv',
                                        dtype={'txId': 'int64', 'class': str})
        self.risk = pd.read_csv(self.root / 'risk_trajectory.csv')
        self.metrics = pd.read_csv(self.root / 'test_metrics.csv')
        self.test_predictions = pd.read_csv(self.root / 'test_model_predictions.csv')
        self.period_metrics = pd.read_csv(self.root / 'test_period_metrics.csv')
        self.validation = pd.read_csv(self.root / 'phase4_validation_metrics.csv')
        self.confusions = read_json(self.root / 'test_confusion_matrices.json')
        self.threshold = float(self.frozen['thresholds']['Temporal GNN'])
        self._arrays = None
        self._array_lock = Lock()
        self.validate_tables()

    def validate_tables(self):
        tx = self.transactions
        require(len(tx) == self.summary['dataset_transactions'], 'Transaction count mismatch.')
        require(not tx.txId.duplicated().any(), 'Duplicate transaction IDs.')
        require(tx[['txId', 'time_step', 'label', 'temporal_score']].notna().all().all(),
                'Missing transaction values.')
        require(tx[['time_step', 'txId']].equals(
            tx.sort_values(['time_step', 'txId'])[['time_step', 'txId']]),
            'Transactions must remain in exported time/ID order.')
        require(set(tx.time_step) == set(range(1, 50)), 'Expected time steps 1 through 49.')
        require(tx.label.isin([-1, 0, 1]).all(), 'Invalid labels.')
        mapped = tx['class'].map({'1': 1, '2': 0, 'unknown': -1})
        np.testing.assert_array_equal(mapped, tx.label)
        require(np.isfinite(tx.temporal_score).all() and tx.temporal_score.between(0, 1).all(),
                'Invalid model scores.')
        require(np.isclose(self.threshold, self.config['threshold']), 'Threshold mismatch.')
        np.testing.assert_array_equal(tx.predicted_class, (tx.temporal_score >= self.threshold).astype(int))
        expected_split = np.where(tx.time_step <= 34, 'train_in_sample',
                                  np.where(tx.time_step <= 41, 'validation', 'test'))
        np.testing.assert_array_equal(tx.split, expected_split)
        known_test = tx[(tx.split == 'test') & (tx.label >= 0)]
        require(len(known_test) == self.summary['labelled_test_transactions'], 'Test count mismatch.')
        np.testing.assert_array_equal(known_test.txId, self.test_predictions.txId)
        np.testing.assert_array_equal(known_test.label, self.test_predictions.label)
        np.testing.assert_array_equal(known_test.time_step, self.test_predictions.time_step)
        np.testing.assert_allclose(known_test.temporal_score,
                                  self.test_predictions['Temporal GNN_score'], rtol=1e-5, atol=1e-6)
        require(set(self.metrics.model) == set(self.frozen['thresholds']), 'Model table mismatch.')
        require(self.metrics.model.is_unique, 'Duplicate model rows.')
        require((self.metrics.split == 'test').all(), 'Expected test metrics.')
        for row in self.metrics.itertuples():
            require(row.n == len(known_test) and row.illicit == int(known_test.label.sum()),
                    f'Evaluation counts differ for {row.model}.')
            require(np.isclose(row.threshold, self.frozen['thresholds'][row.model]),
                    f'Threshold differs for {row.model}.')
        require(self.risk.time_step.tolist() == list(range(1, 50)), 'Risk periods are misaligned.')
        recomputed = tx.groupby('time_step').temporal_score.mean().to_numpy()
        np.testing.assert_allclose(self.risk.mean_score, recomputed, rtol=1e-5, atol=1e-6)
        np.testing.assert_allclose(self.risk.previous_risk, self.risk.mean_score.shift(1),
                                  rtol=1e-5, atol=1e-6, equal_nan=True)
        np.testing.assert_allclose(self.risk.risk_change,
                                  self.risk.mean_score - self.risk.previous_risk,
                                  rtol=1e-5, atol=1e-6, equal_nan=True)
        # Explicit parsing avoids bool('False') evaluating to True.
        flags = self.risk.early_warning.astype(str).str.lower().map({'true': True, 'false': False})
        require(flags.notna().all(), 'Invalid warning flags.')
        self.risk['early_warning'] = flags.astype(bool)
        rule = self.frozen['warning_parameters']
        np.testing.assert_array_equal(self.risk.early_warning,
            warning_flags(self.risk, rule['risk_threshold'], rule['escalation_threshold']))
        require(int(self.risk.loc[self.risk.time_step >= 42, 'early_warning'].sum()) ==
                self.summary['test_warning_periods'], 'Warning summary mismatch.')

    def arrays(self):
        with self._array_lock:
            if self._arrays is None:
                with np.load(self.root / 'inference_data.npz', allow_pickle=False) as bundle:
                    arrays = {key: bundle[key] for key in
                              ['raw_features', 'source_indices', 'target_indices', 'memory_before']}
                n = len(self.transactions)
                require(arrays['raw_features'].shape == (n, self.config['input_dim']), 'Feature shape mismatch.')
                require(arrays['memory_before'].shape == (49, self.config['hidden_dim']), 'Memory shape mismatch.')
                for key in ['raw_features', 'memory_before']:
                    require(np.isfinite(arrays[key]).all(), f'Nonfinite values in {key}.')
                source, target = arrays['source_indices'], arrays['target_indices']
                require(source.ndim == target.ndim == 1 and source.shape == target.shape,
                        'Invalid edge arrays.')
                for endpoints in [source, target]:
                    require(np.issubdtype(endpoints.dtype, np.integer) and
                            ((endpoints >= 0) & (endpoints < n)).all(), 'Invalid edge endpoints.')
                times = self.transactions.time_step.to_numpy()
                np.testing.assert_array_equal(times[source], times[target])
                self._arrays = arrays
            return self._arrays


class InferenceEngine:
    def __init__(self, data):
        import joblib
        import torch
        from model import TemporalGNN
        self.data = data
        self.lock = Lock()
        torch.set_num_threads(2)
        cfg = data.config
        self.model = TemporalGNN(cfg['input_dim'], cfg['hidden_dim'], cfg['dropout'])
        weights = torch.load(data.root / 'temporal_gnn_weights.pth', map_location='cpu', weights_only=True)
        self.model.load_state_dict(weights, strict=True)
        self.model.eval()
        # Load only the scaler from your own verified Kaggle export.
        self.scaler = joblib.load(data.root / 'scaler.pkl')
        require(self.scaler.n_features_in_ == cfg['input_dim'], 'Scaler feature count mismatch.')

    def predict_period(self, period):
        import torch
        from torch_geometric.utils import to_undirected
        with self.lock, torch.inference_mode():
            data = self.data
            arrays = data.arrays()
            start, stop = snapshot_bounds(data.transactions.time_step.to_numpy(), int(period))
            source, target = arrays['source_indices'], arrays['target_indices']
            mask = (source >= start) & (source < stop)
            edges = torch.from_numpy(np.stack([source[mask] - start, target[mask] - start]))
            edges = to_undirected(edges, num_nodes=stop - start)
            features = self.scaler.transform(arrays['raw_features'][start:stop]).astype(np.float32)
            context = torch.from_numpy(arrays['memory_before'][period - 1:period].copy())
            logits, _ = self.model(torch.from_numpy(features), edges, context)
            scores = logits.softmax(dim=1)[:, 1].cpu().numpy()
            reference = data.transactions.temporal_score.to_numpy()[start:stop]
            np.testing.assert_allclose(scores, reference, rtol=1e-4, atol=1e-5,
                                       err_msg='Local inference differs from the frozen Kaggle export.')
            return scores, start, float(np.max(np.abs(scores - reference)))
