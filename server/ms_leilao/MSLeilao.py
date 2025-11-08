from datetime import datetime
import json
import time
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
import pika
from server.ms_leilao.Auction import Auction
from server.common.QueueNames import QueueNames
from server.common.RabbitMQConnection import RabbitMQConnection

class MSLeilao:
    def __init__(self):
        print("Configurando MS Leilão...")
        self.rabbit = RabbitMQConnection()
        self.rabbit.connect()
        self.rabbit.setup_direct_exchange("leiloes")
        self.rabbit.setup_fanout_exchange(QueueNames.AUCTION_STARTED.__str__())

        self.scheduler = BackgroundScheduler()
        self.setup_queues()
        self.auctions = []
        print("MS Leilão configurado.")

    def setup_queues(self):
        self.rabbit.setup_queue(
            self.rabbit.direct_exchange, 
            QueueNames.AUCTION_ENDED.__str__(), 
            QueueNames.AUCTION_ENDED.__str__()
        )

    def publish_fanout(self, event: dict):
        self.rabbit.channel.basic_publish(
            exchange=self.rabbit.fanout_exchange,
            routing_key="",
            body=json.dumps(event, default=str),
            properties=pika.BasicProperties(delivery_mode=2)
        )
    
    def publish_direct(self, event: dict, routing_key: str = None):
        self.rabbit.channel.basic_publish(
            exchange=self.rabbit.direct_exchange,
            routing_key=routing_key,
            body=json.dumps(event, default=str),
            properties=pika.BasicProperties(delivery_mode=2)
        )

    def create_new_auction(self, description: str, start_in, duration):
        new_auction = Auction(len(self.auctions) + 1, description, start_in, duration)
        self.auctions.append(new_auction)

        self.rabbit.setup_queue(
            self.rabbit.direct_exchange,
            f"leilao_{new_auction.id}",
            f"leilao_{new_auction.id}"
        )

        self.scheduler.add_job(
            func=self.start_auction,
            trigger=DateTrigger(run_date=new_auction.start_date),
            args=[new_auction.id],
        )

        self.scheduler.add_job(
            func=self.end_auction,
            trigger=DateTrigger(run_date=new_auction.end_date),
            args=[new_auction.id]
        )

    def start_auction(self, auction_id: int):
        auction = self.find_auction_by_id(auction_id)
        if not auction:
            return
        
        try:
            auction.open_auction()
            event = {
                "auction_id": auction.id,
                "description": auction.description,
                "start_date": auction.start_date.isoformat(),
                "end_date": auction.end_date.isoformat(),
                "status": auction.status.__str__(),
                "highest_bid": auction.highest_bid,
                "winner": auction.winner
            }
            self.publish_fanout(event)
            print(f"    Leilão {auction.id} iniciado: {auction.description}.")
        except Exception as e:
            print(f"Erro ao iniciar leilão {auction.id}: {e}")

    def end_auction(self, auction_id: int):
        auction = self.find_auction_by_id(auction_id)
        if not auction:
            return
        
        try:
            auction.close_auction()
            event = {
                "auction_id": auction.id,
                "description": auction.description,
                "start_date": auction.start_date.isoformat(),
                "end_date": auction.end_date.isoformat(),
                "status": auction.status.__str__(),
            }
            self.publish_direct(event, QueueNames.AUCTION_ENDED.__str__())
            print(f"    Leilão {auction.id} finalizado: {auction.description}.")
        except Exception as e:
            print(f"Erro ao finalizar leilão {auction.id}: {e}")

    def find_auction_by_id(self, auction_id: int) -> Auction | None:
        for auction in self.auctions:
            if auction.id == auction_id:
                return auction
        return None

    def start_service(self):
        self.scheduler.start()
        print("Scheduler iniciado.")
        print("Iniciando MS Leilão...")
        time.sleep(3)
        print(f"Agora são {datetime.now().strftime('%H:%M:%S')}\n")

        try:
            while True:
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("MS Leilão interrompido.")
        except Exception as e:
            print(f"Erro no MS Leilão: {e}.")
        finally:
            self.scheduler.shutdown()
            self.rabbit.disconnect()
            print("MS Leilão terminado com sucesso.")