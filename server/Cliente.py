import base64
import json
import os
import threading
import time
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
import pika
from QueueNames import QueueNames
from RabbitMQConnection import RabbitMQConnection

class Cliente:
    def __init__(self, user_id: int, user_name: str):
        print("Configurando cliente...")
        self.user_id = user_id
        self.user_name = user_name
        self.private_key = None
        self.public_key = None
        self.selected_auctions = set()
        self.generateKeys()

        self.rabbit = RabbitMQConnection()
        self.rabbit.connect()
        self.rabbit.setupDirectExchange("leiloes")
        self.rabbit.setupFanoutExchange(QueueNames.AUCTION_STARTED.__str__())
        print(f"Cliente {self.user_id} configurado: {self.user_name}.")

    def generateKeys(self):
        print("Gerando chaves...")
        key = RSA.generate(2048)
        self.private_key = key
        self.public_key = key.publickey()

        key_path = "public_keys"
        os.makedirs(key_path, exist_ok=True)

        with open(f"{key_path}/user_{self.user_id}_public.pem", "wb") as f:
            f.write(self.public_key.export_key())
        print("Chaves geradas.")

    def signMessage(self, message):
        print("Assinando mensagem...")
        ordered_message = {
            "auction_id": int(message["auction_id"]),
            "user_id": int(message["user_id"]),
            "value": float(message["value"])
        }
        data = json.dumps(ordered_message).encode()
        h = SHA256.new(data)
        signature = pkcs1_15.new(self.private_key).sign(h)
        print("Mensagem assinada.")
        return base64.b64encode(signature).decode()

    def consumeStartedAuction(self):
        rabbit_consumer = RabbitMQConnection()
        rabbit_consumer.connect()
        rabbit_consumer.setupFanoutExchange(QueueNames.AUCTION_STARTED.__str__())
        auction_started_queue = rabbit_consumer.setupAnonymousQueue(rabbit_consumer.fanout_exchange)
        try:
            rabbit_consumer.channel.basic_consume(
                queue=auction_started_queue,
                on_message_callback=self.processStartedAuction,
                auto_ack=True
            )

            rabbit_consumer.channel.start_consuming()
        except Exception as e:
            print(f"Erro no consumidor de leilões iniciados: {e}.")
        finally:
            rabbit_consumer.disconnect()
            print("Consumidor de leilões iniciados finalizado.")

    def processStartedAuction(self, ch, method, properties, body):
        try:
            auction = json.loads(body)
            auction_id = int(auction["auction_id"])
            if auction_id in self.selected_auctions:
                return

            print(f"\nNOVO LEILÃO INICIADO!")
            print(f"  ID: {auction_id}")
            print(f"  Descrição: {auction["description"]}")
            print(f"  Início: {auction["start_date"]}")
            print(f"  Fim: {auction["end_date"]}")

        except Exception as e:
            print(f"Erro ao processar leilão iniciado: {e}.")

    def placeBid(self, auction_id: int, value: float):
        bid = {
            "auction_id": auction_id,
            "user_id": self.user_id,
            "value": value,
        }
        bid["signature"] = self.signMessage(bid)

        self.rabbit.channel.basic_publish(
            exchange=self.rabbit.direct_exchange,
            routing_key=QueueNames.BID_DONE.__str__(),
            body=json.dumps(bid),
            properties=pika.BasicProperties(delivery_mode=2)
        )
        print("Lance enviado.")
        if auction_id not in self.selected_auctions:
            self.consumeSelectedAuction(auction_id)

    def consumeSelectedAuction(self, auction_id: int):
        self.selected_auctions.add(auction_id)
        t = threading.Thread(target=self.taskStarter, args=(auction_id,), daemon=True)
        t.start()

    def taskStarter(self, auction_id: int):
        consumer_rabbit = RabbitMQConnection()
        consumer_rabbit.connect()
        consumer_rabbit.setupDirectExchange("leiloes")
        try:
            queue_name = f"cliente_{self.user_id}_leilao_{auction_id}"
            consumer_rabbit.setupQueue(consumer_rabbit.direct_exchange, queue_name, f"leilao_{auction_id}")
            consumer_rabbit.channel.basic_consume(
                queue=queue_name,
                on_message_callback=self.processAuctionNotification,
                auto_ack=True
            )
            consumer_rabbit.channel.start_consuming()
            print(f"Ouvindo notificações para o leilão {auction_id}.")
        except Exception as e:
            print(f"Erro no consumidor do leilão {auction_id}: {e}.")
        finally:
            consumer_rabbit.disconnect()
            print(f"Consumidor do leilão {auction_id} finalizado.")

    def processAuctionNotification(self, ch, method, properties, body):
        try:
            event = json.loads(body)
            if event["type"] == "lance_realizado":
                print(f"Leilão {event['auction_id']} - Novo lance: user {event['user_id']} = R${event['value']:.2f}.")
            elif event["type"] == "leilao_finalizado":
                print(f"Leilão {event['auction_id']} - ENCERRADO - Vencedor: user {event['user_id']} por R${event['highest_bid']:.2f}.")
            else:
                print(f"Formato de notificação desconhecido.")
        except Exception as e:
            print(f"Erro ao processar notificação: {e}.")

    def startService(self):
        print(f"Iniciando cliente {self.user_name}...")
        print("--------------------------------")
        try:
            consume_thread = threading.Thread(target=self.consumeStartedAuction, daemon=True)
            consume_thread.start()
            print("Aguardando leilões...")
            time.sleep(1)

            while True:
                print("\nOpções:")
                print("1. Fazer lance em um leilão")
                print("2. Sair")
                choice = input("Escolha uma opção: ")
                
                if choice == "1":
                    try:
                        auction_id = int(input("ID do leilão: "))
                        value = float(input("Valor do lance (R$): "))
                        self.placeBid(auction_id, value)
                    except ValueError:
                        print("Valores inválidos.")
                elif choice == "2":
                    print("Saindo...")
                    break
                else:
                    print("Opção inválida!")
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nCliente interrompido.")
        finally:
            self.rabbit.disconnect()
            print("Cliente finalizado.")

if __name__ == "__main__":
    try:
        user_id = int(input("Digite seu ID de usuário: "))
        user_name = input("Digite seu nome: ")
        
        if not user_id or not user_name:
            print("ID e nome são obrigatórios.")
            exit(1)

        cliente = Cliente(user_id, user_name)
        cliente.startService()
        
    except ValueError:
        print("ID deve ser um número.")
    except Exception as e:
        print(f"Erro ao iniciar cliente: {e}.")