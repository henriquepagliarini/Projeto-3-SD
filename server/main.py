import threading
import time
from MSLance import MSLance
from MSLeilao import MSLeilao
from MSNotificacao import MSNotificacao

def runMSLeilao():
    try:
        ms_leilao = MSLeilao()
        ms_leilao.startService()
    except Exception as e:
        print(f"Erro no MS Leilão: {e}")

def runMSLance():
    try:
        ms_lance = MSLance()
        ms_lance.startService()
    except Exception as e:
        print(f"Erro no MS Lance: {e}")

def runMSNotificacao():
    try:
        ms_notificacao = MSNotificacao()
        ms_notificacao.startService()
    except Exception as e:
        print(f"Erro no MS Notificação: {e}")

if __name__ == "__main__":
    print("Iniciando sistema de leilão...")
    
    leilao_thread = threading.Thread(target=runMSLeilao, daemon=True)
    lance_thread = threading.Thread(target=runMSLance, daemon=True)
    notificacao_thread = threading.Thread(target=runMSNotificacao, daemon=True)
    
    leilao_thread.start()
    lance_thread.start()
    notificacao_thread.start()

    print("Sistema iniciado. Pressione Ctrl+C para parar.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nParando sistema...")
    finally:
        print("Sistema finalizado")