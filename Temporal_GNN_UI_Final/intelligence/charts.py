import numpy as np
import plotly.graph_objects as go
import networkx as nx
from .config import COLORS, TEAL, MUTED
from .data_adapter import band, reference


def finish(fig, title='', height=300):
    fig.update_layout(template='plotly_dark', paper_bgcolor='#101B2B', plot_bgcolor='#101B2B',
        font=dict(family='Segoe UI, sans-serif', color='#B5C4D7', size=12),
        title=dict(text=title, font=dict(size=15, color='#E8F0F8'), x=.035),
        height=height, margin=dict(l=35, r=25, t=50, b=35),
        legend=dict(orientation='h', y=-.22, x=0), hoverlabel=dict(bgcolor='#23354A'),
        xaxis=dict(gridcolor='#223147', zeroline=False), yaxis=dict(gridcolor='#223147', zeroline=False))
    return fig


def trajectory(frame, level=None, title='Population risk trajectory'):
    fig = go.Figure(go.Scatter(x=frame.time_step, y=frame.mean_score * 100,
        mode='lines+markers', line=dict(color=TEAL, width=2.5), marker=dict(size=6),
        fill='tozeroy', fillcolor='rgba(108,218,196,.07)', name='Population score',
        hovertemplate='Period %{x}<br>Population score %{y:.2f} / 100<extra></extra>'))
    if level is not None:
        fig.add_hline(y=level*100, line_dash='dot', line_color=COLORS['Watch'],
                      annotation_text='Frozen level condition', annotation_position='top left')
    if frame.time_step.min() < 42 and frame.time_step.max() >= 42:
        fig.add_vline(x=41.5, line_dash='dash', line_color=MUTED)
    finish(fig, title)
    fig.update_xaxes(title='Monitoring Period', dtick=1 if len(frame)<10 else 5)
    if frame.time_step.min() >= 42:
        fig.update_xaxes(range=[41.7,49.3])
    fig.update_yaxes(title='Model score / 100', rangemode='tozero')
    return fig


def distribution(frame, threshold):
    values = band(frame.temporal_score, threshold)
    counts = [int((values == label).sum()) for label in COLORS]
    fig = go.Figure(go.Pie(labels=list(COLORS), values=counts, hole=.74,
                          marker=dict(colors=list(COLORS.values())), sort=False,
                          textinfo='none', hovertemplate='%{label}: %{value:,}<extra></extra>'))
    fig.add_annotation(text=f'<b>{len(frame):,}</b><br>transactions', x=.5, y=.5,
                       showarrow=False, font=dict(size=17, color='#E8F0F8'))
    return finish(fig, 'Review distribution')


def activity(frame):
    fig = go.Figure(go.Bar(x=frame.time_step, y=frame.total_transactions,
                           marker_color='#467F99', name='Transactions',
                           hovertemplate='Period %{x}<br>%{y:,} transactions<extra></extra>'))
    finish(fig, 'Observed network activity', 260)
    fig.update_xaxes(title='Monitoring Period', dtick=1)
    fig.update_yaxes(title='Transactions')
    return fig


def gauge(score, threshold):
    fig = go.Figure(go.Indicator(mode='gauge+number', value=score*100,
        number=dict(suffix=' / 100', font=dict(size=32, color='#ECF4FC')),
        title=dict(text='Transaction risk score', font=dict(size=14)),
        gauge=dict(axis=dict(range=[0,100], tickvals=[0,50,100]),
            bgcolor='#233246', borderwidth=0, bar=dict(color=str(COLORS[str(band(score, threshold))])),
            steps=[dict(range=[0,threshold*100],color='#1A3A38'),
                   dict(range=[threshold*100,100],color='#45302C')],
            threshold=dict(line=dict(color='#D8E5F3',width=3), value=threshold*100))))
    return finish(fig, height=270)


def network_graph(adapter, graph):
    network = nx.DiGraph()
    network.add_nodes_from(graph['nodes']); network.add_edges_from(graph['edges'])
    positions = nx.spring_layout(network, seed=42)
    fig = go.Figure()
    ex, ey = [], []
    for source, target in graph['edges']:
        ex.extend([positions[source][0], positions[target][0], None])
        ey.extend([positions[source][1], positions[target][1], None])
        # Direction is shown at the target end of each original edge.
        a, b = positions[source], positions[target]
        if source != target:
            fig.add_annotation(x=b[0]*.88+a[0]*.12, y=b[1]*.88+a[1]*.12,
                ax=b[0]*.68+a[0]*.32, ay=b[1]*.68+a[1]*.32,
                xref='x', yref='y', axref='x', ayref='y', text='', showarrow=True,
                arrowhead=2, arrowsize=.7, arrowwidth=1, arrowcolor='#52657B')
    fig.add_trace(go.Scatter(x=ex,y=ey,mode='lines',line=dict(color='#3B5065',width=1),
                            hoverinfo='skip',showlegend=False))
    for name, color in COLORS.items():
        nodes = [i for i in graph['nodes'] if str(band(adapter.tx.iloc[i].temporal_score,adapter.threshold)) == name]
        rows = adapter.tx.iloc[nodes]
        hover = [[reference(row.txId), float(row.temporal_score)*100,
                  {-1:'Unlabelled',0:'Licit',1:'Illicit'}[int(row.label)]] for row in rows.itertuples()]
        fig.add_trace(go.Scatter(x=[positions[i][0] for i in nodes], y=[positions[i][1] for i in nodes],
            mode='markers', name=name, customdata=hover,
            marker=dict(size=[25 if i == graph['centre'] else 14 for i in nodes], color=color,
                        line=dict(width=[3 if i == graph['centre'] else 1 for i in nodes], color='#DCE9F7')),
            hovertemplate='%{customdata[0]}<br>Risk %{customdata[1]:.2f} / 100<br>Recorded label: %{customdata[2]}<extra></extra>'))
    centre = graph['centre']
    fig.add_annotation(x=positions[centre][0],y=positions[centre][1],
                        text=reference(adapter.tx.iloc[centre].txId),showarrow=False,yshift=25,font=dict(color='#FFFFFF'))
    finish(fig, 'Transaction neighbourhood · drag to pan, scroll controls to zoom', 480)
    fig.update_layout(dragmode='pan')
    fig.update_xaxes(visible=False); fig.update_yaxes(visible=False,scaleanchor='x',scaleratio=1)
    return fig


def comparison(metrics):
    fig = go.Figure()
    for metric, name, color in [('average_precision','Average Precision',TEAL),('f1','F1','#789ECB')]:
        fig.add_trace(go.Bar(x=metrics.model,y=metrics[metric],name=name,marker_color=color,
                            hovertemplate='%{x}<br>%{y:.4f}<extra>'+name+'</extra>'))
    finish(fig, 'Frozen test comparison', 330)
    fig.update_yaxes(range=[0,1], title='Score')
    return fig
