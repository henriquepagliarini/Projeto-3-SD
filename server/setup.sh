echo "Configurando ambiente virtual..."

python3 -m venv venv

source venv/bin/activate
export PYTHONPATH="$PYTHONPATH:$(pwd)"
echo "Ambiente virtual ativado!"

echo "Instalando dependências..."
pip install -r requirements.txt

echo "Ambiente configurado!"
echo "Ative o ambiente com: source venv/bin/activate"