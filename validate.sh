#!/bin/bash
# Validacao ponta a ponta do sistema

set -e

ORION_URL="http://localhost:1026"
QL_URL="http://localhost:8668"
NODERED_URL="http://localhost:1880"

echo "=== Validacao Ponta a Ponta ==="
echo ""

echo "1. Verificando containers..."
if docker compose ps | grep -q "Up"; then
    echo "   Containers rodando"
else
    echo "   Containers nao estao rodando"
    exit 1
fi

echo "2. Verificando Mock Orion..."
if curl -s "$ORION_URL/version" | grep -q "orion"; then
    echo "   Mock Orion OK"
else
    echo "   Mock Orion nao acessivel"
    exit 1
fi

echo "3. Verificando entidade Galeria:Ponto1..."
if curl -s "$ORION_URL/v2/entities/Galeria:Ponto1" | grep -q "AirQualitySensor"; then
    echo "   Entidade criada"
else
    echo "   Entidade nao encontrada"
    echo "   Execute: ./setup_subscription.sh"
    exit 1
fi

echo "4. Verificando subscription QuantumLeap..."
if curl -s "$ORION_URL/v2/subscriptions" | grep -q "quantumleap"; then
    echo "   Subscription configurada"
else
    echo "   Subscription nao encontrada"
    echo "   Execute: ./setup_subscription.sh"
    exit 1
fi

echo "5. Verificando Node-RED..."
if curl -s "$NODERED_URL" > /dev/null 2>&1; then
    echo "   Node-RED acessivel"
else
    echo "   Node-RED nao acessivel"
fi

echo "6. Verificando dados no Orion..."
DATA=$(curl -s "$ORION_URL/v2/entities/Galeria:Ponto1/attrs")
if echo "$DATA" | grep -q "ch4"; then
    echo "   Dados presentes no Orion"
    echo "$DATA" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f\"     CH4: {data['ch4']['value']:.3f}%\")
print(f\"     CO: {data['co']['value']:.1f}ppm\")
print(f\"     CO2: {data['co2']['value']:.0f}ppm\")
print(f\"     Temp: {data['temperatura']['value']:.1f}C\")
print(f\"     Umidade: {data['umidade']['value']:.1f}%\")
print(f\"     Ventilador: {data['ventilador']['value']}\")
print(f\"     Status: {data['status']['value']}\")
" 2>/dev/null || echo "     (valores disponiveis)"
else
    echo "   Dados nao encontrados no Orion"
fi

echo "7. Verificando CrateDB..."
COUNT=$(curl -s "http://localhost:4200/_sql" -H "Content-Type: application/json" \
  -d '{"stmt":"SELECT count(*) FROM doc.etairqualitysensor"}' | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(data['rows'][0][0])
" 2>/dev/null || echo "0")
if [ "$COUNT" -gt 0 ]; then
    echo "   CrateDB: $COUNT registros"
else
    echo "   CrateDB sem dados"
fi

echo ""
echo "=== Validacao Concluida! ==="
echo ""
echo "Acessos:"
echo "  Node-RED Dashboard: http://localhost:1880/ui"
echo "  Streamlit: streamlit run dashboard.py"
echo ""
