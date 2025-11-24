import threading
import time
from flask import Flask, jsonify, request
import random
import requests

app = Flask(__name__)
app.json.sort_keys = False
transactions = {}

@app.route("/create_payment_url", methods=["POST"])
def create_payment_url():
    data = request.get_json()

    if not data:
        return jsonify({"erro": "Dados recebidos inválidos"}), 400
    
    transaction_id = len(transactions) + 1
    transactions[transaction_id] = data

    payment_url = f"http://localhost:7777/pay/{transaction_id}"

    def async_notification():
        time.sleep(3)

        status = "APROVADO" if random.random() < 0.65 else "RECUSADO"

        webhook_content = {
            "transaction_id": transaction_id,
            "auction_id": data["auction_id"],
            "user_id": data["user_id"],
            "amount": data["amount"],
            "status": status
        }

        print(f"Enviando webhook com status: {status}")
        requests.post(data["callback_url"], json=webhook_content)
        
    threading.Thread(target=async_notification, daemon=True).start()
    return jsonify({"payment_url": payment_url}), 200

if __name__ == "__main__":
    app.run(port=7777, debug=True, use_reloader=False)
