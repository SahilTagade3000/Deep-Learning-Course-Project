"""Convert verified artifacts into readable, traceable presentation objects."""
import numpy as np
import pandas as pd
from analytics import neighbourhood
from .config import LOW_FRACTION_OF_DECISION, CRITICAL_SCORE, MAX_NEIGHBOURS


def reference(tx_id):
    return f'TX-{int(tx_id)}'


def band(score, decision):
    return np.select([np.asarray(score) >= CRITICAL_SCORE, np.asarray(score) >= decision,
                      np.asarray(score) >= decision * LOW_FRACTION_OF_DECISION],
                     ['Critical', 'High', 'Watch'], default='Low')


def review_levels(frame, level, increase):
    high = frame.mean_score >= level
    rising = frame.risk_change >= increase
    return np.select([high & rising, high, rising], ['Critical', 'High', 'Watch'], default='Normal')


class DataAdapter:
    def __init__(self, project):
        self.project = project
        self.tx = project.transactions
        self.times = self.tx.time_step.to_numpy()
        self.threshold = project.threshold
        self.ids = {int(value): int(index) for index, value in enumerate(self.tx.txId)}
        self.rule = project.frozen['warning_parameters']

    def visible(self, period):
        return self.tx[(self.times >= 42) & (self.times <= period)]

    def transaction_table(self, frame):
        return pd.DataFrame({
            'Transaction Reference': frame.txId.map(reference),
            'Monitoring Period': frame.time_step.to_numpy(),
            'Risk Score / 100': (frame.temporal_score * 100).round(2).to_numpy(),
            'Review Band': band(frame.temporal_score, self.threshold),
            'Recorded Label': frame.label.map({-1: 'Unlabelled', 0: 'Licit', 1: 'Illicit'}).to_numpy(),
        })

    def period_table(self, frame, level=None, increase=None):
        level = self.rule['risk_threshold'] if level is None else level
        increase = self.rule['escalation_threshold'] if increase is None else increase
        return pd.DataFrame({
            'Monitoring Period': frame.time_step.to_numpy(),
            'Previous Score / 100': (frame.previous_risk * 100).round(2).to_numpy(),
            'Population Score / 100': (frame.mean_score * 100).round(2).to_numpy(),
            'Change (score points)': (frame.risk_change * 100).round(2).to_numpy(),
            'Review Level': review_levels(frame, level, increase),
            'Frozen Escalation Flag': frame.early_warning.to_numpy(),
        })

    def risk_periods(self, period, include_history=False):
        start = 1 if include_history else 42
        risk = self.project.risk
        return risk[(risk.time_step >= start) & (risk.time_step <= period)].copy()

    def dashboard(self, period):
        frame = self.visible(period)
        risk = self.risk_periods(period)
        model = self.project.metrics.set_index('model').loc['Temporal GNN']
        return dict(total=len(self.tx), processed=len(frame), high=int(frame.predicted_class.sum()),
                    alerts=int(risk.early_warning.sum()), f1=float(model.f1),
                    current_mean=float(risk.iloc[-1].mean_score),
                    periods=len(risk))

    def get_transaction(self, tx_id):
        index = self.ids.get(int(tx_id))
        if index is None:
            raise ValueError('No transaction with this reference is available.')
        return self.tx.iloc[index]

    def network(self, tx_id):
        centre = self.ids[int(tx_id)]
        arrays = self.project.arrays()
        source, target = arrays['source_indices'], arrays['target_indices']
        adjacent = np.union1d(target[source == centre], source[target == centre])
        adjacent = adjacent[adjacent != centre]
        scores = self.tx.temporal_score.to_numpy()
        nodes, edges = neighbourhood(source, target, centre, scores, MAX_NEIGHBOURS)
        return dict(centre=centre, nodes=nodes, edges=edges, connections=len(adjacent),
                    high_neighbours=int((scores[adjacent] >= self.threshold).sum()),
                    neighbour_mean=float(scores[adjacent].mean()) if len(adjacent) else None,
                    incoming=int(np.unique(source[target == centre]).size),
                    outgoing=int(np.unique(target[source == centre]).size))

    def selected_summary(self, tx_id):
        row = self.get_transaction(tx_id)
        graph = self.network(tx_id)
        period = self.project.risk[self.project.risk.time_step == row.time_step].iloc[0]
        return dict(reference=reference(tx_id), row=row, graph=graph, period=period,
                    band=str(band(float(row.temporal_score), self.threshold)))

    def demo_cases(self, period):
        frame = self.visible(period)
        high = int(frame.loc[frame.temporal_score.idxmax(), 'txId'])
        low = int(frame.loc[frame.temporal_score.idxmin(), 'txId'])
        known = frame[(frame.label == 1) & (frame.predicted_class == 1)]
        cases = {'Highest model score': high, 'Low-score example': low}
        if not known.empty:
            cases['Detected labelled illicit example'] = int(known.loc[known.temporal_score.idxmax(), 'txId'])
        return cases
