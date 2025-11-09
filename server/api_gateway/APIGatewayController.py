import os
from threading import Thread
import requests
from flask import Flask, jsonify, request
from server.api_gateway.APIGateway import APIGateway

app = Flask(__name__)
app.json.sort_keys = False

MS_LEILAO_URL = "http://localhost:6666"
MS_LANCE_URL = "http://localhost:6667"

@app.route("/api/leiloes", methods=["GET"])
def get_auctions():
    try:
        response = requests.get(
            f"{MS_LEILAO_URL}/leiloes",
        )
        
        return jsonify(response.json()), response.status_code
        
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route("/api/leiloes", methods=["POST"])
def create_auction():
    data = request.get_json()

    if not data:
        return jsonify({"erro": "Dados recebidos inválidos"}), 400
    
    try:
        response = requests.post(
            f"{MS_LEILAO_URL}/leiloes",
            json=data
        )

        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route("/api/lances", methods=["POST"])
def place_bid():
    data = request.get_json()
    
    if not data:
        return jsonify({"erro": "Dados inválidos"}), 400
    
    try:
        response = requests.post(
            f"{MS_LANCE_URL}/lances",
            json=data
        )
        
        return jsonify(response.json()), response.status_code
        
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

if __name__ == "__main__":
    service = APIGateway()
    Thread(target=service.start_service, daemon=True).start()
    app.run(port=6660, debug=True, use_reloader=False)