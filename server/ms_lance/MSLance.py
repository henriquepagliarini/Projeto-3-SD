import json
import threading
import time
import pika
from server.common.QueueNames import QueueNames
from server.common.RabbitMQConnection import RabbitMQConnection

class MSLance:
    def __init__(self):
        print("Configurando MS Lance...")
        self.rabbit = RabbitMQConnection()
        self.rabbit.connect()
        self.rabbit.setup_direct_exchange("lances")
        self.setup_queues()

        self.active_auctions = {}
        print("MS Lance configurado.")

    def setup_queues(self):
        self.rabbit.setup_queue(
            self.rabbit.direct_exchange,
            QueueNames.BID_VALID.value,
            QueueNames.BID_VALID.value
        )
        self.rabbit.setup_queue(
            self.rabbit.direct_exchange,
            QueueNames.BID_INVALID.value,
            QueueNames.BID_INVALID.value
        )
        self.rabbit.setup_queue(
            self.rabbit.direct_exchange,
            QueueNames.AUCTION_WINNER.value,
            QueueNames.AUCTION_WINNER.value
        )

    def consume_event(self):
        rabbit_consumer = RabbitMQConnection()
        rabbit_consumer.connect()
        rabbit_consumer.setup_direct_exchange("leiloes")

        rabbit_consumer.setup_queue(
            rabbit_consumer.direct_exchange,
            QueueNames.AUCTION_STARTED.value,
            QueueNames.AUCTION_STARTED.value
        )
        rabbit_consumer.setup_queue(
            rabbit_consumer.direct_exchange,
            QueueNames.AUCTION_ENDED.value,
            QueueNames.AUCTION_ENDED.value
        )

        try:
            rabbit_consumer.channel.basic_consume(
                queue=QueueNames.AUCTION_STARTED.value,
                on_message_callback=self.process_auction_started,
                auto_ack=True
            )

            rabbit_consumer.channel.basic_consume(
                queue=QueueNames.AUCTION_ENDED.value,
                on_message_callback=self.process_auction_ended,
                auto_ack=True,
            )
            rabbit_consumer.channel.start_consuming()
        except Exception as e:
            print(f"Erro no consumo de eventos do MS Lance: {e}.")
        finally:
            rabbit_consumer.disconnect()

    def publish_event(self, event: dict, routing_key: QueueNames):
        self.rabbit.channel.basic_publish(
            exchange=self.rabbit.direct_exchange,
            routing_key=routing_key.value,
            body=json.dumps(event, default=str),
            properties=pika.BasicProperties(delivery_mode=2)
        )

    def process_auction_started(self, ch, method, properties, body):
        try:
            auction_data = json.loads(body)
            auction_id = int(auction_data["auction_id"])
            self.active_auctions[auction_id] = {
                "highest_bid": float(auction_data["highest_bid"]),
                "winner": int(auction_data["winner"])
            }
            print(f"Leilão {auction_id} iniciado e aceitando lances.")
        except Exception as e:
            print(f"Erro ao processar leilão iniciado: {e}.")

    def process_auction_ended(self, ch, method, properties, body):
        try:
            auction_data = json.loads(body)
            auction_id = int(auction_data["auction_id"])

            a = self.active_auctions[auction_id]
            winner = a["winner"]
            highest_bid = a["highest_bid"]
            
            if winner != -1:
                event = {
                    "auction_id": auction_id,
                    "user_id": winner,
                    "highest_bid": highest_bid
                }
                print(f"Leilão {auction_id} finalizado. Vencedor: {winner} - R${highest_bid:.2f}.")
                self.publish_event(event, QueueNames.AUCTION_WINNER)
            else:
                print(f"Leilão {auction_id} finalizado sem vencedor.")
            del self.active_auctions[auction_id]
        except Exception as e:
            print(f"Erro ao processar leilão finalizado: {e}.")

    def process_bid(self, body):
        try:
            auction_id = int(body["auction_id"])
            user_id = int(body["user_id"])
            value = float(body["value"])

            event = {
                "auction_id": auction_id,
                "user_id": user_id,
                "value": value
            }

            if not self.validate_bid(auction_id, value):
                self.publish_event(event, QueueNames.BID_INVALID)
                print(f"Lance invalidado: Leilão {auction_id}, Usuário {user_id}, R${value:.2f}.")
                return
            
            self.active_auctions[auction_id]["highest_bid"] = value
            self.active_auctions[auction_id]["winner"] = user_id

            self.publish_event(event, QueueNames.BID_VALID)
            print(f"Lance validado: Leilão {auction_id}, Usuário {user_id}, R${value:.2f}.")
        except Exception as e:
            print(f"Erro ao processar lance: {e}.")

    def validate_bid(self, auction_id: int, value: float):
        if auction_id not in self.active_auctions:
            return False

        if value <= self.active_auctions[auction_id]["highest_bid"]:
            return False
        return True

    def start_service(self):
        print("Iniciando MS Lance...")
        print("--------------------------------")
        try:
            print("Aguardando leilões e lances...")
            consumer_thread = threading.Thread(target=self.consume_event, daemon=True)
            consumer_thread.start()

            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("MS Lance interrompido.")
        except Exception as e:
            print(f"Erro no MS Lance: {e}.")
        finally:
            self.rabbit.disconnect()
            print("MS Lance terminado com sucesso.")