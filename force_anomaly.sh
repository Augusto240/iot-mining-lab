#!/bin/bash
# Forca anomalia no sistema - para o publisher, seta valores altos, espera
# Uso: ./force_anomaly.sh [duracao_em_segundos]

DURACAO=${1:-15}
ORION="http://localhost:1026/v2/entities/Galeria:Ponto1/attrs"

echo "=== FORCANDO ANOMALIA POR ${DURACAO}s ==="

# Matar publisher
pkill -f publisher.py 2>/dev/null
sleep 1
echo "Publisher parado."

# Setar valores de anomalia
curl -s -X PATCH "$ORION" \
  -H "Content-Type: application/json" \
  -d '{"ch4":{"type":"Number","value":1.8},"co":{"type":"Number","value":35},"co2":{"type":"Number","value":1200},"temperatura":{"type":"Number","value":38},"umidade":{"type":"Number","value":75},"ventilador":{"type":"Boolean","value":true},"status":{"type":"String","value":"alerta"}}' > /dev/null

echo "Valores de ANOMALIA setados:"
curl -s http://localhost:1026/v2/entities/Galeria:Ponto1 | python3 -c "
import sys,json; d=json.load(sys.stdin)
print(f'  CH4={d[\"ch4\"][\"value\"]} CO={d[\"co\"][\"value\"]} Status={d[\"status\"][\"value\"]} Fan={d[\"ventilador\"][\"value\"]}')"

echo ""
echo "Aguardando ${DURACAO}s..."
echo "Abra o dashboard.html e veja os gauges vermelhos + ventilador girando!"
echo ""

for i in $(seq $DURACAO -1 1); do
    printf "\r  Tempo restante: %ds " $i
    sleep 1
done
echo ""

# Restaurar publisher
echo "Reiniciando publisher..."
python3 publisher.py &
sleep 3
echo "Sistema restaurado."
echo "=== FIM ==="
