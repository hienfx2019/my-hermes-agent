#!/usr/bin/env bash
set -e

echo "==> Install Python dependencies"
pip install --upgrade pip
pip install -r requirements.txt

echo "==> Clone Hermes source for web frontend"
rm -rf /tmp/hermes-agent
git clone https://github.com/NousResearch/hermes-agent.git /tmp/hermes-agent

echo "==> Build Hermes dashboard frontend"
cd /tmp/hermes-agent/web
npm install
npm run build

echo "==> Copy built frontend into installed hermes_cli package"
python - <<'PY'
import hermes_cli
import pathlib
import shutil

pkg = pathlib.Path(hermes_cli.__file__).parent
src = pathlib.Path("/tmp/hermes-agent/hermes_cli/web_dist")
dst = pkg / "web_dist"

print("Package:", pkg)
print("Source web_dist:", src)
print("Target web_dist:", dst)

if not src.exists():
    raise SystemExit("web_dist not found after npm build")

if dst.exists():
    shutil.rmtree(dst)

shutil.copytree(src, dst)
print("Copied web_dist OK")
PY
