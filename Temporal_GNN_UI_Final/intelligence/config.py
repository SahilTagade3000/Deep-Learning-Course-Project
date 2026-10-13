from pathlib import Path
import os

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = Path(os.environ.get('TEMPORAL_ARTIFACT_DIR', str(ROOT / 'artifacts')))
PAGES = ['Command Center', 'Transaction Intelligence', 'Temporal Risk',
         'Early Warning Center', 'Network Investigation', 'Model Intelligence']
COLORS = {'Low': '#59BFA6', 'Watch': '#D7B45A', 'High': '#E9985E', 'Critical': '#E56F7C'}
TEAL = '#6CDAC4'
MUTED = '#8E9BAE'
# Presentation bands only; the model decision threshold is always read from its export.
LOW_FRACTION_OF_DECISION = 0.5
CRITICAL_SCORE = 0.90
MAX_NEIGHBOURS = 30
