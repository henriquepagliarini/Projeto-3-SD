echo "Configurando ambiente virtual..."

python3 -m venv venv

source venv/bin/activate
export PYTHONPATH="$PYTHONPATH:$(pwd)"
echo "Ambiente virtual ativado!"

echo "Instalando dependências..."
pip install -r requirements.txt

echo "Verificando redis..."

if ! command -v redis-server &> /dev/null
then
    echo "Redis não encontrado. Instalando..."
    sudo apt update
    sudo apt install -y redis-server
else
    echo "Redis já instalado."
fi

echo "Iniciando redis..."
sudo service redis-server start

if redis-cli ping | grep -q "PONG"; then
    echo "Redis iniciado com sucesso!"
else
    echo "Erro ao iniciar o Redis. Verifique manualmente."
    exit 1
fi


echo "Ambiente configurado!"
echo "Volte para a pasta raiz e ative o ambiente com: source server/venv/bin/activate"