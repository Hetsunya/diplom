#!/usr/bin/env bash

set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"

# === Backend ===
(
  cd "$ROOT/code/emeeting-backend"
  go run ./cmd/server/main.go
) &

# === Frontend ===
(
  cd "$ROOT/code/emeeting-ui"
  npm run dev
) &

wait
