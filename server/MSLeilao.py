from datetime import datetime
import json
import time
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
import pika
from Auction import Auction
from QueueNames import QueueNames
from RabbitMQConnection import RabbitMQConnection

class MSLeilao:
    def __init__(self):
        print("Configurando MS Leilão...")
        self.rabbit = RabbitMQConnection()
        self.rabbit.connect()
        self.rabbit.setupDirectExchange("leiloes")
        self.rabbit.setupFanoutExchange(QueueNames.AUCTION_STARTED.__str__())

        self.scheduler = BackgroundScheduler()
        self.setupQueues()
        self.auctions = self.initializeAuctions()
        self.scheduleAuctions()
        print("MS Leilão configurado.")

    def setupQueues(self):
        self.rabbit.setupQueue(
            self.rabbit.direct_exchange, 
            QueueNames.AUCTION_ENDED.__str__(), 
            QueueNames.AUCTION_ENDED.__str__()
        )

    def publishFanout(self, event: dict):
        self.rabbit.channel.basic_publish(
            exchange=self.rabbit.fanout_exchange,
            routing_key="",
            body=json.dumps(event, default=str),
            properties=pika.BasicProperties(delivery_mode=2)
        )
    
    def publishDirect(self, event: dict, routing_key: str = None):
        self.rabbit.channel.basic_publish(
            exchange=self.rabbit.direct_exchange,
            routing_key=routing_key,
            body=json.dumps(event, default=str),
            properties=pika.BasicProperties(delivery_mode=2)
        )

    def initializeAuctions(self) -> list[Auction]:
        auctions = [
            Auction(1, "Celular", {"seconds": 10}, {"seconds": 30}),
            Auction(2, "Televisão", {"seconds": 20}, {"seconds": 40}),
            Auction(3, "Carro", {"seconds": 25}, {"seconds": 40})
        ]
        for auction in auctions:
            self.rabbit.setupQueue(
                self.rabbit.direct_exchange, 
                f"leilao_{auction.id}", 
                f"leilao_{auction.id}"
            )

        print("Leilões inicializados.")
        return auctions

    def scheduleAuctions(self):
        print("Agendando leilões...")
        for auctions in self.auctions:
            self.scheduler.add_job(
                func=self.startAuction,
                trigger=DateTrigger(run_date=auctions.start_date),
                args=[auctions.id],
            )

            self.scheduler.add_job(
                func=self.endAuction,
                trigger=DateTrigger(run_date=auctions.end_date),
                args=[auctions.id]
            )

            print(f"Leilão {auctions.id}: {auctions.description}")
            print(f"Início: {auctions.start_date.strftime("%H:%M:%S")}")
            print(f"Fim: {auctions.end_date.strftime("%H:%M:%S")}\n")
            print("Leilões agendados.")

    def startAuction(self, auction_id: int):
        auction = self.findAuctionById(auction_id)
        if not auction:
            return
        
        try:
            auction.openAuction()
            event = {
                "auction_id": auction.id,
                "description": auction.description,
                "start_date": auction.start_date.isoformat(),
                "end_date": auction.end_date.isoformat(),
                "status": auction.status.__str__(),
                "highest_bid": auction.highest_bid,
                "winner": auction.winner
            }
            self.publishFanout(event)
            print(f"    Leilão {auction.id} iniciado: {auction.description}.")
        except Exception as e:
            print(f"Erro ao iniciar leilão {auction.id}: {e}")

    def endAuction(self, auction_id: int):
        auction = self.findAuctionById(auction_id)
        if not auction:
            return
        
        try:
            auction.closeAuction()
            event = {
                "auction_id": auction.id,
                "description": auction.description,
                "start_date": auction.start_date.isoformat(),
                "end_date": auction.end_date.isoformat(),
                "status": auction.status.__str__(),
            }
            self.publishDirect(event, QueueNames.AUCTION_ENDED.__str__())
            print(f"    Leilão {auction.id} finalizado: {auction.description}.")
        except Exception as e:
            print(f"Erro ao finalizar leilão {auction.id}: {e}")

    def findAuctionById(self, auction_id: int) -> Auction | None:
        for auction in self.auctions:
            if auction.id == auction_id:
                return auction
        return None

    def startService(self):
        self.scheduler.start()
        print("Scheduler iniciado.")
        print("Iniciando MS Leilão...")
        time.sleep(3)
        print(f"Agora são {datetime.now().strftime('%H:%M:%S')}\n")
        print("Leilões agendados:")
        for auction in self.auctions:
            time_to_start = (auction.start_date - datetime.now()).total_seconds()
            print(f"    Leilão {auction.id}: {auction.description} inicia em {time_to_start:.0f}s.")

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