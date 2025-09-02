import os
import requests
from flask import Flask, jsonify, abort, make_response
from flask_cors import CORS
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Configura o aplicativo Flask
app = Flask(__name__)
CORS(app)  # Habilita o CORS para permitir chamadas do front-end

# Obtém as credenciais da API das variáveis de ambiente
TOKEN_API = os.getenv('TOKEN_API')
CRYPT_KEY = os.getenv('CRYPT_KEY')

# Validação inicial para garantir que as chaves foram carregadas
if not TOKEN_API or not CRYPT_KEY:
    raise ValueError("Erro: As credenciais TOKEN_API e CRYPT_KEY não foram encontradas no arquivo .env")

# --- Otimização: Cache de Documentos ---
documents_cache = []

def fetch_all_documents():
    """Busca todos os documentos da D4Sign e os armazena em cache."""
    global documents_cache
    print("Buscando e cacheando a lista de documentos da D4Sign...")
    url = f"https://secure.d4sign.com.br/api/v1/documents?tokenAPI={TOKEN_API}&cryptKey={CRYPT_KEY}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        # Filtra e armazena apenas os dados necessários
        all_docs = response.json()
        documents_cache = [
            {"uuidDoc": doc.get("uuidDoc"), "nameDoc": doc.get("nameDoc")}
            for doc in all_docs if doc.get("uuidDoc") and doc.get("nameDoc") != "Matrícula - Luiz Eduardo de Azevedo Cardoso"
        ]
        print(f"{len(documents_cache)} documentos foram carregados com sucesso no cache.")
    except requests.exceptions.RequestException as e:
        print(f"Erro CRÍTICO ao buscar documentos: {e}")
        documents_cache = []

# --- Endpoints da nossa API ---

@app.route('/api/documents', methods=['GET'])
def get_documents():
    """Endpoint que retorna a lista de documentos em cache para o front-end."""
    if not documents_cache:
        fetch_all_documents()
    return jsonify(documents_cache)

@app.route('/api/documents/<uuid_doc>/signers', methods=['GET'])
def get_document_signers(uuid_doc):
    """Endpoint que busca os signatários de um ÚNICO documento sob demanda."""
    print(f"--- NOVA REQUISIÇÃO ---")
    print(f"Buscando signatários para o documento UUID: {uuid_doc}...")
    url = f"https://secure.d4sign.com.br/api/v1/documents/{uuid_doc}/list?tokenAPI={TOKEN_API}&cryptKey={CRYPT_KEY}"
    try:
        response = requests.get(url)
        print(f"D4Sign API Status Code: {response.status_code}")
        response.raise_for_status()
        
        data = response.json()
        print(f"Dados recebidos da D4Sign: {data}")

        # --- MUDANÇA PRINCIPAL: Adicionar cabeçalhos anti-cache ---
        resp = make_response(jsonify(data))
        resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        resp.headers['Pragma'] = 'no-cache'
        resp.headers['Expires'] = '0'
        
        print(f"Enviando resposta para o front-end com sucesso.")
        return resp

    except requests.exceptions.RequestException as e:
        print(f"Erro ao buscar signatários para {uuid_doc}: {e}")
        abort(500, description="Não foi possível buscar os signatários.")

# --- Execução do Servidor ---
if __name__ == '__main__':
    fetch_all_documents()
    app.run(port=5001, debug=True)