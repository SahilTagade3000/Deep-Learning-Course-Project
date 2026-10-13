"""Run the standalone dashboard from the existing project environment."""
import argparse
import socket
from pathlib import Path
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8000)
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535:
        parser.error('Choose a port between 1024 and 65535.')
    try:
        import uvicorn
    except ImportError:
        print('Install the new web dependencies first:\n'
              r'.\.venv\Scripts\python.exe -m pip install -r web_dashboard\requirements_web.txt')
        return 1
    with socket.socket() as probe:
        try:
            probe.bind(('127.0.0.1', args.port))
        except OSError:
            print(f'Port {args.port} is already in use. Stop the earlier terminal with Ctrl+C, '
                  f'or add --port {args.port + 1} to the command.')
            return 1
    print(f'\nDashboard: http://127.0.0.1:{args.port}\n'
          'Keep this terminal open. Press Ctrl+C to stop.\n', flush=True)
    uvicorn.run('server:app', app_dir=str(Path(__file__).resolve().parent),
                host='127.0.0.1', port=args.port, workers=1)
    return 0


if __name__ == '__main__':
    sys.exit(main())
