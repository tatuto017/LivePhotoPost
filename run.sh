#!/bin/bash
set -e
infisical run -- uv run python -m src.main "$@"
