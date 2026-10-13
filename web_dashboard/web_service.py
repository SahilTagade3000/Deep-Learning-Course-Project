"""A read-only bridge to the original project modules. No Streamlit imports."""
import importlib
import os
from pathlib import Path
import sys
import time
from threading import Lock

# Keep numerical imports light on Windows laptops, before NumPy initializes.
os.environ.setdefault('OPENBLAS_NUM_THREADS', '1')
os.environ.setdefault('OMP_NUM_THREADS', '2')
os.environ.setdefault('MKL_NUM_THREADS', '2')
sys.dont_write_bytecode = True

import networkx as nx
import numpy as np
import pandas as pd
from sklearn.metrics import precision_recall_curve, roc_curve

LABELS = {-1: 'Unlabelled', 0: 'Licit', 1: 'Illicit'}
MODELS = {'XGBoost': 'xgboost_history.csv', 'GCN': 'gcn_history.csv',
          'Temporal GNN': 'temporal_gnn_history.csv',
          'Reset-history ablation': 'reset_history_history.csv'}


def clean(value):
    """Translate numerical/Pandas objects to strict JSON, including missing period-1 history."""
    if isinstance(value, dict):
        return {str(key): clean(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, np.ndarray)):
        return [clean(item) for item in value]
    if isinstance(value, np.generic):
        return clean(value.item())
    if isinstance(value, float) and not np.isfinite(value):
        return None
    return value


