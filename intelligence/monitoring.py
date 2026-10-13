"""Finite historical replay. No synthetic records, sleeps or background loops."""
from datetime import datetime


def initial_state():
    return dict(period=42, running=False, last_tick=None, updated='Not started')


def control(state, action, now):
    result = dict(state)
    if action == 'start':
        if result['period'] == 49:
            result['period'] = 42
        result.update(running=True, last_tick=now)
    elif action == 'pause':
        result['running'] = False
    elif action == 'reset':
        return initial_state()
    else:
        raise ValueError('Unknown replay control')
    return result


def advance(state, now, interval):
    result = dict(state)
    if result['running'] and result['last_tick'] is not None and now - result['last_tick'] >= interval:
        result['period'] = min(49, result['period'] + 1)
        result['last_tick'] = now
        result['updated'] = datetime.now().astimezone().strftime('%H:%M:%S %Z')
        if result['period'] == 49:
            result['running'] = False
    return result
