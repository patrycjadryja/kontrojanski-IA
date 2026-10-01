#!/bin/bash
# Instalacja Generatora Agencji na Macu lub Linuksie. Uruchom: bash instaluj.sh
set -e
cd "$(dirname "$0")"
echo "Generator Agencji: instalacja"
command -v python3 >/dev/null || { echo "Brak python3. Zainstaluj Pythona 3.9 lub nowszego i uruchom ponownie."; exit 1; }
if [ ! -d "/Applications/Google Chrome.app" ] && ! command -v google-chrome >/dev/null && ! command -v chromium >/dev/null; then
  echo "Uwaga: nie znaleziono Google Chrome. Jest potrzebny do eksportu grafik. Zainstaluj go przed pierwszym klientem."
fi
[ -d .venv ] || python3 -m venv .venv
.venv/bin/pip install -q --upgrade pip
.venv/bin/pip install -q -r requirements.txt
[ -f agencja.json ] || cp agencja.przyklad.json agencja.json
mkdir -p klienci fonty
SK="$HOME/.claude/skills"
mkdir -p "$SK"
TU="$(pwd)"
for s in skill/*/; do n=$(basename "$s"); mkdir -p "$SK/$n"; sed "s#~/generator-agencji#$TU#g" "$s/SKILL.md" > "$SK/$n/SKILL.md"; done
echo "Skille dla Claude Code: $(ls skill | tr '\n' ' ')"
command -v claude >/dev/null || echo "Uwaga: nie znaleziono programu claude. Zainstaluj Claude Code, zeby zwiad dzialal w tle: https://claude.com/claude-code"
chmod +x panel.sh
echo
echo "Gotowe. Uruchom panel: ./panel.sh"
echo "W Claude Code: /generator-agencji (klienci), 'podlacz serwer' (publikacja), /nowa-nisza (wlasna branza)."