class DashboardService:
    def __init__(self, project):
        self.project_path = Path(project).resolve()
        for filename in ['model.py', 'project_data.py', 'analytics.py',
                         'intelligence/data_adapter.py', 'artifacts/artifact_manifest.json']:
            if not (self.project_path / filename).is_file():
                raise FileNotFoundError(f'Missing {filename} in {self.project_path}. '
                                        'Put web_dashboard inside the original project folder, '
                                        'or correct project.json.')
        sys.path.insert(0, str(self.project_path))
        # Guard against accidentally importing a similarly named installed package.
        for name in ['analytics', 'model', 'project_data', 'intelligence']:
            previous = sys.modules.get(name)
            if previous and not Path(previous.__file__).resolve().is_relative_to(self.project_path):
                raise RuntimeError(f'{name} was loaded from an unrelated folder. Restart the server.')
        module = importlib.import_module('project_data')
        adapter = importlib.import_module('intelligence.data_adapter')
        self.band = adapter.band
        self.reference = adapter.reference
        self.data = module.ProjectData(self.project_path / 'artifacts')
        self.adapter = adapter.DataAdapter(self.data)
        self.engine = None
        self._engine_factory = module.InferenceEngine
        self._engine_lock = Lock()
        self.histories = {name: pd.read_csv(self.data.root / filename)
                          for name, filename in MODELS.items()}

    def record(self, row):
        return clean(dict(id=int(row.txId), reference=self.reference(row.txId),
                          period=int(row.time_step), score=float(row.temporal_score),
                          band=str(self.band(row.temporal_score, self.data.threshold)),
                          label=LABELS[int(row.label)], flagged=bool(row.predicted_class)))

    def selected(self, tx_id, period):
        row = self.adapter.get_transaction(tx_id)
        if not 42 <= int(row.time_step) <= period:
            raise ValueError('This transaction is outside the replayed test periods. '
                             'Advance the monitoring period to view it.')
        return row

    def risk_rows(self, period, history=False):
        frame = self.adapter.risk_periods(period, include_history=history)
        table = self.adapter.period_table(frame)
        levels = table['Review Level'].tolist()
        return clean([dict(period=int(row.time_step), mean=float(row.mean_score),
                           previous=float(row.previous_risk), change=float(row.risk_change),
                           transactions=int(row.total_transactions),
                           high=int(row.high_risk_transactions), warning=bool(row.early_warning),
                           level=levels[i], split=str(row.split))
                      for i, row in enumerate(frame.itertuples())])

    def meta(self):
        return clean(dict(summary=self.data.summary, threshold=self.data.threshold,
                          rule=self.adapter.rule, models=list(MODELS),
                          config=self.data.config, manifest_files=len(self.data.manifest),
                          inference_device='CPU', source='Frozen Kaggle Phase 5 export'))

    def overview(self, period):
        visible = self.adapter.visible(period)
        bands = self.band(visible.temporal_score, self.data.threshold)
        top = visible[visible.time_step == period].nlargest(8, 'temporal_score')
        return clean(dict(kpis=self.adapter.dashboard(period),
                          bands={name: int((bands == name).sum()) for name in ['Low', 'Watch', 'High', 'Critical']},
                          labels={name: int((visible.label == code).sum()) for code, name in LABELS.items()},
                          risk=self.risk_rows(period),
                          queue=[self.record(row) for row in top.itertuples()]))

    def transactions(self, period, query='', risk='All', label='All', offset=0, limit=25):
        frame = self.adapter.visible(period)
        query = query.strip().upper().removeprefix('TX-')
        if query:
            frame = frame[frame.txId.astype(str).str.contains(query, regex=False)]
        if risk != 'All':
            frame = frame[self.band(frame.temporal_score, self.data.threshold) == risk]
        if label != 'All':
            code = next(key for key, name in LABELS.items() if name == label)
            frame = frame[frame.label == code]
        frame = frame.sort_values(['temporal_score', 'txId'], ascending=[False, True])
        cases = self.adapter.demo_cases(period)
        return dict(total=len(frame), offset=offset, limit=limit,
                    rows=[self.record(row) for row in frame.iloc[offset:offset + limit].itertuples()],
                    demos=[dict(name=name, id=tx_id) for name, tx_id in cases.items()])

    def transaction(self, tx_id, period):
        row = self.selected(tx_id, period)
        summary = self.adapter.selected_summary(tx_id)
        graph = summary['graph']
        population = summary['period']
        return clean(dict(record=self.record(row),
                          connections=graph['connections'], incoming=graph['incoming'],
                          outgoing=graph['outgoing'], high_neighbours=graph['high_neighbours'],
                          neighbour_mean=graph['neighbour_mean'],
                          population_change=float(population.risk_change),
                          threshold=self.data.threshold,
                          technical=dict(tx_id=int(tx_id), input_features=self.data.config['input_dim'],
                                         hidden_dimension=self.data.config['hidden_dim'],
                                         raw_features=self.data.arrays()['raw_features'][int(row.name)].tolist())))

    def analyze(self, tx_id, period):
        row = self.selected(tx_id, period)
        started = time.perf_counter()
        # Load the original CPU model once, when analysis is first requested.
        # Other dashboard pages do not need a second model resident in memory.
        with self._engine_lock:
            if self.engine is None:
                self.engine = self._engine_factory(self.data)
        scores, start, difference = self.engine.predict_period(int(row.time_step))
        return dict(id=int(tx_id), period=int(row.time_step), score=float(scores[int(row.name) - start]),
                    exported_score=float(row.temporal_score), snapshot_nodes=len(scores),
                    maximum_snapshot_difference=difference, elapsed_seconds=time.perf_counter() - started,
                    device='CPU', verified=True)

    def network(self, tx_id, period):
        self.selected(tx_id, period)
        graph = self.adapter.network(tx_id)
        nx_graph = nx.DiGraph()
        nx_graph.add_nodes_from(graph['nodes']); nx_graph.add_edges_from(graph['edges'])
        positions = nx.spring_layout(nx_graph, seed=42)
        nodes = []
        for index in graph['nodes']:
            item = self.record(self.data.transactions.iloc[index])
            item.update(x=float(positions[index][0]), y=float(positions[index][1]),
                        selected=index == graph['centre'])
            nodes.append(item)
        return clean(dict(nodes=nodes,
                          edges=[dict(source=int(self.data.transactions.iloc[source].txId),
                                      target=int(self.data.transactions.iloc[target].txId))
                                 for source, target in graph['edges']],
                          connections=graph['connections'], high_neighbours=graph['high_neighbours'],
                          neighbour_mean=graph['neighbour_mean'], displayed_nodes=len(nodes)))

    def warnings(self, period, level=None, increase=None):
        frozen = self.risk_rows(period)
        historical = [row for row in self.risk_rows(41, history=True) if row['warning']]
        exploratory = None
        if level is not None and increase is not None:
            frame = self.adapter.risk_periods(period)
            table = self.adapter.period_table(frame, level, increase)
            exploratory = [dict(row, level=str(table.iloc[i]['Review Level']),
                                exploratory_warning=bool(row['mean'] >= level and row['change'] >= increase))
                           for i, row in enumerate(frozen)]
        return dict(frozen=frozen, alerts=[row for row in frozen if row['warning']],
                    historical=historical, exploratory=exploratory,
                    rule=clean(self.adapter.rule))

    def models(self):
        metrics = self.data.metrics.to_dict('records')
        indexed = self.data.metrics.set_index('model')
        return clean(dict(metrics=metrics, labelled_test=len(self.data.test_predictions),
                          illicit_test=int(self.data.test_predictions.label.sum()),
                          winner=str(indexed.average_precision.idxmax()),
                          temporal_control_ap_difference=float(indexed.loc['Temporal GNN', 'average_precision'] -
                                                               indexed.loc['Reset-history ablation', 'average_precision']),
                          dimensions=dict(input=self.data.config['input_dim'], hidden=self.data.config['hidden_dim'],
                                          classifier=2 * self.data.config['hidden_dim'], output=2)))

    def model_details(self, name):
        if name not in MODELS:
            raise ValueError('Unknown model. Choose a model from the evaluation table.')
        labels = self.data.test_predictions.label.to_numpy()
        scores = self.data.test_predictions[name + '_score'].to_numpy()
        precision, recall, _ = precision_recall_curve(labels, scores)
        fpr, tpr, _ = roc_curve(labels, scores)
        return clean(dict(name=name, precision=precision, recall=recall, fpr=fpr, tpr=tpr,
                          prevalence=float(labels.mean()), confusion=self.data.confusions[name],
                          history=self.histories[name].to_dict('records')))
