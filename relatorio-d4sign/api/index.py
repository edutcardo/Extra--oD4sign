import os
import requests
from flask import Flask, jsonify, make_response
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

TOKEN_API = os.getenv('TOKEN_API')
CRYPT_KEY = os.getenv('CRYPT_KEY')

if not TOKEN_API or not CRYPT_KEY:
    @app.route('/api/<path:path>')
    def missing_env_vars(path=None):
        error_message = {"error": "Credenciais da API não configuradas."}
        return jsonify(error_message), 500

# NOVA ROTA: Retorna apenas a lista de cofres. É rápida e não vai estourar o tempo.
@app.route('/api/safes', methods=['GET'])
def get_safes():
    print("Iniciando busca de cofres...")
    url = f"https://secure.d4sign.com.br/api/v1/safes?tokenAPI={TOKEN_API}&cryptKey={CRYPT_KEY}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        safes = response.json()
        print(f"Encontrados {len(safes)} cofres.")
        resp = make_response(jsonify(safes))
        # Cacheia a lista de cofres por 5 minutos
        resp.headers['Cache-Control'] = 's-maxage=300, stale-while-revalidate'
        return resp
    except Exception as e:
        print(f"ERRO ao buscar cofres: {e}")
        return jsonify({"error": "Não foi possível buscar os cofres.", "details": str(e)}), 500

# NOVA ROTA: Busca todos os documentos (com paginação) de UM cofre específico.
@app.route('/api/safes/<uuid_safe>/documents', methods=['GET'])
def get_documents_from_safe(uuid_safe):
    print(f"Buscando documentos para o cofre {uuid_safe}...")
    all_docs_in_safe = []
    page = 1
    while True:
        try:
            url = f"https://secure.d4sign.com.br/api/v1/documents/{uuid_safe}/safe?tokenAPI={TOKEN_API}&cryptKey={CRYPT_KEY}&pg={page}"
            response = requests.get(url, timeout=15) # Damos um tempo maior por requisição
            response.raise_for_status()
            
            documents_on_page = response.json()
            if not documents_on_page:
                break
            
            all_docs_in_safe.extend(documents_on_page)
            page += 1
        except Exception as e:
            print(f"Erro ao buscar página {page} do cofre {uuid_safe}: {e}")
            break # Se der erro, para de buscar neste cofre
    
    documents_data = [{"uuidDoc": doc.get("uuidDoc"), "nameDoc": doc.get("nameDoc")} for doc in all_docs_in_safe if doc.get("uuidDoc")]
    print(f"Enviando {len(documents_data)} documentos do cofre {uuid_safe}.")
    resp = make_response(jsonify(documents_data))
    # Cacheia os documentos de cada cofre
    resp.headers['Cache-Control'] = 's-maxage=300, stale-while-revalidate'
    return resp

# ROTA ANTIGA de signatários (sem alteração na lógica, apenas na URL para consistência)
@app.route('/api/documents/<uuid_doc>/signers', methods=['GET'])
def get_document_signers(uuid_doc):
    url = f"https://secure.d4sign.com.br/api/v1/documents/{uuid_doc}/list?tokenAPI={TOKEN_API}&cryptKey={CRYPT_KEY}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        resp = make_response(jsonify(data))
        resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        return resp
    except Exception as e:
        return jsonify({"error": str(e)}), 500