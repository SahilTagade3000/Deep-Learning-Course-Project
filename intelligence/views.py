import time
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from sklearn.metrics import precision_recall_curve, roc_curve
from . import charts
from .config import COLORS, TEAL, CRITICAL_SCORE
from .data_adapter import reference, band, review_levels
from .theme import header, panel, section, table, chart


def command_center(a, period, engine):
    header('Temporal Transaction Risk Intelligence',
           'AI-powered graph and temporal analysis for illicit transaction detection and risk escalation monitoring.',
           st.session_state.replay['running'])
    values = a.dashboard(period)
    cols = st.columns(5)
    for col, title, value, help_text in zip(cols,
        ['Dataset coverage', 'Transactions replayed', 'High-risk transactions', 'Escalation flags', 'Model F1'],
        [f"{values['total']:,}", f"{values['processed']:,}", f"{values['high']:,}", str(values['alerts']), f"{values['f1']:.3f}"],
        ['All periods in the verified dataset.', 'Observed test periods 42 through the replay cursor.',
         'Transactions at or above the frozen classification threshold.', 'Frozen population flags through the replay cursor.',
         'Temporal GNN score across the entire frozen test split; not a rolling replay metric.']):
        col.metric(title, value, help=help_text)
    section('Monitoring workspace')
    left, right = st.columns([1.8,1])
    with left:
        chart(charts.trajectory(a.risk_periods(period),a.rule['risk_threshold']), 'command_trajectory')
    with right:
        chart(charts.distribution(a.visible(period),a.threshold), 'command_distribution')
    st.caption('Historical dataset replay • Scores are uncalibrated model indicators. Review bands are presentation categories, not additional trained classes.')
    left, right = st.columns([1.8,1])
    with left:
        section('Recent period · review queue')
        recent = a.tx[a.tx.time_step == period].nlargest(6,'temporal_score')
        table(a.transaction_table(recent))
        st.caption('Highest scores in the current period; within-period transaction arrival times are unavailable.')
    with right:
        section('Population review')
        risk = a.risk_periods(period)
        current = risk.iloc[-1]
        status = review_levels(risk,a.rule['risk_threshold'],a.rule['escalation_threshold'])[-1]
        panel(f'Period {period} · {status}', f'Population risk score {current.mean_score*100:.2f} / 100. '
              f'Change {current.risk_change*100:+.2f} points from the previous period.')
        panel('Evidence, not identity', 'Dataset records are anonymous transactions. No personal identity or wallet ownership information is available.')
    with st.expander('Coverage and interpretation'):
        table(a.visible(period).label.map({-1:'Unlabelled',0:'Licit',1:'Illicit'}).value_counts()
              .rename_axis('Recorded label').reset_index(name='Transactions replayed'))
        chart(charts.activity(a.risk_periods(period)), 'command_activity')
        st.write('Licit and illicit are observed dataset labels when available; the model risk bands are separate predictions. Unknown labels are not treated as licit.')


def picker(a, period, key):
    frame = a.visible(period)
    cases = a.demo_cases(period)
    chosen = st.session_state.get('selected_transaction', cases['Highest model score'])
    if chosen not in a.ids or not 42 <= int(a.get_transaction(chosen).time_step) <= period:
        chosen = cases['Highest model score']
    c1,c2 = st.columns([1,2])
    with c1:
        mode = st.selectbox('Find a transaction', ['Demonstration cases','Search by reference','Browse current period'], key=key+'_mode')
    with c2:
        if mode == 'Demonstration cases':
            case = st.selectbox('Real examples from observed periods', ['Keep selected transaction',*cases], key=key+'_case')
            if case in cases:
                chosen = cases[case]
        elif mode == 'Search by reference':
            query = st.text_input('Transaction Reference', value=reference(chosen), placeholder='TX-73160850',key=key+'_search')
            try:
                chosen = int(query.strip().upper().removeprefix('TX-'))
                row = a.get_transaction(chosen)
                if not 42 <= int(row.time_step) <= period:
                    st.info('This reference is outside the replayed test periods. Advance the monitoring cursor to its period.')
                    return None
            except (ValueError,TypeError):
                st.info('Enter an existing reference such as TX-73160850.')
                return None
        else:
            rows = frame[frame.time_step == period].sort_values('temporal_score',ascending=False)
            chosen = st.selectbox('Transactions in the current period · highest score first',
                                  rows.txId.astype(int).tolist(),format_func=reference,key=key+'_browse')
    st.session_state.selected_transaction = int(chosen)
    return int(chosen)


