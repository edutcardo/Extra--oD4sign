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
    Busca TODOS os documentos da conta, sem filtro de cofre.
    Esta é a busca mais ampla possível.
    """
    print("FUNÇÃO SERVERLESS: Buscando TODOS os documentos da conta...")
    url = f"https://secure.d4sign.com.br/api/v1/documents?tokenAPI={TOKEN_API}&cryptKey={CRYPT_KEY}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        all_docs = response.json()
        
        # Filtra a resposta para enviar apenas os campos necessários ao front-end
        documents_data = [
            {"uuidDoc": doc.get("uuidDoc"), "nameDoc": doc.get("nameDoc")}
            for doc in all_docs if doc.get("uuidDoc")
        ]
        
        print(f"Enviando um total de {len(documents_data)} documentos para o front-end.")
        resp = make_response(jsonify(documents_data))
        # Adiciona um cache para não sobrecarregar a API a cada recarga da página
        resp.headers['Cache-Control'] = 's-maxage=300, stale-while-revalidate'
        return resp
        
    except requests.exceptions.RequestException as e:
        print(f"ERRO CRÍTICO ao buscar documentos: {e}")
        return jsonify({"error": "Não foi possível buscar os documentos da conta.", "details": str(e)}), 500


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