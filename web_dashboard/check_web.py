"""Check the web bridge against the existing project, without running Streamlit."""
import os
os.environ.setdefault('OPENBLAS_NUM_THREADS', '1')
os.environ.setdefault('OMP_NUM_THREADS', '2')
os.environ.setdefault('MKL_NUM_THREADS', '2')
import hashlib
import json
from pathlib import Path
import sys
sys.dont_write_bytecode = True


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    from fastapi.testclient import TestClient
    import numpy as np
    from sklearn.metrics import average_precision_score, confusion_matrix
    from server import app, project_path

    project = project_path().resolve()
    protected = [p for p in project.rglob('*') if p.is_file() and
                 (p.suffix in {'.py', '.md', '.cmd', '.txt'} or 'artifacts' in p.parts) and
                 not any(part in {'.venv', '.venv311', 'web_dashboard', '__pycache__', '.git'} for part in p.parts)]
    before = {str(p): digest(p) for p in protected}
    checks = 0

    with TestClient(app) as client:
        bridge = app.state.service
        original = bridge.adapter

        def get(url):
            response = client.get(url)
            assert response.status_code == 200, (url, response.text)
            return response.json()

        assert get('/api/health')['ready']
        assert get('/api/meta')['threshold'] == bridge.data.threshold
        checks += 2
        for period in range(42, 50):
            dashboard = get(f'/api/overview?period={period}')
            assert dashboard['kpis'] == original.dashboard(period)
            assert sum(dashboard['bands'].values()) == dashboard['kpis']['processed']
            assert sum(dashboard['labels'].values()) == dashboard['kpis']['processed']
            assert len(dashboard['risk']) == period - 41
            assert all(row['period'] == period for row in dashboard['queue'])
            checks += 5
        final = get('/api/overview?period=49')['kpis']
        assert final['processed'] == 36824 and final['high'] == 1578 and final['alerts'] == 0
        checks += 1
        print('PASS: all eight replay dashboards match the original application.', flush=True)

        pool = get('/api/transactions?period=42&limit=10')
        assert pool['total'] == len(original.visible(42))
        assert all(row['period'] == 42 for row in pool['rows'])
        tx_id = 73160850
        selected = get(f'/api/transactions/{tx_id}?period=42')
        row = original.get_transaction(tx_id)
        assert selected['record']['score'] == float(row.temporal_score)
        assert selected['record']['label'] == 'Unlabelled'
        assert len(selected['technical']['raw_features']) == 165
        match = get(f'/api/transactions?query=TX-{tx_id}&period=42')
        assert len(match['rows']) == 1 and match['rows'][0]['id'] == tx_id
        assert get('/api/transactions?query=does-not-exist&period=42')['total'] == 0
        filtered = get('/api/transactions?risk=Critical&label=Illicit&period=49')
        assert filtered['rows'] and all(r['band'] == 'Critical' and r['label'] == 'Illicit' for r in filtered['rows'])
        second = get('/api/transactions?period=42&limit=10&offset=10')
        assert not set(r['id'] for r in pool['rows']) & set(r['id'] for r in second['rows'])
        checks += 9

        response = client.post(f'/api/transactions/{tx_id}/analyze?period=42')
        assert response.status_code == 200, response.text
        prediction = response.json()
        np.testing.assert_allclose(prediction['score'], row.temporal_score, rtol=1e-4, atol=1e-5)
        assert prediction['verified'] and prediction['device'] == 'CPU'
        assert prediction['snapshot_nodes'] == len(bridge.data.transactions[bridge.data.transactions.time_step == 42])
        checks += 4
        print(f"PASS: fresh model inference matches the Kaggle export; snapshot max difference {prediction['maximum_snapshot_difference']:.3g}.", flush=True)

        network = get(f'/api/network/{tx_id}?period=42')
        source = original.network(tx_id)
        assert network['connections'] == source['connections']
        assert network['high_neighbours'] == source['high_neighbours']
        assert network['displayed_nodes'] == len(source['nodes']) <= 31
        expected = {(int(bridge.data.transactions.iloc[a].txId), int(bridge.data.transactions.iloc[b].txId)) for a, b in source['edges']}
        assert {(e['source'], e['target']) for e in network['edges']} == expected
        assert sum(n['selected'] for n in network['nodes']) == 1
        checks += 5

        history = get('/api/risk?period=49&history=true')['rows']
        assert len(history) == 49 and history[0]['previous'] is None and history[0]['change'] is None
        warnings = get('/api/warnings?period=49')
        assert len(warnings['frozen']) == 8 and warnings['alerts'] == []
        assert [r['period'] for r in warnings['historical']] == [9, 11, 13, 17, 19, 20, 24, 25, 30, 34]
        exploratory = get('/api/warnings?period=49&level=0&increase=0')
        assert any(r['exploratory_warning'] for r in exploratory['exploratory'])
        assert exploratory['frozen'] == warnings['frozen'] and exploratory['alerts'] == []
        checks += 5
        print('PASS: real directed graph data, chronological visibility and separate exploratory warnings.', flush=True)

        metrics = get('/api/models')
        assert metrics['winner'] == 'XGBoost' and metrics['labelled_test'] == 8841
        for model in metrics['metrics']:
            name = model['model']
            detail = get('/api/models/' + name)
            truth = bridge.data.test_predictions.label.to_numpy()
            scores = bridge.data.test_predictions[name + '_score'].to_numpy()
            assert abs(model['average_precision'] - average_precision_score(truth, scores)) < 1e-10
            np.testing.assert_array_equal(detail['confusion'], confusion_matrix(truth, scores >= model['threshold']))
            assert len(detail['precision']) == len(detail['recall']) and detail['history']
            assert len(detail['fpr']) == len(detail['tpr'])
            checks += 4
        assert 'attachment' in client.get('/api/download/metrics').headers['content-disposition']
        checks += 2

        future = int(bridge.data.transactions[bridge.data.transactions.time_step == 49].iloc[0].txId)
        invalid = [('/api/overview?period=41', 422), ('/api/overview?period=50', 422),
                   ('/api/transactions?limit=1000', 422), ('/api/transactions?risk=Fake', 422),
                   ('/api/transactions/0?period=42', 400), (f'/api/transactions/{future}?period=42', 400),
                   ('/api/warnings?level=0.1', 422), ('/api/warnings?level=2&increase=0', 422),
                   ('/api/models/Fake', 400), ('/artifacts/temporal_gnn_weights.pth', 404)]
        for url, expected_status in invalid:
            assert client.get(url).status_code == expected_status, url
            checks += 1
        for asset in ['/', '/static/styles.css', '/static/app.js', '/static/vendor/plotly.min.js']:
            response = client.get(asset) if asset == '/' else client.head(asset)
            assert response.status_code == 200, asset
            checks += 1
        assert 'streamlit' not in sys.modules
        checks += 1
        print('PASS: metrics, all model curves, invalid inputs and locally bundled frontend assets.', flush=True)

    after = {str(p): digest(p) for p in protected}
    assert before == after, 'Original project files changed during web checks.'
    checks += 1
    print(f'ALL {checks} CHECKS PASSED. Original source files and artifacts unchanged.', flush=True)
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as error:
        import traceback
        traceback.print_exc()
        print(f'CHECK FAILED: {error}\nKeep your original files and share this terminal output for help.')
        sys.exit(1)
