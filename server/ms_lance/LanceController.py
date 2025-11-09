from threading import Thread
import requests
from flask import Flask, jsonify, request
from server.ms_lance.MSLance import MSLance

app = Flask(__name__)
app.json.sort_keys = False

@app.route("/lances", methods=["POST"])
def make_bid():
    data = request.get_json()

    if not data:
        return jsonify({"erro": "Dados recebidos inválidos"}), 400
    
    try:
        service.process_bid(data)

        return jsonify({"mensagem": "Lance enviado com sucesso"}), 201
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

if __name__ == "__main__":
    service = MSLance()
    Thread(target=service.start_service, daemon=True).start()
    app.run(port=6667, debug=True, use_reloader=False)