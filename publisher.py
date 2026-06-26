import paho.mqtt.client as mqtt
import json, time, random, math

BROKER = "localhost"
PORT = 1883
TOPIC_BASE = "mineracao/galeria/ponto1"
PUBLISH_INTERVAL = 2

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.connect(BROKER, PORT, 60)
client.loop_start()

anomaly_mode = False
anomaly_start = 0
cycle_start = time.time()

def get_ch4(t, is_anomaly):
    base = 0.2 + 0.1 * math.sin(t * 0.1)
    noise = random.uniform(-0.05, 0.05)
    if is_anomaly:
        anomaly_progress = min((t - anomaly_start) / 5.0, 1.0)
        return round(base + noise + 1.2 * anomaly_progress, 3)
    return round(max(0, base + noise), 3)

def get_co(t, is_anomaly):
    base = 10 + 3 * math.sin(t * 0.15)
    noise = random.uniform(-2, 2)
    if is_anomaly:
        anomaly_progress = min((t - anomaly_start) / 5.0, 1.0)
        return round(base + noise + 25 * anomaly_progress, 1)
    return round(max(0, base + noise), 1)

def get_co2(t):
    base = 600 + 100 * math.sin(t * 0.05)
    noise = random.uniform(-20, 20)
    return round(base + noise, 0)

def get_temperature(t):
    base = 30 + 2 * math.sin(t * 0.08)
    noise = random.uniform(-1, 1)
    return round(base + noise, 1)

def get_humidity(t):
    base = 70 + 5 * math.sin(t * 0.07)
    noise = random.uniform(-3, 3)
    return round(max(0, min(100, base + noise)), 1)

try:
    while True:
        t = time.time() - cycle_start

        elapsed_anomaly = t - anomaly_start if anomaly_mode else 999
        if not anomaly_mode and random.random() < 0.003:
            anomaly_mode = True
            anomaly_start = t
        elif anomaly_mode and elapsed_anomaly > 15:
            anomaly_mode = False

        ch4 = get_ch4(t, anomaly_mode)
        co = get_co(t, anomaly_mode)
        co2 = get_co2(t)
        temp = get_temperature(t)
        humid = get_humidity(t)
        fan = ch4 > 1.0 or co > 25.0

        client.publish(f"{TOPIC_BASE}/ch4", json.dumps({"value": ch4}))
        client.publish(f"{TOPIC_BASE}/co", json.dumps({"value": co}))
        client.publish(f"{TOPIC_BASE}/co2", json.dumps({"value": co2}))
        client.publish(f"{TOPIC_BASE}/temperatura", json.dumps({"value": temp}))
        client.publish(f"{TOPIC_BASE}/umidade", json.dumps({"value": humid}))
        client.publish(f"{TOPIC_BASE}/ventilador", json.dumps({"value": fan}))

        status = "alerta" if (ch4 > 1.0 or co > 25.0) else ("atencao" if (ch4 > 0.5 or co > 15.0) else "normal")
        print(f"[{time.strftime('%H:%M:%S')}] CH4={ch4}% CO={co}ppm CO2={co2}ppm T={temp}C RH={humid}% Fan={fan} Status={status}")

        time.sleep(PUBLISH_INTERVAL)

except KeyboardInterrupt:
    client.loop_stop()
    client.disconnect()
