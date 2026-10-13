#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
PYTHON_BIN="./.venv311/bin/python"
if [ ! -x "$PYTHON_BIN" ] || [ ! -f .venv311/.setup_complete ]; then
  echo "Setup is not complete. Run: bash .devcontainer/setup.sh"
  exit 1
fi
"$PYTHON_BIN" -c "import sys; assert sys.version_info[:2] == (3, 11), 'Use the supplied Python 3.11 Codespace configuration.'"
test -f artifacts/artifact_manifest.json || { echo "Missing model/data artifacts. Upload the complete artifacts folder."; exit 1; }
echo "Starting the dashboard on port 8000. Keep this terminal running."
exec "$PYTHON_BIN" -m uvicorn server:app --app-dir web_dashboard --host 0.0.0.0 --port 8000
