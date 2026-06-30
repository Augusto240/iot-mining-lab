#!/bin/bash
# Forca anomalia - para publisher, seta valores altos, espera, restaura
DURACAO=${1:-15}
ORION="http://localhost:1026"

echo "=== FORCANDO ANOMALIA POR ${DURACAO}s ==="

# 1. Matar publisher
pkill -f publisher.py 2>/dev/null
sleep 2

# 2. Recriar entidade limpa (garante que existe)
curl -s -X POST "$ORION/v2/entities" \
  -H "Content-Type: application/json" \
  -d '{"id":"Galeria:Ponto1","type":"AirQualitySensor","ch4":{"type":"Number","value":0},"co":{"type":"Number","value":0},"co2":{"type":"Number","value":0},"temperatura":{"type":"Number","value":0},"umidade":{"type":"Number","value":0},"ventilador":{"type":"Boolean","value":false},"status":{"type":"String","value":"normal"}}' > /dev/null 2>&1

sleep 1

# 3. Setar anomalia
curl -s -X PATCH "$ORION/v2/entities/Galeria:Ponto1/attrs" \
  -H "Content-Type: application/json" \
  -d '{"ch4":{"type":"Number","value":1.8},"co":{"type":"Number","value":35},"co2":{"type":"Number","value":1200},"temperatura":{"type":"Number","value":38},"umidade":{"type":"Number","value":75},"ventilador":{"type":"Boolean","value":true},"status":{"type":"String","value":"alerta"}}' > /dev/null 2>&1

sleep 1

# 4. Verificar
VAL=$(curl -s "$ORION/v2/entities/Galeria:Ponto1")
echo "$VAL" | python3 -c "
import sys,json
d=json.load(sys.stdin)
print(f'  CH4={d[\"ch4\"][\"value\"]} CO={d[\"co\"][\"value\"]} Status={d[\"status\"][\"value\"]} Fan={d[\"ventilador\"][\"value\"]}')
print('  ALERTA ATIVO - Dashboard deve mostrar VERMELHO')
" 2>/dev/null || echo "  (entity set, check dashboard)"

echo ""
echo "Aguardando ${DURACAO}s..."

for i in $(seq $DURACAO -1 1); do
    printf "\r  Restam: %ds " $i
    sleep 1
done
echo ""

# 5. Restaurar publisher
echo "Reiniciando publisher..."
python3 publisher.py &
sleep 3
echo "Sistema normalizado."
echo "=== FIM ==="