def transaction_intelligence(a, period, engine):
    header('Transaction Intelligence','Investigate a real transaction using the trained Temporal GNN.',st.session_state.replay['running'])
    tx_id = picker(a,period,'intelligence')
    if tx_id is None:
        return
    row = a.get_transaction(tx_id)
    st.caption(f'{reference(tx_id)} · Monitoring Period {int(row.time_step)} · Recorded label: '
               + {-1:'Unlabelled',0:'Licit',1:'Illicit'}[int(row.label)])
    if st.button('Analyze transaction',type='primary',key='analyze'):
        try:
            with st.spinner('Running the trained model on this transaction’s complete graph…'):
                started = time.perf_counter()
                scores,start,difference = engine().predict_period(int(row.time_step))
                st.session_state.inference = dict(tx_id=tx_id, score=float(scores[int(row.name)-start]),
                    difference=difference,seconds=time.perf_counter()-started,nodes=len(scores))
        except Exception as exc:
            st.error('The model could not complete a verified prediction. Run the artifact verifier before retrying.')
            with st.expander('Technical error details'):
                st.code(str(exc))
            return
    result = st.session_state.get('inference')
    if not result or result['tx_id'] != tx_id:
        panel('Ready for investigation','Select Analyze transaction to run a fresh prediction using the saved model, scaler and graph context.')
        return
    summary = a.selected_summary(tx_id)
    graph = summary['graph']
    score = result['score']; level = str(band(score,a.threshold))
    left,right = st.columns([1,1.6])
    with left:
        chart(charts.gauge(score,a.threshold),'transaction_gauge')
    with right:
        section(reference(tx_id))
        st.markdown(f'<span class="risk-badge" style="color:{COLORS[level]}">{level.upper()} REVIEW BAND</span>',unsafe_allow_html=True)
        c1,c2,c3 = st.columns(3)
        c1.metric('Monitoring Period',int(row.time_step))
        c2.metric('Network Connections',graph['connections'],help='Unique directly connected transactions in the full snapshot, excluding itself.')
        c3.metric('Decision threshold',f'{a.threshold*100:.0f} / 100')
        st.write('**Classification:** ' + ('Flagged for review' if score >= a.threshold else 'Below the review threshold'))
        st.caption('The displayed risk is an uncalibrated model score. It does not establish that an unlabelled transaction is illicit.')
    section('Risk indicators')
    c1,c2,c3 = st.columns(3)
    c1.info(f"Model score is {'above' if score >= a.threshold else 'below'} the frozen transaction threshold.")
    c2.info(f"{graph['high_neighbours']} of {graph['connections']} direct neighbours exceed that threshold.")
    change = float(summary['period'].risk_change)*100
    c3.info(f"The population score changed {change:+.2f} points in this period. This is not an individual transaction history.")
    st.caption('These are observed indicators, not feature attributions or causal explanations of the model’s decision.')
    with st.expander('Advanced Model Information'):
        st.json(dict(transaction_id=tx_id, temporal_index=int(row.time_step),
            illicit_class_score=score, predicted_class=int(score>=a.threshold),
            input_features=a.project.config['input_dim'], hidden_dimension=a.project.config['hidden_dim'],
            incoming_connections=graph['incoming'],outgoing_connections=graph['outgoing'],
            snapshot_nodes=result['nodes'],cpu_seconds=result['seconds'],
            max_difference_from_Kaggle=result['difference']))
        st.write('The 165 features are anonymized released numerical inputs. Their names do not identify financial meanings.')
        raw = a.project.arrays()['raw_features'][int(row.name)]
        table(pd.DataFrame({'Input':['Feature '+str(i+1).zfill(3) for i in range(len(raw))], 'Released value':raw}))


