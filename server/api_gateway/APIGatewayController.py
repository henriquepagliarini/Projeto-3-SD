from threading import Thread
import requests
from flask import Flask, jsonify, request
from flask_sse import sse
from server.api_gateway.APIGateway import APIGateway

app = Flask(__name__)
app.json.sort_keys = False

app.config["REDIS_URL"] = "redis://localhost:6379/0"
app.register_blueprint(sse, url_prefix='/stream')

MS_LEILAO_URL = "http://localhost:6666"
MS_LANCE_URL = "http://localhost:6667"

@app.route("/api/register_channel", methods=["POST"])
def register_channel():
    data = request.get_json()

    if not data:
        return jsonify({"erro": "Dados recebidos inválidos"}), 400

    user_id = data.get("user_id")
    channel = data.get("channel")

    try:
        service.register_sse_channel(user_id, channel)
        return jsonify({"mensagem": f"Canal registrado do usuário {user_id}"}), 201
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


@app.route("/api/register_channel", methods=["DELETE"])
def unregister_channel():
    data = request.get_json()

    if not data:
        return jsonify({"erro": "Dados recebidos inválidos"}), 400

    user_id = data.get("user_id")

    try:
        service.unregister_sse_channel(user_id)
        return jsonify({"mensagem": f"Canal removido do usuário {user_id}"}), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route("/api/interest", methods=["POST"])
def register_interest():
    data = request.get_json()

    if not data:
        return jsonify({"erro": "Dados recebidos inválidos"}), 400

    auction_id = data["auction_id"]
    user_id = data["user_id"]

    try:
        service.register_user_interest(user_id, auction_id)
        return jsonify({"mensagem": f"Cliente {user_id} registrado para notificações do leilão {auction_id}"}), 201
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route("/api/interest", methods=["DELETE"])
def cancel_interest():
    data = request.get_json()

    if not data:
        return jsonify({"erro": "Dados recebidos inválidos"}), 400

    auction_id = data["auction_id"]
    user_id = data["user_id"]

    try:
        service.cancel_user_interest(user_id, auction_id)
        return jsonify({"mensagem": f"Cliente {user_id} cancelou notificações do leilão {auction_id}"}), 201
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

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
    service = APIGateway(app, sse)
    Thread(target=service.start_service, daemon=True).start()
    app.run(port=6660, debug=True, use_reloader=False)