"""Six-page interface for the frozen Elliptic experiment. Run with Streamlit."""
from pathlib import Path
import time

import numpy as np
import pandas as pd
import streamlit as st

from analytics import neighbourhood, warning_flags
from project_data import ProjectData, InferenceEngine, REQUIRED

ROOT = Path(__file__).resolve().parent
ARTIFACTS = ROOT / 'artifacts'
st.set_page_config(page_title='Transaction Risk Monitor', page_icon='◈', layout='wide')


@st.cache_resource
def load_project():
    return ProjectData(ARTIFACTS)


@st.cache_resource
def load_engine():
    return InferenceEngine(load_project())


def table(frame):
    st.dataframe(frame, use_container_width=True, hide_index=True)


def download(frame, filename):
    st.download_button('Download this table', frame.to_csv(index=False).encode('utf-8'),
                       file_name=filename, mime='text/csv')


def label_name(value):
    return {-1: 'Unknown', 0: 'Licit', 1: 'Illicit'}[int(value)]


def transaction_picker(data, key):
    period = st.selectbox('Time step', list(range(1, 50)), index=41, key=key + '_period')
    rows = data.transactions[data.transactions.time_step == period]
    default_id = int(rows.loc[rows.temporal_score.idxmax(), 'txId'])
    text = st.text_input('Transaction ID', value=str(default_id), key=f'{key}_id_{period}')
    try:
        tx_id = int(text.strip())
    except ValueError:
        st.info('Enter an integer transaction ID from this dataset.')
        return None
    match = rows[rows.txId == tx_id]
    if match.empty:
        st.info('That ID is not in the selected time step. Choose its time step or use an example below.')
        table(rows.nlargest(10, 'temporal_score')[['txId', 'temporal_score', 'class']])
        return None
    with st.expander('Other transactions in this time step'):
        st.caption('These examples are ranked by saved model score, including unknown labels.')
        table(rows.nlargest(20, 'temporal_score')[['txId', 'class', 'temporal_score']])
    return match.iloc[0]


def dashboard(data):
    st.title('Transaction Risk Monitor')
    st.write('A GCN + GRU study of transaction graphs across 49 time steps.')
    tx = data.transactions
    test = tx[tx.split == 'test']
    risk = data.risk[data.risk.time_step >= 42]
    a, b, c, d = st.columns(4)
    a.metric('All transactions', f'{len(tx):,}')
    b.metric('Test transactions', f'{len(test):,}')
    c.metric('Test transactions above threshold', f'{int(test.predicted_class.sum()):,}')
    d.metric('Test periods with escalation flags', int(risk.early_warning.sum()))
    st.caption('Transaction counts include unknown labels. Flags refer to entire periods; they are not transaction labels.')
    a, b, c = st.columns(3)
    a.metric('Known labels across all periods', f'{int((tx.label >= 0).sum()):,}')
    b.metric('Known illicit across all periods', f'{int((tx.label == 1).sum()):,}')
    c.metric('Model hidden dimension', data.config['hidden_dim'])
    left, right = st.columns([2, 1])
    with left:
        st.subheader('Population score over time')
        st.line_chart(data.risk.set_index('time_step')[['mean_score']])
        st.caption('1–34: training (in sample) · 35–41: validation · 42–49: held-out test. Scores are uncalibrated.')
    with right:
        st.subheader('Available labels')
        counts = tx.label.map(label_name).value_counts().rename_axis('Label').reset_index(name='Transactions')
        table(counts)
        st.write('Unknown transactions support graph context and receive scores. They are excluded from supervised metrics.')
    st.subheader('Test-period score distribution')
    counts, bins = np.histogram(test.temporal_score, bins=np.linspace(0, 1, 11))
    distribution = pd.DataFrame({'Score range': [f'{lo:.1f}–{hi:.1f}' for lo, hi in zip(bins[:-1], bins[1:])],
                                 'Transactions': counts}).set_index('Score range')
    st.bar_chart(distribution)
    st.subheader('Held-out comparison')
    table(data.metrics[['model', 'average_precision', 'f1', 'precision', 'recall']])
    best = data.metrics.loc[data.metrics.average_precision.idxmax(), 'model']
    st.info(f'{best} has the highest test Average Precision in this experiment. All models use frozen validation thresholds.')
    st.caption('Dashboard values come from the verified Phase 5 export. Use Transaction Analyzer for a fresh model forward pass.')


