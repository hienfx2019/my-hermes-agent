#!/usr/bin/env bash
set -e

export PYTHONPATH="$PWD/vendor/hermes-agent:$PYTHONPATH"

echo "==> Prepare Hermes config"
mkdir -p ~/.hermes

cat > ~/.hermes/config.yaml <<'YAML'
model:
  provider: openrouter
  default: openrouter/auto
  context_length: 128000
YAML

echo "==> Runtime check Hermes package"
python - <<'PY'
import hermes_cli
import pathlib

pkg = pathlib.Path(hermes_cli.__file__).parent
web_dist = pkg / "web_dist"

print("hermes_cli package:", pkg)
print("web_dist:", web_dist)
print("web_dist exists:", web_dist.exists())

if not web_dist.exists():
    raise SystemExit("ERROR: web_dist missing at runtime")
PY

echo "==> Start Hermes Telegram Gateway in background"
hermes gateway &

echo "==> Start Hermes Dashboard"
exec hermes dashboard --host 0.0.0.0 --port "${PORT:-10000}" --no-open