def temporal_risk(a,period,engine):
    header('Temporal Risk Intelligence','Track changes in the observed transaction population across monitoring periods.',st.session_state.replay['running'])
    st.caption('Analysis group: entire transaction population. Individual transactions do not persist across these periods.')
    include_history = st.toggle('Include training and validation context',value=False)
    frame = a.risk_periods(period,include_history)
    chart(charts.trajectory(frame,a.rule['risk_threshold'],'Observed population risk · chronological view'),'temporal_main')
    current = frame.iloc[-1]
    cols = st.columns(4)
    cols[0].metric('Previous population score',f'{current.previous_risk*100:.2f} / 100')
    cols[1].metric('Current population score',f'{current.mean_score*100:.2f} / 100')
    cols[2].metric('Risk change',f'{current.risk_change*100:+.2f} points',help='Current minus previous score, on a 0–100 display scale.')
    relative = current.risk_change/current.previous_risk*100 if current.previous_risk>0 else None
    cols[3].metric('Relative change',f'{relative:+.1f}%' if relative is not None else 'Unavailable',
                   help='100 × (current − previous) / previous. Different from a score-point change.')
    trend = 'Increasing' if current.risk_change>0 else 'Decreasing' if current.risk_change<0 else 'Stable'
    panel(f'Population trend · {trend}', 'Each point uses the complete observed graph for that period. Later test-period scores are not forecasts of events before they occur.')
    table(a.period_table(frame))
    with st.expander('How temporal memory works'):
        st.write('The GRU carries a graph-level summary forward in time. Node identities are not reused as persistent accounts. '
                 'Training periods 1–34 are in-sample context; 35–41 are validation; 42–49 are held-out test periods.')


def early_warnings(a,period,engine):
    header('Early Warning Center','Review observed population escalation against transparent experimental conditions.',st.session_state.replay['running'])
    frame = a.risk_periods(period)
    level = a.rule['risk_threshold']; increase = a.rule['escalation_threshold']
    frozen = a.period_table(frame)
    st.session_state.alert_list = frozen[frozen['Frozen Escalation Flag']].to_dict('records')
    cols=st.columns(3)
    cols[0].metric('Frozen escalation flags',int(frame.early_warning.sum()))
    cols[1].metric('Population level condition',f'{level*100:.2f} / 100')
    cols[2].metric('Increase condition',f'+{increase*100:.2f} points')
    panel('Two conditions, one escalation flag', 'Both the population level and its one-period increase must meet the frozen rule. '
          'Watch means the increase condition alone is met; High means the level condition alone is met; Critical means both are met. Normal means neither is met.')
    tab1,tab2,tab3 = st.tabs(['Frozen monitoring','Threshold exploration','Historical example'])
    with tab1:
        if not st.session_state.alert_list:
            st.info('No frozen escalation flags in the replayed test periods. High-scoring individual transactions may still require review.')
        else:
            table(pd.DataFrame(st.session_state.alert_list))
        section('Population review feed')
        table(frozen.sort_values('Monitoring Period',ascending=False))
        st.caption('Critical is an experimental review level, not verified advance warning. No warning-event labels or lead-time evaluation are available.')
    with tab2:
        st.write('Use the sidebar’s exploratory thresholds. Frozen results and model decisions remain unchanged.')
        if st.session_state.explore:
            what = a.period_table(frame,st.session_state.explore_level/100,st.session_state.explore_increase/100)
            what['Exploratory Escalation Flag'] = what['Review Level']=='Critical'
            st.warning('EXPLORATORY VIEW — these settings are not part of the frozen test evaluation.')
            table(what)
        else:
            st.info('Enable Threshold exploration in the sidebar to compare alternative review rules.')
    with tab3:
        history = a.project.risk[(a.project.risk.time_step<42) & a.project.risk.early_warning]
        if history.empty:
            st.info('No historical trigger satisfies the frozen rule in the exported training/validation periods.')
        else:
            selected = st.selectbox('Actual historical rule trigger',history.time_step.astype(int).tolist(),
                                   format_func=lambda t:f'Monitoring Period {t} · '+('training' if t<=34 else 'validation'))
            st.warning('Historical demonstration using earlier-period predictions. This is not an additional held-out test detection.')
            table(a.period_table(history[history.time_step==selected]))
    with st.expander('Individual high-score review queue — separate from population warnings'):
        table(a.transaction_table(a.visible(period).query('predicted_class == 1').nlargest(15,'temporal_score')))


