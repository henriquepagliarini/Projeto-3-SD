from enum import Enum

class AuctionStatus(Enum):
    INACTIVE = "Inativo"
    ACTIVE = "Ativo"
    CLOSED = "Encerrado"

    def __str__(self):
        return self.value
