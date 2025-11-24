from threading import Thread
from flask import Flask, jsonify, request
from server.ms_pagamento.MSPagamento import MSPagamento

app = Flask(__name__)
app.json.sort_keys = False

@app.route("/payment/webhook", methods=["POST"])
def payment_webhook():
    data = request.get_json()

    if not data:
        return jsonify({"erro": "Dados recebidos inválidos"}), 400
    
    try:
        service.process_webhook(data)

        return jsonify({"mensagem": "Notificação processada com sucesso"}), 201
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

if __name__ == "__main__":
    service = MSPagamento()
    Thread(target=service.start_service, daemon=True).start()
    app.run(port=6668, debug=True, use_reloader=False)