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
    @app.route('/api/<path:path>')
    def missing_env_vars(path=None):
        error_message = {"error": "Credenciais da API não configuradas."}
        return jsonify(error_message), 500


@app.route('/api/documents', methods=['GET'])
def get_documents():
    """
    Busca documentos de TODOS os cofres da conta e junta os resultados.
    """
    print("FUNÇÃO SERVERLESS: Iniciando busca de documentos em todos os cofres...")
    
    # --- ETAPA 1: Buscar todos os cofres ---
    safes_url = f"https://secure.d4sign.com.br/api/v1/safes?tokenAPI={TOKEN_API}&cryptKey={CRYPT_KEY}"
    all_docs = []
    
    try:
        print("Buscando a lista de cofres...")
        safes_response = requests.get(safes_url)
        safes_response.raise_for_status()
        safes = safes_response.json()
        print(f"Encontrados {len(safes)} cofres.")

        # --- ETAPA 2: Iterar sobre cada cofre para buscar os documentos ---
        for safe in safes:
            uuid_safe = safe.get("uuid_safe")
            safe_name = safe.get("name_safe")
            if not uuid_safe:
                continue

            print(f"Buscando documentos no cofre: '{safe_name}'...")
            docs_url = f"https://secure.d4sign.com.br/api/v1/documents/{uuid_safe}/safe?tokenAPI={TOKEN_API}&cryptKey={CRYPT_KEY}"
            
            docs_response = requests.get(docs_url)
            # Usamos um 'continue' para não parar a execução se um cofre estiver vazio ou der erro
            if docs_response.status_code != 200:
                print(f"Aviso: Não foi possível buscar documentos do cofre '{safe_name}' (Status: {docs_response.status_code}).")
                continue
            
            documents_in_safe = docs_response.json()
            all_docs.extend(documents_in_safe) # Adiciona os documentos encontrados à lista principal

        # --- ETAPA 3: Preparar e enviar a resposta final ---
        # Filtra a resposta para enviar apenas os campos necessários, como você já fazia
        documents_data = [
            {"uuidDoc": doc.get("uuidDoc"), "nameDoc": doc.get("nameDoc")}
            for doc in all_docs if doc.get("uuidDoc")
        ]
        
        print(f"Busca finalizada. Enviando um total de {len(documents_data)} documentos de todos os cofres para o front-end.")
        resp = make_response(jsonify(documents_data))
        resp.headers['Cache-Control'] = 's-maxage=300, stale-while-revalidate' # Mantém o cache
        return resp
        
    except requests.exceptions.RequestException as e:
        print(f"ERRO CRÍTICO na nova rotina de busca: {e}")
        return jsonify({"error": "Não foi possível buscar os cofres ou documentos.", "details": str(e)}), 500

@app.route('/api/documents/<uuid_doc>/signers', methods=['GET'])
def get_document_signers(uuid_doc):
    # Esta função não precisa de alteração
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