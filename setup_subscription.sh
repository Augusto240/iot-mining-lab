#!/bin/bash
# Configuração da subscription QuantumLeap no Orion
# Execute após subir os containers: docker compose up -d

ORION_URL="http://localhost:1026"
QL_URL="http://localhost:8668"

echo "=== Configurando Subscription QuantumLeap ==="

# Verificar se Orion está rodando
echo "Verificando Orion..."
until curl -s "$ORION_URL/version" > /dev/null 2>&1; do
    echo "Aguardando Orion..."
    sleep 2
done
echo "Orion OK!"

# Criar entidade no Orion
echo "Criando entidade Galeria:Ponto1..."
curl -s -X POST "$ORION_URL/v2/entities" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "Galeria:Ponto1",
    "type": "AirQualitySensor",
    "ch4": {"type": "Number", "value": 0},
    "co": {"type": "Number", "value": 0},
    "co2": {"type": "Number", "value": 0},
    "temperatura": {"type": "Number", "value": 0},
    "umidade": {"type": "Number", "value": 0},
    "ventilador": {"type": "Boolean", "value": false},
    "status": {"type": "String", "value": "normal"}
  }'

echo ""
echo "Entidade criada!"

# Criar subscription no Orion para QuantumLeap
echo "Criando subscription para QuantumLeap..."
curl -s -X POST "$ORION_URL/v2/subscriptions" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Persiste dados de qualidade do ar no QuantumLeap",
    "subject": {
      "entities": [
        {
          "id": "Galeria:Ponto1",
          "type": "AirQualitySensor"
        }
      ]
    },
    "notification": {
      "http": {
        "url": "http://quantumleap:8668/v2/notify"
      },
      "attrs": ["ch4", "co", "co2", "temperatura", "umidade", "ventilador", "status"]
    },
    "throttling": 5
  }'

echo ""
echo "=== Configuração concluída! ==="
echo ""
echo "Verificar subscription:"
echo "  curl $ORION_URL/v2/subscriptions"
echo ""
echo "Verificar dados no QuantumLeap:"
echo "  curl '$QL_URL/v2/entities/Galeria:Ponto1/attrs'"
