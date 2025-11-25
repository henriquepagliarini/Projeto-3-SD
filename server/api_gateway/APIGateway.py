import json
import threading
import time
from server.common.QueueNames import QueueNames
from server.common.RabbitMQConnection import RabbitMQConnection

class APIGateway:
    def __init__(self, app, sse):
        print("Configurando API Gateway...")
        self.users = {}
        self.users_channels = {}
        self.app = app
        self.sse = sse

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

    def consume_bids(self):
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
        self.lances_rabbit.channel.start_consuming()
    
    def consume_payments(self):
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
        self.pagamentos_rabbit.channel.start_consuming()

    def process_bid_valid(self, ch, method, properties, body):
        try:
            data = json.loads(body)
            auction_id = data["auction_id"]
            user_id = data["user_id"]
            value = data["value"]
            sse_type = "lance_valido"

            message = {
                "type": sse_type,
                "auction_id": auction_id,
                "user_id": user_id,
                "value": value,
            }
            
            self.sse_to_interested_users(auction_id, sse_type, message)
            print(f"SSE: Novo lance válido no leilão {auction_id}")
            
        except Exception as e:
            print(f"Erro ao processar lance válido: {e}")

    def process_bid_invalid(self, ch, method, properties, body):
        try:
            data = json.loads(body)
            auction_id = data["auction_id"]
            user_id = data["user_id"]
            value = data["value"]
            sse_type = "lance_invalido"
            
            message = {
                "type": sse_type,
                "auction_id": auction_id,
                "user_id": user_id,
                "value": value,
            }
            
            self.sse_to_user(user_id, sse_type, message)
            print(f"SSE: Lance inválido do user {user_id}")
            
        except Exception as e:
            print(f"Erro ao processar lance inválido: {e}")

    def process_auction_winner(self, ch, method, properties, body):
        try:
            data = json.loads(body)
            auction_id = data["auction_id"]
            user_id = data["user_id"]
            highest_bid = data["highest_bid"]
            sse_type = "vencedor_leilao"

            message = {
                "type": sse_type,
                "auction_id": auction_id,
                "user_id": user_id,
                "highest_bid": highest_bid,
            }
            
            self.sse_to_interested_users(auction_id, sse_type, message)
            print(f"SSE: User {user_id} vencedor do leilão {auction_id}")
            
        except Exception as e:
            print(f"Erro ao processar vencedor: {e}")

    def process_payment_link(self, ch, method, properties, body):
        try:
            data = json.loads(body)
            auction_id = data["auction_id"]
            user_id = data["user_id"]
            payment_url = data["payment_url"]
            amount = data["amount"]
            sse_type = "link_pagamento"

            message = {
                "type": sse_type,
                "user_id": user_id,
                "auction_id": auction_id,
                "payment_url": payment_url,
                "amount": amount,
            }
            
            self.sse_to_user(user_id, sse_type, message)
            
            print(f"SSE: Link de pagamento para user {user_id}")
            
        except Exception as e:
            print(f"Erro ao processar link de pagamento: {e}")

    def process_payment_status(self, ch, method, properties, body):
        try:
            data = json.loads(body)
            auction_id = data["auction_id"]
            user_id = data["user_id"]
            status = data["status"]
            amount = data["amount"]
            sse_type = "status_pagamento"

            message = {
                "type": sse_type,
                "user_id": user_id,
                "auction_id": auction_id,
                "status": status,
                "amount": amount,
            }
            
            self.sse_to_user(user_id, sse_type, message)
            print(f"SSE: Status de pagamento ({status}) do user {user_id}")
            
        except Exception as e:
            print(f"Erro ao processar status de pagamento: {e}")

    def sse_to_interested_users(self, auction_id, event_type, data):
        interested_users = []
        auction_key = str(auction_id)

        for user_id, auctions in self.users.items():
            if auction_key in map(str, auctions):
                interested_users.append(user_id)
        
        for user_id in interested_users:
            self.sse_to_user(user_id, event_type, data)

    def sse_to_user(self, user_id, event_type, data):
        try:
            user_key = str(user_id)
            channel = self.users_channels.get(user_key)
            if channel:
                with self.app.app_context():
                    self.sse.publish(
                        data,
                        type=event_type,
                        channel=channel
                    )
                print(f"SSE enviado para usuário {user_id}: {event_type} (channel={channel})")
            else:
                print(f"Usuário {user_id} não tem canal registrado para receber {event_type}")
        except Exception as e:
            print(f"Erro ao enviar SSE para cliente {user_id}: {e}")

    def register_user_interest(self, user_id, auction_id):
        user_key = str(user_id)
        auction_key = str(auction_id)

        if user_key not in self.users:
            self.users[user_key] = set()

        self.users[user_key].add(auction_key)
        print(f"Usuário {user_key} registrou interesse no leilão {auction_key}")

    def cancel_user_interest(self, user_id, auction_id):
        user_key = str(user_id)
        auction_key = str(auction_id)

        if user_key in self.users and auction_key in self.users[user_key]:
            self.users[user_key].remove(auction_key)
            print(f"Usuário {user_key} cancelou interesse no leilão {auction_key}")
    
    def register_sse_channel(self, user_id, channel):
        self.users_channels[str(user_id)] = channel
        print(f"Canal SSE registrado para usuário {user_id}: {channel}")

    def unregister_sse_channel(self, user_id):
        user_key = str(user_id)
        if user_key in self.users_channels:
            del self.users_channels[user_key]
            print(f"Canal SSE removido para usuário {user_id}")

    def start_service(self):
        print("Iniciando API Gateway...")
        print("--------------------------------")
        try:
            bids_thread = threading.Thread(target=self.consume_bids, daemon=True)
            bids_thread.start()
            payments_thread = threading.Thread(target=self.consume_payments, daemon=True)
            payments_thread.start()
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
            print("MPI Gateway terminado com sucesso.")