def analyzer(data):
    st.title('Transaction Analyzer')
    st.write('Run the saved Temporal GNN on the full graph snapshot containing a selected transaction.')
    selected = transaction_picker(data, 'analyzer')
    if selected is None:
        return
    tx_id, period = int(selected.txId), int(selected.time_step)
    st.write(f'Observed dataset label: **{label_name(selected.label)}** · Time step **{period}** · Split **{selected.split}**')
    st.caption('Features and prior graph context are from the historical export. This interface accepts existing dataset IDs.')
    if st.button('Run model inference', type='primary'):
        try:
            started = time.perf_counter()
            with st.spinner('Loading the model and scoring this graph on CPU…'):
                scores, start, difference = load_engine().predict_period(period)
            score = float(scores[int(selected.name) - start])
            st.session_state['inference_result'] = dict(
                tx_id=tx_id, period=period, score=score, difference=difference,
                seconds=time.perf_counter() - started, nodes=len(scores))
        except Exception as exc:
            st.error(f'Inference could not be verified: {exc}')
            st.info('Run verify_artifacts.py in the VS Code terminal and inspect its error before continuing.')
    result = st.session_state.get('inference_result')
    if result and result['tx_id'] == tx_id and result['period'] == period:
        a, b, c = st.columns(3)
        a.metric('Illicit-class model score', f"{result['score']:.6f}")
        b.metric('Frozen decision threshold', f'{data.threshold:.2f}')
        c.metric('Model prediction', 'Illicit' if result['score'] >= data.threshold else 'Licit')
        st.write('Review status: **' + ('Above transaction threshold' if result['score'] >= data.threshold
                                      else 'Below transaction threshold') + '**')
        st.caption('An uncalibrated model score is not a confirmed illicit label or an estimated real-world crime probability.')
        with st.expander('Inference verification'):
            st.write(f"Scored {result['nodes']:,} nodes on CPU in {result['seconds']:.3f} seconds, including initial loading if needed.")
            st.write(f"Maximum snapshot difference from Kaggle: {result['difference']:.3g}.")
            st.write('Saved scaler → complete undirected snapshot → GCN → prior-context GRU → classifier. No training or label input.')


def future_risk(data):
    st.title('Future Risk')
    st.info('This page monitors held-out later periods after their graphs are observed. The model does not forecast an unseen future period.')
    risk = data.risk[data.risk.time_step >= 42].copy()
    st.line_chart(risk.set_index('time_step')[['mean_score', 'previous_risk']])
    period = st.selectbox('Inspect test period', risk.time_step.tolist())
    row = risk[risk.time_step == period].iloc[0]
    a, b, c = st.columns(3)
    a.metric('Previous population mean', f'{row.previous_risk:.4f}')
    b.metric('Current population mean', f'{row.mean_score:.4f}')
    c.metric('One-period change', f'{row.risk_change:+.4f}')
    st.caption('The population changes between snapshots. These are not trajectories of the same transaction or account.')
    table(risk[['time_step', 'total_transactions', 'high_risk_transactions', 'mean_score', 'risk_change']])
    download(risk, 'held_out_population_scores.csv')


