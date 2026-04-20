#!/usr/bin/env bash
# Sync shared cursor-memory (run on project open, pre-commit, or cron)
set -e
cd "$(git rev-parse --show-toplevel)/.cursor-memory" && git pull
