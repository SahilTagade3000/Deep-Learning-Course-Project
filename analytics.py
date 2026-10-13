"""Small, deterministic operations shared by the app and verification script."""
import numpy as np


def warning_flags(frame, level, increase):
    """Both conditions must hold; a missing previous period cannot trigger a flag."""
    return ((frame['mean_score'] >= level) &
            (frame['risk_change'] >= increase)).fillna(False)


def snapshot_bounds(times, period):
    rows = np.flatnonzero(np.asarray(times) == period)
    if not len(rows):
        raise ValueError(f'Time step {period} is absent from the exported data.')
    start, stop = int(rows[0]), int(rows[-1]) + 1
    if stop - start != len(rows):
        raise ValueError('Snapshot rows are not contiguous. Restore the original export.')
    return start, stop


def neighbourhood(source, target, centre, scores, max_neighbours=30):
    adjacent = set(target[source == centre]) | set(source[target == centre])
    adjacent.discard(centre)
    chosen = sorted(adjacent, key=lambda i: (-float(scores[i]), int(i)))[:max_neighbours]
    nodes = sorted({int(centre), *map(int, chosen)})
    mask = np.isin(source, nodes) & np.isin(target, nodes)
    return nodes, list(zip(source[mask].tolist(), target[mask].tolist()))
