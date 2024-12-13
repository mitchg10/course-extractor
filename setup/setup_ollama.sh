#!/bin/bash

# Wait for Ollama service to be ready
echo "Waiting for Ollama service..."
timeout=120  # 2 minutes timeout
elapsed=0
until curl -s http://${OLLAMA_HOST}:11434/api/tags > /dev/null; do
    if [ $elapsed -ge $timeout ]; then
        echo "Timeout waiting for Ollama service"
        exit 1
    fi
    sleep 5
    elapsed=$((elapsed + 5))
    echo "Still waiting for Ollama... ($elapsed seconds elapsed)"
done

# Pull the model if not already present
echo "Checking for LLM model..."
if ! curl -s http://${OLLAMA_HOST}:11434/api/tags | grep -q "${OLLAMA_MODEL}"; then
    echo "Pulling ${OLLAMA_MODEL} model..."
    curl -X POST http://${OLLAMA_HOST}:11434/api/pull -d "{\"name\": \"${OLLAMA_MODEL}\"}"
fi

echo "Ollama setup complete!"