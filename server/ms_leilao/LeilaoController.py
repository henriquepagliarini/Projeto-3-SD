from threading import Thread
import requests
from flask import Flask, jsonify, request
from server.ms_leilao.MSLeilao import MSLeilao

app = Flask(__name__)
app.json.sort_keys = False

@app.route("/leiloes", methods=["GET"])
def get_auctions():
    auctions = []
    for auction in service.auctions:
        auctions.append({
            "id": auction.id,
            "description": auction.description,
            "start_date": auction.start_date.isoformat(),
            "end_date": auction.end_date.isoformat(),
            "status": auction.status.value,
        })
    return jsonify(auctions), 200

@app.route("/leiloes", methods=["POST"])
def add_auction():
    data = request.get_json()

    if not data:
        return jsonify({"erro": "Dados recebidos inválidos"}), 400
    
    try:
        service.create_new_auction(
            data["description"],
            data["start_in"],
            data["duration"]
        )
        return jsonify({"mensagem": "Leilao criado com sucesso"}), 201
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

if __name__ == "__main__":
    service = MSLeilao()
    Thread(target=service.start_service, daemon=True).start()
    app.run(port=6666, debug=True, use_reloader=False)