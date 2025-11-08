from datetime import datetime, timedelta
from typing import Dict, Union
from AuctionStatus import AuctionStatus
from RabbitMQConnection import RabbitMQConnection

TimeConfig = Dict[str, Union[int, float]]

class Auction:
    def __init__(self, id: int, description: str, start_in: TimeConfig, duration: TimeConfig):
        self.config = [start_in, duration]
        self.id = id
        self.description = description
        self.start_date = self.calculateStartDate()
        self.end_date = self.calculateEndDate()
        self.status = AuctionStatus.INACTIVE
        self.highest_bid = 0.0
        self.winner: int = -1

    def parseTimeConfig(self, time_config: TimeConfig):
        delta = timedelta()
        if "days" in time_config:
            delta += timedelta(days=time_config["days"])
        if "hours" in time_config:
            delta += timedelta(hours=time_config["hours"])
        if "minutes" in time_config:
            delta += timedelta(minutes=time_config["minutes"])
        if "seconds" in time_config:
            delta += timedelta(seconds=time_config["seconds"])
        return delta

    def calculateStartDate(self):
        delta = self.parseTimeConfig(self.config[0])
        return datetime.now() + delta

    def calculateEndDate(self):
        delta = self.parseTimeConfig(self.config[1])
        return self.start_date + delta

    def openAuction(self):
        if self.status == AuctionStatus.INACTIVE:
            self.status = AuctionStatus.ACTIVE
            return
        raise Exception(f"Não é possível iniciar um lote {self.status}")

    def closeAuction(self):
        if self.status == AuctionStatus.ACTIVE:
            self.status = AuctionStatus.CLOSED
            return
        raise Exception(f"Não é possível encerrar um lote {self.status}")