# Gemeo Digital - Qualidade do Ar em Galeria de Mineracao

Sistema de monitoramento de qualidade do ar em galeria subterranea de mineracao, utilizando stack FIWARE completa.

## Arquitetura

```
Publisher (simulacao) -> MQTT (Mosquitto) -> Node-RED (regras) -> Mock Orion (NGSI-v2)
                                                                       |
                                                                  QuantumLeap
                                                                       |
                                                                    CrateDB
                                                                       |
                                                                  Streamlit
```

| Componente | Porta | Funcao |
|------------|-------|--------|
| Mock Orion (Context Broker) | 1026 | API NGSI-v2 compativel (ARM64) |
| Mosquitto | 1883 | Broker MQTT |
| Node-RED | 1880 | Regras de negocio + Dashboard |
| QuantumLeap | 8668 | Serie temporal via subscriptions |
| CrateDB | 4200 | Armazenamento de series temporais |
| Streamlit | 8501 | Indicadores de negocio |

## Inicio Rapido

```bash
# 1. Subir o ambiente
docker compose up -d

# 2. Instalar dashboard do Node-RED
docker compose exec nodered npm install node-red-dashboard@2.23.0
docker compose restart nodered

# 3. Configurar entidade e subscription
./setup_subscription.sh

# 4. Iniciar simulador (em outro terminal)
python publisher.py

# 5. Acessar dashboards
# Node-RED Dashboard: http://localhost:1880/ui
# Streamlit: streamlit run dashboard.py
```

## Sensores

| Sensor | Unidade | Limiar Atencao | Limiar Alerta |
|--------|---------|----------------|---------------|
| CH4 (Metano) | % | > 0.5 | > 1.0 |
| CO (Monoxido de Carbono) | ppm | > 15 | > 25 |
| CO2 (Dioxido de Carbono) | ppm | > 1000 | > 1500 |
| Temperatura | C | > 35 | > 40 |
| Umidade | % | < 40 ou > 85 | - |

## Regra de Negocio

```
SE (CH4 > 1.0%) OU (CO > 25 ppm) ENTAO
  -> Status: "alerta"
  -> Ventilador: LIGADO
  -> Dashboard: indicador vermelho

SENAO SE (CH4 > 0.5%) OU (CO > 15 ppm) ENTAO
  -> Status: "atencao"
  -> Dashboard: indicador amarelo

SENAO
  -> Status: "normal"
  -> Ventilador: DESLIGADO
  -> Dashboard: indicador verde
```

## Visualizacoes

### 1. Operacao ao Vivo (Node-RED Dashboard - http://localhost:1880/ui)
- Gauges de sensores em tempo real (CH4, CO, CO2, Temperatura, Umidade)
- Indicador de status do ventilador (LIGADO/DESLIGADO)
- Indicador de status geral (normal/atencao/alerta)
- **Pergunta respondida:** Qual e o estado atual da qualidade do ar na galeria?

### 2. Indicadores de Negocio (Streamlit - streamlit run dashboard.py)
- % tempo em conformidade NR-33
- Custo de energia da ventilacao
- Numero de incidentes
- Historico de gases e variaveis ambientais
- **Pergunta respondida:** Qual o impacto operacional e economico da qualidade do ar?

## Componentes da Arquitetura

1. **Publisher** (`publisher.py`): Simula sensores com ciclos normais e anomalias
2. **MQTT (Mosquitto)**: Transporte de dados dos sensores
3. **Node-RED** (`flows/flows.json`): Processa mensagens MQTT, aplica regras de negocio, atualiza Orion
4. **Mock Orion** (`orion_mock/`): Context Broker NGSI-v2, armazena estado do gemeo digital
5. **QuantumLeap**: Escuta notificacoes do Orion e persiste em serie temporal
6. **CrateDB**: Banco de dados de series temporais
7. **Streamlit** (`dashboard.py`): Indicadores de negocio e conformidade

## Arquivos

| Arquivo | Descricao |
|---------|-----------|
| `docker-compose.yml` | Stack Docker completa |
| `publisher.py` | Simulador de sensores |
| `mosquitto.conf` | Configuracao do broker MQTT |
| `flows/flows.json` | Fluxo Node-RED |
| `orion_mock/` | Context Broker NGSI-v2 (Python) |
| `setup_subscription.sh` | Configuracao da subscription |
| `dashboard.py` | App Streamlit |
| `requirements.txt` | Dependencias Python |
| `validate.sh` | Validacao ponta a ponta |

## Parar Ambiente

```bash
docker compose down -v
```
