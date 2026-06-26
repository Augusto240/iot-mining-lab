from flask import Flask, request, jsonify
import requests as req
import time
import threading
from socketserver import ThreadingTCPServer, BaseRequestHandler
import json

app = Flask(__name__)

entities = {}
subscriptions = []
lock = threading.Lock()

@app.route('/version', methods=['GET'])
def version():
    return jsonify({
        "orion": {
            "version": "3.10.1-mock",
            "uptime": f"{int(time.time())}s",
            "note": "Python mock for ARM64 compatibility"
        }
    })

@app.route('/v2/entities', methods=['POST'])
def create_entity():
    with lock:
        entity = request.json
        entities[entity['id']] = entity
    return '', 204

@app.route('/v2/entities', methods=['GET'])
def list_entities():
    with lock:
        return jsonify(list(entities.values()))

@app.route('/v2/entities/<path:entity_id>', methods=['GET'])
def get_entity(entity_id):
    with lock:
        if entity_id in entities:
            return jsonify(entities[entity_id])
    return jsonify({"error": "entity not found"}), 404

@app.route('/v2/entities/<path:entity_id>/attrs', methods=['PATCH'])
def update_entity(entity_id):
    with lock:
        if entity_id not in entities:
            entities[entity_id] = {"id": entity_id, "type": "Unknown"}

        attrs = request.json
        for key, val in attrs.items():
            entities[entity_id][key] = val

        current = dict(entities[entity_id])

    for sub in subscriptions:
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
        sub = request.json
        subscriptions.append(sub)
    return '', 204

@app.route('/v2/subscriptions', methods=['GET'])
def get_subscriptions():
    with lock:
        result = []
        for i, s in enumerate(subscriptions):
            entry = dict(s)
            entry['id'] = str(i)
            result.append(entry)
    return jsonify(result)

@app.route('/v2/subscriptions/<sub_id>', methods=['GET'])
def get_subscription(sub_id):
    with lock:
        idx = int(sub_id)
        if 0 <= idx < len(subscriptions):
            entry = dict(subscriptions[idx])
            entry['id'] = sub_id
            return jsonify(entry)
    return jsonify({"error": "subscription not found"}), 404

@app.route('/v2/subscriptions/<sub_id>', methods=['DELETE'])
def delete_subscription(sub_id):
    with lock:
        idx = int(sub_id)
        if 0 <= idx < len(subscriptions):
            subscriptions.pop(idx)
            return '', 204
    return jsonify({"error": "subscription not found"}), 404

@app.route('/v2/op/query', methods=['POST'])
def query():
    body = request.json
    entities_list = body.get('entities', [])
    attrs = body.get('attrs', [])
    with lock:
        results = []
        for e in entities_list:
            eid = e.get('id', '')
            if eid in entities:
                if attrs:
                    filtered = {k: entities[eid][k] for k in attrs if k in entities[eid]}
                    filtered['id'] = eid
                    filtered['type'] = entities[eid].get('type', '')
                    results.append(filtered)
                else:
                    results.append(entities[eid])
    return jsonify(results)

@app.route('/notify', methods=['POST'])
def notify():
    return '', 204

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=1026, debug=False, threaded=True, use_reloader=False)
