from flask import Flask, request, jsonify
import requests as req
import time
import threading
import json
import os

app = Flask(__name__)

DATA_FILE = '/tmp/orion_data.json'

@app.after_request
def add_cors(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PATCH, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

lock = threading.Lock()

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {"entities": {}, "subscriptions": []}

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f)

@app.route('/version', methods=['GET'])
def version():
    return jsonify({"orion": {"version": "3.10.1-mock", "uptime": f"{int(time.time())}s"}})

@app.route('/v2/entities', methods=['POST'])
def create_entity():
    with lock:
        data = load_data()
        entity = request.json
        data["entities"][entity['id']] = entity
        save_data(data)
    return '', 204

@app.route('/v2/entities', methods=['GET'])
def list_entities():
    with lock:
        data = load_data()
        return jsonify(list(data["entities"].values()))

@app.route('/v2/entities/<path:entity_id>', methods=['GET'])
def get_entity(entity_id):
    with lock:
        data = load_data()
        if entity_id in data["entities"]:
            return jsonify(data["entities"][entity_id])
    return jsonify({"error": "entity not found"}), 404

@app.route('/v2/entities/<path:entity_id>', methods=['DELETE'])
def delete_entity(entity_id):
    with lock:
        data = load_data()
        if entity_id in data["entities"]:
            del data["entities"][entity_id]
            save_data(data)
    return '', 204

@app.route('/v2/entities/<path:entity_id>/attrs', methods=['PATCH'])
def update_entity(entity_id):
    with lock:
        data = load_data()
        if entity_id not in data["entities"]:
            data["entities"][entity_id] = {"id": entity_id, "type": "Unknown"}

        attrs = request.json
        for key, val in attrs.items():
            data["entities"][entity_id][key] = val

        current = dict(data["entities"][entity_id])
        subs = data.get("subscriptions", [])
        save_data(data)

    for sub in subs:
        url = sub.get('notification', {}).get('http', {}).get('url', '')
        if url:
            notification = {"data": [current]}
            t = threading.Thread(target=send_notification, args=(url, notification))
            t.daemon = True
            t.start()

    return '', 204

def send_notification(url, payload):
    try:
        req.post(url, json=payload, timeout=2)
    except Exception:
        pass

@app.route('/v2/subscriptions', methods=['POST'])
def create_subscription():
    with lock:
        data = load_data()
        data.setdefault("subscriptions", []).append(request.json)
        save_data(data)
    return '', 204

@app.route('/v2/subscriptions', methods=['GET'])
def get_subscriptions():
    with lock:
        data = load_data()
        result = []
        for i, s in enumerate(data.get("subscriptions", [])):
            entry = dict(s)
            entry['id'] = str(i)
            result.append(entry)
    return jsonify(result)

@app.route('/v2/subscriptions/<sub_id>', methods=['GET'])
def get_subscription(sub_id):
    with lock:
        data = load_data()
        idx = int(sub_id)
        subs = data.get("subscriptions", [])
        if 0 <= idx < len(subs):
            entry = dict(subs[idx])
            entry['id'] = sub_id
            return jsonify(entry)
    return jsonify({"error": "not found"}), 404

@app.route('/v2/subscriptions/<sub_id>', methods=['DELETE'])
def delete_subscription(sub_id):
    with lock:
        data = load_data()
        idx = int(sub_id)
        subs = data.get("subscriptions", [])
        if 0 <= idx < len(subs):
            subs.pop(idx)
            save_data(data)
    return '', 204

@app.route('/v2/op/query', methods=['POST'])
def query():
    body = request.json
    entities_list = body.get('entities', [])
    attrs = body.get('attrs', [])
    with lock:
        data = load_data()
        results = []
        for e in entities_list:
            eid = e.get('id', '')
            if eid in data["entities"]:
                ent = data["entities"][eid]
                if attrs:
                    filtered = {k: ent[k] for k in attrs if k in ent}
                    filtered['id'] = eid
                    filtered['type'] = ent.get('type', '')
                    results.append(filtered)
                else:
                    results.append(ent)
    return jsonify(results)

@app.route('/notify', methods=['POST'])
def notify():
    return '', 204

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=1026, debug=False, threaded=True, use_reloader=False)
