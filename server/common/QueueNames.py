from enum import Enum

class QueueNames(Enum):
    AUCTION_STARTED = "leilao_iniciado"
    AUCTION_ENDED = "leilao_finalizado"
    BID_VALID = "lance_validado"
    BID_INVALID = "lance_invalidado"
    AUCTION_WINNER = "leilao_vencedor"
    PAYMENT_LINK = "link_pagamento"
    PAYMENT_STATUS = "status_pagamento"
