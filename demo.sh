#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"
SRC_DIR="$SCRIPT_DIR/src"
PIDS=()

cleanup() {
    echo ""
    echo "Shutting down..."
    for pid in "${PIDS[@]}"; do
        kill "$pid" 2>/dev/null || true
    done
    wait 2>/dev/null || true
    echo "Done."
}
trap cleanup EXIT INT TERM

# ── Python venv ──────────────────────────────────────────────────────
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"
pip install -q -r "$SRC_DIR/requirements.txt"

# ── Ollama (optional) ───────────────────────────────────────────────
MODEL_SIMPLE="qwen2.5:0.5b"
MODEL_COMPLEX="qwen2.5:1.5b"
MODEL_NAME="$MODEL_COMPLEX"
USE_OLLAMA=false

if command -v ollama &>/dev/null; then
    echo "Ollama found — checking models..."
    MODELS_READY=true
    for model in "$MODEL_SIMPLE" "$MODEL_COMPLEX"; do
        if ollama list 2>/dev/null | grep -q "$model"; then
            echo "  $model ready."
        else
            echo "  Pulling $model (this may take a minute)..."
            if ! ollama pull "$model"; then
                echo "  Pull failed for $model."
                MODELS_READY=false
            fi
        fi
    done
    if $MODELS_READY; then
        USE_OLLAMA=true
    else
        echo "Not all models available — falling back to demo mode."
    fi
else
    echo "Ollama not found — running in demo mode (simulated agent responses)."
fi

# ── Environment ──────────────────────────────────────────────────────
if $USE_OLLAMA; then
    export MODEL_ENDPOINT="http://localhost:11434/v1"
    export MODEL_NAME
    export MODEL_SIMPLE
    export MODEL_COMPLEX
    export DEMO_MODE="false"
    echo "Starting agents in LIVE mode (Ollama)..."
else
    export DEMO_MODE="true"
    export MODEL_ENDPOINT=""
    export MODEL_NAME
    export MODEL_SIMPLE
    export MODEL_COMPLEX
    echo "Starting agents in DEMO mode..."
fi

cd "$SRC_DIR"

# ── Auth token (optional) ──────────────────────────────────────────
export AGENT_AUTH_TOKEN="${AGENT_AUTH_TOKEN:-}"

# ── Start MCP tool server ──────────────────────────────────────────
MCP_PORT=8004 python3 -m uvicorn mcp_server:app --host 127.0.0.1 --port 8004 &
PIDS+=($!)
export MCP_SERVER_URL="http://127.0.0.1:8004"

echo -n "Waiting for MCP server..."
for _ in $(seq 1 30); do
    if curl -sf "http://127.0.0.1:8004/health" >/dev/null 2>&1; then
        break
    fi
    sleep 1
    echo -n "."
done
echo " ready."

# ── Start guardrails service ───────────────────────────────────────
GUARDRAILS_PORT=8005 python3 -m uvicorn guardrails:app --host 127.0.0.1 --port 8005 &
PIDS+=($!)
export GUARDRAILS_URL="http://127.0.0.1:8005"

echo -n "Waiting for guardrails..."
for _ in $(seq 1 30); do
    if curl -sf "http://127.0.0.1:8005/health" >/dev/null 2>&1; then
        break
    fi
    sleep 1
    echo -n "."
done
echo " ready."

# ── Start 3 A2A agents ──────────────────────────────────────────────
AGENT_NAME=research AGENT_SKILLS=investigate,summarize AGENT_PORT=8001 \
    python3 -m uvicorn agent:app --host 127.0.0.1 --port 8001 &
PIDS+=($!)

AGENT_NAME=analyst AGENT_SKILLS=analyze,recommend AGENT_PORT=8002 \
    python3 -m uvicorn agent:app --host 127.0.0.1 --port 8002 &
PIDS+=($!)

AGENT_NAME=executor AGENT_SKILLS=execute,report AGENT_PORT=8003 \
    python3 -m uvicorn agent:app --host 127.0.0.1 --port 8003 &
PIDS+=($!)

# Wait for all 3 agents
echo -n "Waiting for agents..."
for port in 8001 8002 8003; do
    for _ in $(seq 1 30); do
        if curl -sf "http://127.0.0.1:$port/health" >/dev/null 2>&1; then
            break
        fi
        sleep 1
        echo -n "."
    done
done
echo " ready."

