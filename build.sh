#!/usr/bin/env bash
set -e

echo "==> Check versions"
python --version
pip --version
node --version || true
npm --version || true

echo "==> Upgrade pip"
pip install --upgrade pip

echo "==> Install existing requirements if any"
if [ -f requirements.txt ]; then
  pip install -r requirements.txt
fi

echo "==> Clone Hermes source"
rm -rf vendor/hermes-agent
mkdir -p vendor
git clone --depth 1 https://github.com/NousResearch/hermes-agent.git vendor/hermes-agent

echo "==> Install Hermes from source with dashboard dependencies"
cd vendor/hermes-agent
pip install -e ".[web,pty]"

echo "==> Build Hermes Dashboard frontend"
cd web
npm install
npm run build

echo "==> Verify frontend build"
cd ..
test -d hermes_cli/web_dist
echo "Frontend build OK"
