#!/bin/bash
# Script para ejecutar el agente Claude correctamente
# Uso: ./run_agent.sh /ruta/del/proyecto

if [ $# -eq 0 ]; then
    echo "❌ Error: Proporciona la ruta del proyecto"
    echo "Uso: ./run_agent.sh /ruta/del/proyecto"
    exit 1
fi

echo "🚀 Activando virtual environment y ejecutando Claude Agent..."
source .venv/bin/activate && python start_agent.py "$1"