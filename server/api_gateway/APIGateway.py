import json
import os
import time
from flash_sse import sse
from server.common.QueueNames import QueueNames
from server.common.RabbitMQConnection import RabbitMQConnection

class APIGateway:
    def __init__(self, app):
        print("Configurando API Gateway...")
        self.lances_rabbit = RabbitMQConnection()
        self.pagamentos_rabbit = RabbitMQConnection()

        self.lances_rabbit.connect()
        self.pagamentos_rabbit.connect()

        self.lances_rabbit.setup_direct_exchange("lances")
        self.pagamentos_rabbit.setup_direct_exchange("pagamentos")

        self.setup_queues()
        print("API Gateway configurado.")

    def setup_queues(self):
        self.lances_rabbit.setup_queue(
            self.lances_rabbit.direct_exchange,
            QueueNames.BID_VALID.value,
            QueueNames.BID_VALID.value
        )
        self.lances_rabbit.setup_queue(
            self.lances_rabbit.direct_exchange,
            QueueNames.BID_INVALID.value,
            QueueNames.BID_INVALID.value
        )
        self.lances_rabbit.setup_queue(
            self.lances_rabbit.direct_exchange,
            QueueNames.AUCTION_WINNER.value,
            QueueNames.AUCTION_WINNER.value
        )

        self.pagamentos_rabbit.setup_queue(
            self.pagamentos_rabbit.direct_exchange,
            QueueNames.PAYMENT_LINK.value,
            QueueNames.PAYMENT_LINK.value
        )
        self.pagamentos_rabbit.setup_queue(
            self.pagamentos_rabbit.direct_exchange,
            QueueNames.PAYMENT_STATUS.value,
            QueueNames.PAYMENT_STATUS.value
        )

    def consume_event(self):
        self.lances_rabbit.channel.basic_consume(
            queue=QueueNames.BID_VALID.value,
            on_message_callback=self.process_bid_valid,
            auto_ack=True
        )
        self.lances_rabbit.channel.basic_consume(
            queue=QueueNames.BID_INVALID.value,
            on_message_callback=self.process_bid_invalid,
            auto_ack=True
        )
        self.lances_rabbit.channel.basic_consume(
            queue=QueueNames.AUCTION_WINNER.value,
            on_message_callback=self.process_auction_winner,
            auto_ack=True
        )

        self.pagamentos_rabbit.channel.basic_consume(
            queue=QueueNames.PAYMENT_LINK.value,
            on_message_callback=self.process_payment_link,
            auto_ack=True
        )
        self.pagamentos_rabbit.channel.basic_consume(
            queue=QueueNames.PAYMENT_STATUS.value,
            on_message_callback=self.process_payment_status,
            auto_ack=True
        )

        self.lances_rabbit.channel.start_consuming()
        self.pagamentos_rabbit.channel.start_consuming()

    def process_bid_valid(self, ch, method, properties, body):
        try:
            data = json.loads(body)
            auction_id = data["auction_id"]
            
            print(f"SSE: Novo lance válido no leilão {auction_id}")
            
        except Exception as e:
            print(f"Erro ao processar lance válido: {e}")


    def process_bid_invalid(self, ch, method, properties, body):
        try:
            data = json.loads(body)
            user_id = data["user_id"]
            
            print(f"SSE: Lance inválido do user {user_id}")
            
        except Exception as e:
            print(f"Erro ao processar lance inválido: {e}")

    def process_auction_winner(self, ch, method, properties, body):
        try:
            data = json.loads(body)
            auction_id = data["auction_id"]
            user_id = data["user_id"]
            
            print(f"SSE: User {user_id} vencedor do leilão {auction_id}")
            
        except Exception as e:
            print(f"Erro ao processar vencedor: {e}")

    def process_payment_link(self, ch, method, properties, body):
        try:
            data = json.loads(body)
            user_id = data["user_id"]
            
            print(f"SSE: Link de pagamento para user {user_id}")
            
        except Exception as e:
            print(f"Erro ao processar link de pagamento: {e}")

    def process_payment_status(self, ch, method, properties, body):
        try:
            data = json.loads(body)
            user_id = data["user_id"]
            status = data["status"]
            
            print(f"SSE: Status de pagamento ({status}) do user {user_id}")
            
        except Exception as e:
            print(f"Erro ao processar status de pagamento: {e}")

    def start_service(self):
        print("Iniciando API Gateway...")
        print("--------------------------------")
        try:
            print("Aguardando eventos...")
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("API Gateway interrompido.")
        except Exception as e:
            print(f"Erro no API Gateway: {e}.")
        finally:
            self.lances_rabbit.disconnect()
            self.pagamentos_rabbit.disconnect()
            print("MAPI Gateway terminado com sucesso.")