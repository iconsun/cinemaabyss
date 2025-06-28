from flask import Flask, request, jsonify
from kafka import KafkaProducer, KafkaConsumer
from threading import Thread
from json import dumps, loads
from os import environ

app = Flask(__name__)
brokers = environ.get("KAFKA_BROKERS")
topics = {"movie": "movie-events", "payment": "payment-events", "user": "user-events"}
producer = KafkaProducer(bootstrap_servers=brokers)

def consume(topic):
    for m in KafkaConsumer(topic, bootstrap_servers=brokers, enable_auto_commit=True):
        print(f"[{topic}] {loads(m.value.decode())}")

@app.route('/api/events/<key>', methods=['POST'])
def send(key):
    topic = topics.get(key)
    if not topic: return jsonify(status="failure"), 404
    producer.send(topic, dumps(request.json).encode())
    return jsonify(status="success"), 201

@app.route('/api/events/health')
def health(): return jsonify(status=True)

if __name__ == '__main__':
    [Thread(target=consume, args=(t,), daemon=True).start() for t in topics.values()]
    app.run(host='0.0.0.0', port=int(environ.get("PORT", 8082)))
