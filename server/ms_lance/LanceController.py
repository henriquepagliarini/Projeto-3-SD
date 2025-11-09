from threading import Thread
from flask import Flask, jsonify, request
from server.ms_lance.MSLance import MSLance

app = Flask(__name__)
app.json.sort_keys = False

@app.route("/lance", methods=["POST"])
def make_bid():
    data = request.get_json()

    if not data:
        return jsonify({"erro": "Dados recebidos inválidos"})
    
    try:
        service.process_bid(data)

        return jsonify({"mensagem": "Lance enviado com sucesso"}), 201
    except Exception as e:
        return jsonify({"erro": str(e)}), 400

if __name__ == "__main__":
    service = MSLance()
    Thread(target=service.start_service, daemon=True).start()
    app.run(port=6667, debug=True, use_reloader=False)