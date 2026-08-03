#!/bin/bash
# Strix launcher script for 9router / OpenAI-compatible API proxy
export LLM_API_BASE="${LLM_API_BASE:-http://localhost:20128/v1}"
export STRIX_LLM="${STRIX_LLM:-openai/ag/claude-opus-4-6-thinking}"

if [ -z "$LLM_API_KEY" ]; then
    export LLM_API_KEY="sk-9router-local"
fi

echo "=== Launching Strix AI connected to 9router ==="
echo "LLM_API_BASE: $LLM_API_BASE"
echo "STRIX_LLM: $STRIX_LLM"
echo "============================================="

python3 -m strix.interface.cli "$@"
