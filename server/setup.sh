echo "Configurando ambiente virtual..."

python3 -m venv venv

source venv/bin/activate

echo "Instalando dependências..."
pip install apscheduler pika pycryptodome

echo "Ambiente configurado!"
echo "Ative o ambiente com: source venv/bin/activate"