def warnings_page(data):
    st.title('Early Warnings')
    st.write('An experimental population review rule, frozen using validation periods 35–41.')
    rule = data.frozen['warning_parameters']
    level, increase = float(rule['risk_threshold']), float(rule['escalation_threshold'])
    st.write(f'A flag requires **mean score ≥ {level:.6f}** AND **one-period increase ≥ {increase:.6f}**.')
    shown = data.risk[data.risk.time_step >= 42].copy()
    st.metric('Frozen test-period escalation flags', int(shown.early_warning.sum()))
    st.caption('Zero flags does not mean there are no illicit or high-scoring transactions. No advance-warning performance has been established.')
    if st.checkbox('Explore different thresholds (separate what-if view)'):
        st.warning('Exploratory view only. This does not replace the frozen benchmark or saved results.')
        level = st.slider('Exploratory population level', 0.0, 1.0, level, step=0.001, format='%.3f')
        increase = st.slider('Exploratory minimum increase', 0.0, 1.0, increase, step=0.001, format='%.3f')
        shown['exploratory_flag'] = warning_flags(shown, level, increase)
        st.metric('Exploratory flags', int(shown.exploratory_flag.sum()))
    shown['level_condition'] = shown.mean_score >= level
    shown['increase_condition'] = shown.risk_change >= increase
    columns = ['time_step', 'previous_risk', 'mean_score', 'risk_change', 'early_warning',
               'level_condition', 'increase_condition']
    if 'exploratory_flag' in shown:
        columns.append('exploratory_flag')
    table(shown[columns])
    st.caption('early_warning always shows the original frozen flag. Condition columns use the thresholds currently displayed.')
    st.subheader('High-scoring transactions for separate review')
    st.caption('Individual scores use the frozen transaction threshold and do not require a population escalation flag.')
    tx = data.transactions
    table(tx[(tx.split == 'test') & (tx.predicted_class == 1)].nlargest(20, 'temporal_score')
          [['txId', 'time_step', 'class', 'temporal_score']])


def network_page(data):
    import matplotlib.pyplot as plt
    import networkx as nx
    st.title('Suspicious Network')
    st.write('Inspect a real transaction and up to 30 direct neighbours, ranked by saved model score.')
    selected = transaction_picker(data, 'network')
    if selected is None:
        return
    centre = int(selected.name)
    arrays = data.arrays()
    nodes, edges = neighbourhood(arrays['source_indices'], arrays['target_indices'], centre,
                                 data.transactions.temporal_score.to_numpy())
    graph = nx.DiGraph()
    graph.add_nodes_from(nodes)
    graph.add_edges_from(edges)
    pos = nx.spring_layout(graph, seed=42)
    fig, ax = plt.subplots(figsize=(10, 6))
    plot = nx.draw_networkx_nodes(graph, pos, nodelist=nodes,
        node_color=data.transactions.iloc[nodes].temporal_score.to_numpy(),
        cmap='YlOrRd', vmin=0, vmax=1, node_size=[750 if i == centre else 250 for i in nodes], ax=ax)
    nx.draw_networkx_edges(graph, pos, arrows=True, alpha=0.4, ax=ax)
    nx.draw_networkx_labels(graph, pos, labels={centre: str(int(selected.txId))}, font_size=9, ax=ax)
    fig.colorbar(plot, ax=ax, label='Uncalibrated model score')
    ax.axis('off')
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)
    st.caption('Arrows preserve original edge direction. The GCN uses undirected edges. This capped view is not the full graph used for inference.')
    st.write(f'Selected transaction label: **{label_name(selected.label)}**. Graph connections and high scores do not prove a laundering chain.')
    shown = data.transactions.iloc[nodes][['txId', 'time_step', 'label', 'temporal_score', 'predicted_class']].copy()
    shown['observed_label'] = shown.label.map(label_name)
    shown['selected_centre'] = np.array(nodes) == centre
    table(shown.drop(columns='label'))
    download(shown, f'neighbourhood_{int(selected.txId)}.csv')


