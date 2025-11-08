import base64
import json
import os
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256
import pika
from QueueNames import QueueNames
from RabbitMQConnection import RabbitMQConnection

class MSLance:
    def __init__(self):
        print("Configurando MS Lance...")
        self.rabbit = RabbitMQConnection()
        self.rabbit.connect()
        self.rabbit.setupDirectExchange("leiloes")
        self.rabbit.setupFanoutExchange(QueueNames.AUCTION_STARTED.__str__())

        self.active_auctions = {}
        self.public_keys = None
        self.auction_started_queue = None
        self.setupQueues()
        print("MS Lance configurado.")

    def loadPublicKeys(self):
        print("Carregando chaves públicas...")
        keys = {}
        keys_dir = "public_keys"

        if not os.path.exists(keys_dir):
            os.makedirs(keys_dir)
            return keys

        for filename in os.listdir(keys_dir):
            if filename.startswith("user_") and filename.endswith("_public.pem"):
                try:
                    user_id = int(filename.split("_")[1])
                    with open(os.path.join(keys_dir, filename), "rb") as f:
                        keys[user_id] = RSA.import_key(f.read())
                    print(f"Chave pública do usuário {user_id} carregada.")
                except (ValueError, IndexError) as e:
                    print(f"Erro ao processar arquivo {filename}: {e}.")
        return keys

    def setupQueues(self):
        self.rabbit.setupQueue(
            self.rabbit.direct_exchange,
            QueueNames.BID_DONE.__str__(),
            QueueNames.BID_DONE.__str__()
        )
        self.rabbit.setupQueue(
            self.rabbit.direct_exchange,
            QueueNames.BID_VALIDATED.__str__(),
            QueueNames.BID_VALIDATED.__str__()
        )
        self.rabbit.setupQueue(
            self.rabbit.direct_exchange,
            QueueNames.AUCTION_WINNER.__str__(),
            QueueNames.AUCTION_WINNER.__str__()
        )
        self.auction_started_queue = self.rabbit.setupAnonymousQueue(self.rabbit.fanout_exchange)

    def consumeEvent(self):
        try:
            self.rabbit.channel.basic_consume(
                queue=self.auction_started_queue,
                on_message_callback=self.processAuctionStarted,
                auto_ack=True
            )

            self.rabbit.channel.basic_consume(
                queue=QueueNames.AUCTION_ENDED.__str__(),
                on_message_callback=self.processAuctionEnded,
                auto_ack=True,
            )

            self.rabbit.channel.basic_consume(
                queue=QueueNames.BID_DONE.__str__(),
                on_message_callback=self.processBid,
                auto_ack=True,
            )
            self.rabbit.channel.start_consuming()
        except Exception as e:
            print(f"Erro no consumo de eventos do MS Lance: {e}.")

    def publishEvent(self, event: dict, routing_key: str):
        self.rabbit.channel.basic_publish(
            exchange=self.rabbit.direct_exchange,
            routing_key=routing_key,
            body=json.dumps(event, default=str),
            properties=pika.BasicProperties(delivery_mode=2)
        )

    def processAuctionStarted(self, ch, method, properties, body):
        try:
            auction_data = json.loads(body)
            auction_id = int(auction_data["auction_id"])
            self.active_auctions[auction_id] = {
                "highest_bid": float(auction_data.get("highest_bid")),
                "winner": auction_data.get("winner")
            }
        except Exception as e:
            print(f"Erro ao processar leilão iniciado: {e}.")

    def processAuctionEnded(self, ch, method, properties, body):
        try:
            auction_data = json.loads(body)
            auction_id = int(auction_data["auction_id"])
            a = self.active_auctions.get(auction_id)
            winner = a.get("winner")
            highest_bid = a.get("highest_bid")
            
            if winner != -1:
                event = {
                    "auction_id": auction_id,
                    "user_id": winner,
                    "highest_bid": highest_bid
                }
                print(f"        Vencedor: {winner} - R${highest_bid:.2f}.")
                self.publishEvent(event, QueueNames.AUCTION_WINNER.__str__())
            else:
                print(f"        Sem lances.")
            del self.active_auctions[auction_id]
        except Exception as e:
            print(f"Erro ao processar leilão finalizado: {e}.")

    def processBid(self, ch, method, properties, body):
        try:
            bid_data = json.loads(body)
            auction_id = int(bid_data["auction_id"])
            user_id = int(bid_data["user_id"])
            value = float(bid_data["value"])
            signature = base64.b64decode(bid_data["signature"])

            if not self.validateBid(bid_data, auction_id, user_id, value, signature):
                return
            
            self.active_auctions[auction_id]["highest_bid"] = value
            self.active_auctions[auction_id]["winner"] = user_id

            event = {
                "auction_id": auction_id,
                "user_id": user_id,
                "value": value
            }
            self.publishEvent(event, QueueNames.BID_VALIDATED.__str__())
            print(f"Lance validado: Leilão {auction_id}, Usuário {user_id}, R${value:.2f}.")
        except Exception as e:
            print(f"Erro ao processar lance: {e}.")

    def validateBid(self, bid_data, auction_id: int, user_id: int, value: float, signature):
        self.public_keys = self.loadPublicKeys()
        if auction_id not in self.active_auctions:
            print(f"Lance rejeitado: Leilão {auction_id} não está ativo.")
            return False

        if user_id not in self.public_keys:
            print(f"Lance rejeitado: Chave pública do usuário {user_id} não encontrada.")
            return False

        try:
            temp_bid = {
                "auction_id": int(auction_id),
                "user_id": int(user_id),
                "value": float(value)
            }
            signed_data = json.dumps(temp_bid).encode()
            h = SHA256.new(signed_data)
            pkcs1_15.new(self.public_keys[user_id]).verify(h, signature)
        except (ValueError, TypeError):
            print(f"Lance rejeitado: Assinatura inválida do usuário {user_id}.")
            return False

        highest_bid = self.active_auctions[auction_id].get("highest_bid")
        if value <= highest_bid:
            print(f"Lance rejeitado: Valor {value} menor ou igual ao atual {highest_bid}.")
            return False
        return True

    def startService(self):
        print("Iniciando MS Lance...")
        print("--------------------------------")
        try:
            print("Aguardando leilões e lances...")
            self.consumeEvent()
        except KeyboardInterrupt:
            print("MS Lance interrompido.")
        except Exception as e:
            print(f"Erro no MS Lance: {e}.")
        finally:
            self.rabbit.disconnect()
            print("MS Lance terminado com sucesso.")