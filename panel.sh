#!/bin/bash
# Uruchamia panel Generatora Agencji i otwiera go w przegladarce.
cd "$(dirname "$0")"
PORT="${1:-8900}"
if curl -s -o /dev/null "http://localhost:$PORT/api/stan"; then
  echo "Panel juz dziala: http://localhost:$PORT"
else
  nohup .venv/bin/python -m silnik panel "$PORT" > panel/panel.log 2>&1 &
  sleep 1
  echo "Panel uruchomiony: http://localhost:$PORT"
fi
command -v open >/dev/null && open "http://localhost:$PORT"
