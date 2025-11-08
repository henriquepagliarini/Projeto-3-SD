from enum import Enum

class QueueNames(Enum):
    AUCTION_STARTED = "leilao_iniciado"
    AUCTION_ENDED = "leilao_finalizado"
    BID_DONE = "lance_realizado"
    BID_VALIDATED = "lance_validado"
    AUCTION_WINNER = "leilao_vencedor"

    def __str__(self):
        return self.value