def performance(data):
    import matplotlib.pyplot as plt
    from sklearn.metrics import precision_recall_curve, roc_curve, ConfusionMatrixDisplay
    st.title('Model Performance')
    st.write('Frozen evaluation on labelled transactions in periods 42–49. Unknown labels are excluded.')
    table(data.metrics)
    download(data.metrics, 'frozen_test_metrics.csv')
    metrics = data.metrics.set_index('model')
    difference = metrics.loc['Temporal GNN', 'average_precision'] - metrics.loc['Reset-history ablation', 'average_precision']
    st.caption(f'Temporal versus reset-history test AP difference: {difference:+.6f}. Single-seed descriptive result; no significance claim.')
    model = st.selectbox('Inspect model', data.metrics.model.tolist())
    predictions = data.test_predictions
    y = predictions.label.to_numpy()
    score = predictions[model + '_score'].to_numpy()
    prec, rec, _ = precision_recall_curve(y, score)
    fpr, tpr, _ = roc_curve(y, score)
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    axes[0].plot(rec, prec)
    axes[0].axhline(y.mean(), color='gray', linestyle=':', label=f'Prevalence {y.mean():.4f}')
    axes[0].set(title='Precision–recall', xlabel='Recall', ylabel='Precision', xlim=(0, 1), ylim=(0, 1.03))
    axes[0].legend(fontsize=8)
    axes[1].plot(fpr, tpr)
    axes[1].plot([0, 1], [0, 1], color='gray', linestyle=':')
    axes[1].set(title='ROC', xlabel='False positive rate', ylabel='True positive rate')
    ConfusionMatrixDisplay(np.asarray(data.confusions[model]), display_labels=['Licit', 'Illicit']).plot(ax=axes[2], colorbar=False)
    axes[2].set_title(f"Frozen threshold {data.frozen['thresholds'][model]:.2f}")
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)
    st.subheader('Performance by test period')
    period = data.period_metrics[data.period_metrics.model == model]
    st.line_chart(period.set_index('time_step')[['average_precision', 'f1']])
    table(period[['time_step', 'n', 'illicit', 'average_precision', 'f1', 'recall']])
    st.caption('Periods with very few illicit labels can have unstable metrics. Average Precision is not trapezoidal PR-AUC.')
    st.subheader('Validation and test')
    combined = pd.concat([data.validation[['model', 'split', 'average_precision', 'f1']],
                          data.metrics[['model', 'split', 'average_precision', 'f1']]], ignore_index=True)
    table(combined[combined.model == model])
    st.subheader('Recorded training history')
    filename = {'XGBoost': 'xgboost_history.csv', 'GCN': 'gcn_history.csv',
                'Temporal GNN': 'temporal_gnn_history.csv',
                'Reset-history ablation': 'reset_history_history.csv'}[model]
    history = pd.read_csv(ARTIFACTS / filename)
    if model == 'XGBoost':
        st.line_chart(history.set_index('round')[['train_logloss', 'validation_logloss']])
    else:
        st.line_chart(history.set_index('epoch')[['train_loss', 'validation_loss']])
    st.caption('These are recorded Kaggle training curves. The app does not train models. Neural losses are class-weighted.')


def main():
    missing = [name for name in REQUIRED if not (ARTIFACTS / name).is_file()]
    if missing:
        st.title('Connect your Kaggle results')
        st.write('Extract temporal_gnn_inference_artifacts.zip into the artifacts folder beside app.py.')
        st.code(str(ARTIFACTS))
        st.info('Use the complete Phase 5 ZIP from Cell 37. The earlier checkpoint ZIPs do not contain all inference inputs.')
        with st.expander('Missing files'):
            st.write(missing)
        st.stop()
    try:
        with st.spinner('Checking the exported files…'):
            data = load_project()
    except Exception as exc:
        st.error(f'Artifact verification failed: {exc}')
        st.info('Restore the complete, unchanged Phase 5 export and restart the app.')
        st.stop()
    st.sidebar.title('Transaction Risk')
    page = st.sidebar.radio('Pages', ['Dashboard', 'Transaction Analyzer', 'Future Risk',
                                    'Early Warnings', 'Suspicious Network', 'Model Performance'])
    st.sidebar.caption('GCN + GRU · Elliptic dataset · CPU inference')
    st.sidebar.caption('Training 1–34 | Validation 35–41 | Test 42–49')
    st.sidebar.caption('Historical research prototype. Model scores are uncalibrated.')
    handlers = {'Dashboard': dashboard, 'Transaction Analyzer': analyzer, 'Future Risk': future_risk,
                'Early Warnings': warnings_page, 'Suspicious Network': network_page,
                'Model Performance': performance}
    handlers[page](data)


if __name__ == '__main__':
    main()
