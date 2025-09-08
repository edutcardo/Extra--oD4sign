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

# Valida se as variáveis de ambiente foram carregadas corretamente na Vercel
if not TOKEN_API or not CRYPT_KEY:
    # Esta rota de erro agora captura qualquer caminho não definido
    @app.route('/<path:path>')
    def missing_env_vars(path=None):
        error_message = {"error": "Credenciais da API não configuradas. Verifique as Variáveis de Ambiente no painel da Vercel."}
        return jsonify(error_message), 500

# --- CORREÇÃO APLICADA AQUI ---
# A rota foi alterada de '/api/documents' para '/documents'
@app.route('/documents', methods=['GET'])
def get_documents():
    """
    Busca documentos especificamente do cofre 'COOPERATIVA'.
    """
    print("FUNÇÃO SERVERLESS: Buscando lista de documentos do cofre 'COOPERATIVA'...")
    
    # --- ETAPA 1: Encontrar o UUID do cofre "COOPERATIVA" ---
    safes_url = f"https://secure.d4sign.com.br/api/v1/safes?tokenAPI={TOKEN_API}&cryptKey={CRYPT_KEY}"
    target_safe_name = "COOPERATIVA"
    uuid_safe = None

    try:
        safes_response = requests.get(safes_url)
        safes_response.raise_for_status()
        safes_data = safes_response.json()

        # O retorno da API de cofres pode não ser uma lista, verificamos o tipo
        if isinstance(safes_data, list):
            for safe in safes_data:
                if safe.get("name_safe") == target_safe_name:
                    uuid_safe = safe.get("uuid_safe")
                    print(f"Encontrado UUID do cofre '{target_safe_name}': {uuid_safe}")
                    break
        else:
             print(f"ERRO: A resposta da API de cofres não foi uma lista. Resposta recebida: {safes_data}")
             return jsonify({"error": "Formato inesperado na resposta da API de cofres."}), 500

        if not uuid_safe:
            print(f"ERRO: Cofre '{target_safe_name}' não foi encontrado na conta.")
            return jsonify({"error": f"O cofre '{target_safe_name}' não foi encontrado."}), 404

    except requests.exceptions.RequestException as e:
        print(f"Erro ao buscar a lista de cofres: {e}")
        return jsonify({"error": "Não foi possível buscar a lista de cofres.", "details": str(e)}), 500

    # --- ETAPA 2: Buscar os documentos usando o UUID do cofre encontrado ---
    docs_url = f"https://secure.d4sign.com.br/api/v1/documents?tokenAPI={TOKEN_API}&cryptKey={CRYPT_KEY}&uuid_safe={uuid_safe}"
    try:
        docs_response = requests.get(docs_url)
        docs_response.raise_for_status()
        all_docs = docs_response.json()
        
        documents_data = [
            {"uuidDoc": doc.get("uuidDoc"), "nameDoc": doc.get("nameDoc")}
            for doc in all_docs if doc.get("uuidDoc")
        ]
        
        print(f"Enviando {len(documents_data)} documentos do cofre '{target_safe_name}'.")
        resp = make_response(jsonify(documents_data))
        resp.headers['Cache-Control'] = 's-maxage=300, stale-while-revalidate'
        return resp
        
    except requests.exceptions.RequestException as e:
        print(f"Erro ao buscar documentos do cofre: {e}")
        return jsonify({"error": "Não foi possível buscar os documentos do cofre.", "details": str(e)}), 500

# --- CORREÇÃO APLICADA AQUI ---
# A rota foi alterada de '/api/documents/<uuid_doc>/signers' para '/documents/<uuid_doc>/signers'
@app.route('/documents/<uuid_doc>/signers', methods=['GET'])
def get_document_signers(uuid_doc):
    # Esta função não precisa de alteração na sua lógica interna
    url = f"https://secure.d4sign.com.br/api/v1/documents/{uuid_doc}/list?tokenAPI={TOKEN_API}&cryptKey={CRYPT_KEY}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        resp = make_response(jsonify(data))
        resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        return resp
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500