# ── Semantic Router (llm-d-sc, optional) ─────────────────────────────
USE_SEMANTIC_ROUTER=false
if [ "${ENABLE_SEMANTIC_ROUTER:-false}" = "true" ]; then
    if command -v llm-d-sc-server &>/dev/null || command -v llm-d-sc &>/dev/null; then
        SC_BIN=$(command -v llm-d-sc-server 2>/dev/null || command -v llm-d-sc 2>/dev/null)
        SC_MODEL_DIR="${LLM_D_SC_MODEL_DIR:-$SCRIPT_DIR/../llm-d-semantic-classifier/artifacts/models/complexity}"
        if [ -d "$SC_MODEL_DIR" ] && [ -f "$SC_MODEL_DIR/model.safetensors" ]; then
            LLM_D_SC_MODEL_DIR="$SC_MODEL_DIR" \
            LLM_D_SC_CLASSIFIER=complexity \
            LLM_D_SC_LISTEN=127.0.0.1:50051 \
                "$SC_BIN" &
            PIDS+=($!)
            echo -n "Waiting for semantic router..."
            for _ in $(seq 1 30); do
                if echo > /dev/tcp/127.0.0.1/50051 2>/dev/null; then
                    break
                fi
                sleep 1
                echo -n "."
            done
            echo " ready."
            export SEMANTIC_ROUTER_ENDPOINT="127.0.0.1:50051"
            USE_SEMANTIC_ROUTER=true
        else
            echo "Semantic router model not found at $SC_MODEL_DIR -- skipping."
            echo "Run: ./hack/fetch-model --classifier complexity (in llm-d-semantic-classifier/)"
        fi
    else
        echo "llm-d-sc binary not found -- semantic routing disabled."
        echo "Set ENABLE_SEMANTIC_ROUTER=false or install llm-d-sc to suppress this message."
    fi
fi

# ── Start orchestrator (on :8000) ────────────────────────────────────
export AGENT_URLS="http://127.0.0.1:8001,http://127.0.0.1:8002,http://127.0.0.1:8003"
python3 -m uvicorn orchestrator:app --host 127.0.0.1 --port 8000 &
PIDS+=($!)

echo -n "Waiting for orchestrator..."
for _ in $(seq 1 30); do
    if curl -sf http://127.0.0.1:8000/health >/dev/null 2>&1; then
        echo " ready."
        break
    fi
    sleep 1
    echo -n "."
done

# ── Start Gradio UI (on :7860) ───────────────────────────────────────
export ORCHESTRATOR_URL="http://127.0.0.1:8000"
UI_RUNNING=false
if python3 -c "import gradio" 2>/dev/null; then
    python3 ui.py &
    PIDS+=($!)
    UI_RUNNING=true
else
    echo "WARNING: Gradio requires Python 3.10+. UI skipped — API still available."
fi

echo ""
echo "════════════════════════════════════════════════════════════"
echo "  Multi-Agent Quickstart — running"
echo ""
echo "  MCP Tool Server:  http://127.0.0.1:8004"
echo "  Guardrails:       http://127.0.0.1:8005"
echo "  Research Agent:   http://127.0.0.1:8001"
echo "  Analyst Agent:    http://127.0.0.1:8002"
echo "  Executor Agent:   http://127.0.0.1:8003"
echo "  Orchestrator:     http://127.0.0.1:8000"
if $UI_RUNNING; then
    echo "  Gradio UI:        http://127.0.0.1:7860"
fi
if $USE_SEMANTIC_ROUTER; then
    echo "  Semantic Router:  127.0.0.1:50051 (llm-d-sc complexity)"
fi
echo ""
if $USE_OLLAMA; then
    echo "  Mode: LIVE (Ollama)"
    echo "  Models: $MODEL_SIMPLE (simple) / $MODEL_COMPLEX (complex)"
else
    echo "  Mode: DEMO (simulated agent responses)"
fi
if $USE_SEMANTIC_ROUTER; then
    echo "  Routing: SEMANTIC (llm-d-sc complexity classifier)"
else
    echo "  Routing: DEFAULT (comprehensive workflow)"
fi
if [ -n "$AGENT_AUTH_TOKEN" ]; then
    echo "  Auth:    ENABLED (bearer token)"
else
    echo "  Auth:    DISABLED"
fi
echo "  MCP:     ENABLED (3 tools)"
echo "  Guards:  ENABLED (input/output screening)"
echo "════════════════════════════════════════════════════════════"
echo "Press Ctrl+C to stop."
echo ""

wait