def network_investigation(a,period,engine):
    header('Network Investigation','Explore real transaction relationships around a selected model-scored record.',st.session_state.replay['running'])
    tx_id = picker(a,period,'network')
    if tx_id is None:
        return
    graph = a.network(tx_id)
    left,right = st.columns([2.4,1])
    with left:
        chart(charts.network_graph(a,graph),'investigation_graph')
    with right:
        section(reference(tx_id))
        st.metric('Network Connections',graph['connections'],help='Unique direct neighbours before the visual cap.')
        st.metric('High-risk neighbours',graph['high_neighbours'],help='All direct neighbours above the frozen transaction threshold.')
        st.metric('Displayed network size',len(graph['nodes']),help='Selected transaction plus up to 30 direct neighbours ranked by score.')
        st.metric('Average neighbour score',f"{graph['neighbour_mean']*100:.1f} / 100" if graph['neighbour_mean'] is not None else 'No neighbours')
    st.caption('The labelled node with a larger white outline is selected. Arrows preserve original direction. '
               'The model uses the full undirected snapshot; this investigation view is capped at 31 nodes.')
    panel('Anonymous records, observed relationships','Network links and high model scores are investigation context, not proof of a laundering chain or shared ownership.')
    shown = a.transaction_table(a.tx.iloc[graph['nodes']])
    shown['Selected transaction'] = np.array(graph['nodes']) == graph['centre']
    table(shown)


