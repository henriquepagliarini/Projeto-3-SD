from enum import Enum

class QueueNames(Enum):
    AUCTION_STARTED = "leilao_iniciado"
    AUCTION_ENDED = "leilao_finalizado"
    BID_VALIDATED = "lance_validado"
    BID_INVALIDATED = "lance_invalidado"
    AUCTION_WINNER = "leilao_vencedor"
    PAYMENT_LINK = "link_pagamento"
    PAYMENT_STATUS = "status_pagamento"

    def __str__(self):
        return self.value
