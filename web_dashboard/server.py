"""Serve the custom frontend and the original verified experiment on one local origin."""
from contextlib import asynccontextmanager
import json
import logging
import os
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from web_service import DashboardService

ROOT = Path(__file__).resolve().parent
Period = Query(default=42, ge=42, le=49)


def project_path():
    override = os.environ.get('TEMPORAL_PROJECT_DIR')
    if override:
        return Path(override)
    if (ROOT.parent / 'project_data.py').is_file():
        return ROOT.parent
    return Path(json.loads((ROOT / 'project.json').read_text(encoding='utf-8'))['project_path'])


@asynccontextmanager
async def lifespan(app):
    app.state.service = DashboardService(project_path())
    print('Verified artifacts loaded. The saved CPU model loads on first analysis.', flush=True)
    yield


app = FastAPI(title='Temporal Transaction Risk Dashboard', lifespan=lifespan)


def service(request):
    return request.app.state.service


@app.exception_handler(ValueError)
async def invalid_value(request, exc):
    return JSONResponse(status_code=400, content={'detail': str(exc)})


@app.exception_handler(Exception)
async def unexpected_error(request, exc):
    logging.exception('Dashboard operation failed')
    return JSONResponse(status_code=500, content={'detail': 'This operation could not complete. '
                                                'See the server terminal for details and run the artifact verifier.'})


@app.get('/api/health')
def health(request: Request):
    return {'ready': True, 'device': 'CPU', 'manifest_files': len(service(request).data.manifest)}


@app.get('/api/meta')
def meta(request: Request):
    return service(request).meta()


@app.get('/api/overview')
def overview(request: Request, period: int = Period):
    return service(request).overview(period)


@app.get('/api/transactions')
def transactions(request: Request, period: int = Period, query: str = Query(default='', max_length=80),
                 risk: Literal['All', 'Low', 'Watch', 'High', 'Critical'] = 'All',
                 label: Literal['All', 'Licit', 'Illicit', 'Unlabelled'] = 'All',
                 offset: int = Query(default=0, ge=0), limit: int = Query(default=25, ge=1, le=100)):
    return service(request).transactions(period, query, risk, label, offset, limit)


@app.get('/api/transactions/{tx_id}')
def transaction(request: Request, tx_id: int, period: int = Period):
    return service(request).transaction(tx_id, period)


@app.post('/api/transactions/{tx_id}/analyze')
def analyze(request: Request, tx_id: int, period: int = Period):
    return service(request).analyze(tx_id, period)


@app.get('/api/network/{tx_id}')
def network(request: Request, tx_id: int, period: int = Period):
    return service(request).network(tx_id, period)


@app.get('/api/risk')
def risk(request: Request, period: int = Period, history: bool = False):
    return {'rows': service(request).risk_rows(period, history)}


@app.get('/api/warnings')
def warnings(request: Request, period: int = Period,
             level: float | None = Query(default=None, ge=0, le=1),
             increase: float | None = Query(default=None, ge=0, le=1)):
    if (level is None) != (increase is None):
        raise HTTPException(status_code=422, detail='Supply both exploratory thresholds together.')
    return service(request).warnings(period, level, increase)


@app.get('/api/models')
def models(request: Request):
    return service(request).models()


@app.get('/api/models/{name}')
def model_details(request: Request, name: str):
    return service(request).model_details(name)


@app.get('/api/download/metrics')
def download(request: Request):
    return Response(service(request).data.metrics.to_csv(index=False), media_type='text/csv',
                    headers={'Content-Disposition': 'attachment; filename="frozen_test_metrics.csv"'})


@app.get('/')
def index():
    return FileResponse(ROOT / 'static' / 'index.html')


app.mount('/static', StaticFiles(directory=ROOT / 'static'), name='static')