def model_intelligence(a,period,engine):
    header('Model Intelligence','Inspect the measured evidence behind the system: baselines, frozen evaluation and model design.',st.session_state.replay['running'])
    st.caption('This benchmark covers the full held-out test split, independently of the monitoring replay cursor.')
    p = a.project
    tab1,tab2,tab3=st.tabs(['Evaluation','Training history','Architecture'])
    with tab1:
        chart(charts.comparison(p.metrics),'model_comparison')
        names={'model':'Model','accuracy':'Accuracy','precision':'Precision','recall':'Recall','f1':'F1',
               'roc_auc':'ROC AUC','average_precision':'Average Precision','threshold':'Decision threshold'}
        table(p.metrics[list(names)].rename(columns=names))
        model=st.selectbox('Inspect a model',p.metrics.model.tolist(),key='model_choice')
        y=p.test_predictions.label.to_numpy(); score=p.test_predictions[model+'_score'].to_numpy()
        prec,rec,_=precision_recall_curve(y,score); fpr,tpr,_=roc_curve(y,score)
        cols=st.columns(2)
        fig=go.Figure(go.Scatter(x=rec,y=prec,mode='lines',line=dict(color=TEAL),name=model))
        fig.add_hline(y=float(y.mean()),line_dash='dot',line_color='#D7B45A')
        charts.finish(fig,'Precision–recall'); fig.update_xaxes(title='Recall');fig.update_yaxes(title='Precision')
        with cols[0]:chart(fig,'pr_curve')
        fig=go.Figure(go.Scatter(x=fpr,y=tpr,mode='lines',line=dict(color=TEAL),name=model))
        fig.add_trace(go.Scatter(x=[0,1],y=[0,1],mode='lines',line=dict(dash='dot',color='#7B8EA5'),name='Chance'))
        charts.finish(fig,'ROC');fig.update_xaxes(title='False positive rate');fig.update_yaxes(title='True positive rate')
        with cols[1]:chart(fig,'roc_curve')
        cols=st.columns([1,1.3]);cm=np.array(p.confusions[model])
        fig=go.Figure(go.Heatmap(z=cm,x=['Predicted licit','Predicted illicit'],y=['Recorded licit','Recorded illicit'],
            text=cm,texttemplate='%{text}',colorscale=[[0,'#162738'],[1,'#3A9D90']],showscale=False))
        charts.finish(fig,'Frozen confusion matrix',300);fig.update_yaxes(autorange='reversed')
        with cols[0]:chart(fig,'confusion')
        with cols[1]:
            best=p.metrics.loc[p.metrics.average_precision.idxmax(),'model']
            difference=p.metrics.set_index('model').loc['Temporal GNN','average_precision']-p.metrics.set_index('model').loc['Reset-history ablation','average_precision']
            panel('Read the result honestly',f'{best} leads on test Average Precision. The temporal model’s AP difference from the reset-history control is {difference:+.6f}. These single-seed results do not establish statistical significance.')
            st.caption(f'{len(y):,} labelled test transactions; {int(y.sum()):,} illicit. Unknown labels are excluded. AP is Average Precision, not trapezoidal PR-AUC.')
        st.download_button('Download frozen test results',p.metrics.to_csv(index=False),file_name='frozen_test_metrics.csv',mime='text/csv')
    with tab2:
        model=st.selectbox('Training history',p.metrics.model.tolist(),key='history_model')
        filename={'XGBoost':'xgboost_history.csv','GCN':'gcn_history.csv','Temporal GNN':'temporal_gnn_history.csv',
                  'Reset-history ablation':'reset_history_history.csv'}[model]
        history=pd.read_csv(p.root/filename);x='round' if model=='XGBoost' else 'epoch'
        columns=['train_logloss','validation_logloss'] if model=='XGBoost' else ['train_loss','validation_loss']
        fig=go.Figure()
        for column,name,color in zip(columns,['Training','Validation'],[TEAL,'#E9985E']):
            fig.add_trace(go.Scatter(x=history[x],y=history[column],name=name,mode='lines',line=dict(color=color)))
        charts.finish(fig,'Recorded training and validation loss',350);fig.update_xaxes(title=x.title());fig.update_yaxes(title='Loss')
        chart(fig,'training_history')
        st.caption('Recorded Kaggle training history. Neural loss is class-weighted; XGBoost log loss is unweighted. No model is retrained here.')
    with tab3:
        st.markdown('<div class="architecture">'+ '<i>→</i>'.join(f'<span>{text}</span>' for text in
            ['Transaction graph','2 × GCN','Node embeddings + graph mean','GRU context','Node + temporal embedding','Risk score','Population review rule'])+'</div>',unsafe_allow_html=True)
        st.write('Two GCN layers represent transactions using their neighbours. The graph mean and previous graph context enter the GRU. '
                 'Each node embedding is concatenated with the updated context for classification. Population monitoring applies the separately frozen rule to aggregated scores.')
        table(pd.DataFrame({'Component':['Model input','Graph hidden dimension','GRU hidden dimension','Classifier input','Output classes'],
                            'Size':[p.config['input_dim'],p.config['hidden_dim'],p.config['hidden_dim'],2*p.config['hidden_dim'],2]}))
        st.caption('Weights, scaler, graph construction and the evaluation split are reused unchanged from the completed experiment.')
