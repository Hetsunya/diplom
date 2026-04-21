#!/usr/bin/env bash

set -e

# === Backend ===
(
  cd "$(dirname "$0")/emeeting-backend"
  go run ./cmd/server/main.go
) &

# === Frontend ===
(
  cd "$(dirname "$0")/emeeting-ui"
  npm run dev
) &

wait
