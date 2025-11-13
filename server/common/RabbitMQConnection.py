import pika
import time

class RabbitMQConnection:
    def __init__(self):
        self.connection = None
        self.channel = None
        self.direct_exchange = None
        self.fanout_exchange = None

    def connect(self):
        retry_delay = 5
        while True:
            try:
                params = pika.ConnectionParameters(
                    host="localhost",
                    heartbeat=60,
                    blocked_connection_timeout=30,
                )
                self.connection = pika.BlockingConnection(params)
                self.channel = self.connection.channel()
                print("Conectado com sucesso ao RabbitMQ.")
                break
            except Exception as e:
                print(f"Erro ao conectar ao RabbitMQ: {e}. Tentando novamente em {retry_delay}s...")
                time.sleep(retry_delay)

    def disconnect(self):
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            print("Conexão fechada.")
        else:
            print("Conexão já estava fechada.")

    def setup_direct_exchange(self, exchange: str):
        self.direct_exchange = exchange
        self.channel.exchange_declare(
            exchange=exchange, 
            exchange_type="direct"
        )
        print(f"Exchange direct '{exchange}' criada.")

    def setup_fanout_exchange(self, exchange: str):
        self.fanout_exchange = exchange
        self.channel.exchange_declare(
            exchange=exchange, 
            exchange_type="fanout" 
        )
        print(f"Exchange fanout '{exchange}' criada.")

    def setup_queue(self, exchange: str, queue: str, routing_key: str):
        self.channel.queue_declare(
            queue=queue
        )
        self.channel.queue_bind(
            exchange=exchange,
            queue=queue,
            routing_key=routing_key
        )
        print(f"Fila '{queue}' declarada e vinculada.")
    
    def setup_anonymous_queue(self, exchange: str) -> str:
        queue = self.channel.queue_declare(
            queue="", 
            exclusive=True, 
            auto_delete=True
        )
        queue_name = queue.method.queue
        self.channel.queue_bind(
            exchange=exchange,
            queue=queue_name
        )
        print(f"Fila anônima '{queue_name}' declarada e vinculada.")
        return queue_name