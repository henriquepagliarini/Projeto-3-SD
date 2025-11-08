from datetime import datetime, timedelta
from typing import Dict, Union
from server.ms_leilao.AuctionStatus import AuctionStatus

TimeConfig = Dict[str, Union[int, float]]

class Auction:
    def __init__(self, id: int, description: str, start_in: TimeConfig, duration: TimeConfig):
        self.config = [start_in, duration]
        self.id = id
        self.description = description
        self.start_date = self.calculate_start_date()
        self.end_date = self.calculate_end_date()
        self.status = AuctionStatus.INACTIVE
        self.highest_bid = 0.0
        self.winner: int = -1

    def parse_time_config(self, time_config: TimeConfig):
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

    def calculate_start_date(self):
        delta = self.parse_time_config(self.config[0])
        return datetime.now() + delta

    def calculate_end_date(self):
        delta = self.parse_time_config(self.config[1])
        return self.start_date + delta

    def open_auction(self):
        if self.status == AuctionStatus.INACTIVE:
            self.status = AuctionStatus.ACTIVE
            return
        raise Exception(f"Não é possível iniciar um lote {self.status}")

    def close_auction(self):
        if self.status == AuctionStatus.ACTIVE:
            self.status = AuctionStatus.CLOSED
            return
        raise Exception(f"Não é possível encerrar um lote {self.status}")