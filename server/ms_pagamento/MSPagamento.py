import json
import threading
import time
import pika
import requests
from server.common.QueueNames import QueueNames
from server.common.RabbitMQConnection import RabbitMQConnection


class MSPagamento:
    def __init__(self):
        print("Configurando MS Pagamento...")
        self.rabbit = RabbitMQConnection()
        self.rabbit.connect()
        self.rabbit.setup_direct_exchange("pagamentos")
        self.setup_queues()
        print("MS Pagamento configurado.")

    def setup_queues(self):
        self.rabbit.setup_queue(
            self.rabbit.direct_exchange,
            QueueNames.PAYMENT_LINK.value,
            QueueNames.PAYMENT_LINK.value
        )
        self.rabbit.setup_queue(
            self.rabbit.direct_exchange,
            QueueNames.PAYMENT_STATUS.value,
            QueueNames.PAYMENT_STATUS.value
        )

    def consume_event(self):
        rabbit_consumer = RabbitMQConnection()
        rabbit_consumer.connect()
        rabbit_consumer.setup_direct_exchange("lances")

        rabbit_consumer.setup_queue(
            rabbit_consumer.direct_exchange,
            QueueNames.AUCTION_WINNER.value,
            QueueNames.AUCTION_WINNER.value
        )

        try:
            rabbit_consumer.channel.basic_consume(
                queue=QueueNames.AUCTION_WINNER.value,
                on_message_callback=self.process_auction_winner,
                auto_ack=True
            )

            rabbit_consumer.channel.start_consuming()
        except Exception as e:
            print(f"Erro no consumo de eventos do MS Pagamento: {e}.")
        finally:
            rabbit_consumer.disconnect()

    def publish_event(self, event: dict, routing_key: QueueNames):
        self.rabbit.channel.basic_publish(
            exchange=self.rabbit.direct_exchange,
            routing_key=routing_key.value,
            body=json.dumps(event, default=str),
            properties=pika.BasicProperties(delivery_mode=2)
        )

    def process_auction_winner(self, ch, method, properties, body):
        data = json.loads(body)
        auction_id = data["auction_id"]
        user_id = data["user_id"]
        amount = data["highest_bid"]

        payment_request = {
            "auction_id": auction_id,
            "user_id": user_id,
            "amount": amount,
            "currency": "BRL",
            "callback_url": "http://localhost:6668/payment/webhook"
        }
        response = requests.post("http://localhost:7777/create_payment_url", json=payment_request).json()

        event = {
            "auction_id": auction_id,
            "user_id": user_id,
            "amount": amount,
            "payment_url": response["payment_url"]
        }

        print(f"Link de pagamento gerado para usuário {user_id} do leilão {auction_id}.")
        self.publish_event(event, QueueNames.PAYMENT_LINK)

    def process_webhook(self, data):
        event = {
            "transaction_id": data["transaction_id"],
            "auction_id": data["auction_id"],
            "user_id": data["user_id"],
            "amount": data["amount"],
            "status": data["status"]
        }

        self.publish_event(event, QueueNames.PAYMENT_STATUS)
        print(f"Status de pagamento publicado para o usuário {data["user_id"]} do leilão {data["auction_id"]}.")

    def start_service(self):
        print("Iniciando MS Pagamento...")
        print("--------------------------------")
        try:
            print("Aguardando leilões com vencedores...")
            consumer_thread = threading.Thread(target=self.consume_event, daemon=True)
            consumer_thread.start()

            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("MS Pagamento interrompido.")
        except Exception as e:
            print(f"Erro no MS Pagamento: {e}.")
        finally:
            self.rabbit.disconnect()
            print("MS Pagamento terminado com sucesso.")