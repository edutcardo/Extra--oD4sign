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
        error_message = {"error": "Credenciais da API não configuradas. Verifique as Variáveis de Ambiente no painel da Vercel."}
        return jsonify(error_message), 500

@app.route('/api/documents', methods=['GET'])
def get_documents():
    """Busca a lista completa de documentos da D4Sign."""
    url = f"https://secure.d4sign.com.br/api/v1/documents?tokenAPI={TOKEN_API}&cryptKey={CRYPT_KEY}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        all_docs = response.json()
        
        documents_data = [
            {"uuidDoc": doc.get("uuidDoc"), "nameDoc": doc.get("nameDoc")}
            for doc in all_docs if doc.get("uuidDoc")
        ]
        
        resp = make_response(jsonify(documents_data))
        # Adiciona cache de 5 minutos para esta resposta na Vercel
        resp.headers['Cache-Control'] = 's-maxage=300, stale-while-revalidate'
        return resp
        
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/documents/<uuid_doc>/signers', methods=['GET'])
def get_document_signers(uuid_doc):
    """Busca os signatários de um documento específico."""
    url = f"https://secure.d4sign.com.br/api/v1/documents/{uuid_doc}/list?tokenAPI={TOKEN_API}&cryptKey={CRYPT_KEY}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        resp = make_response(jsonify(data))
        # Garante que os detalhes dos signatários nunca fiquem em cache
        resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        return resp
        
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500