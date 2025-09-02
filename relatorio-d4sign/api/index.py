import os
import requests
from flask import Flask, jsonify, make_response
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

# A variável 'app' é o que a Vercel irá procurar e usar para servir as requisições
app = Flask(__name__)
CORS(app)

TOKEN_API = os.getenv('TOKEN_API')
CRYPT_KEY = os.getenv('CRYPT_KEY')

# Validação para garantir que as variáveis de ambiente foram carregadas na Vercel
if not TOKEN_API or not CRYPT_KEY:
    # Em um ambiente serverless, é melhor retornar um erro JSON do que quebrar a execução
    @app.route('/api/<path:path>')
    def missing_env_vars(path):
        return jsonify({"error": "Credenciais da API não configuradas nas Variáveis de Ambiente da Vercel."}), 500

@app.route('/api/documents', methods=['GET'])
def get_documents():
    """
    Busca todos os documentos da D4Sign.
    O cache da Vercel (CDN) tornará as chamadas repetidas muito mais rápidas.
    """
    print("FUNÇÃO SERVERLESS: Buscando lista de documentos...")
    url = f"https://secure.d4sign.com.br/api/v1/documents?tokenAPI={TOKEN_API}&cryptKey={CRYPT_KEY}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        all_docs = response.json()
        
        documents_data = [
            {"uuidDoc": doc.get("uuidDoc"), "nameDoc": doc.get("nameDoc")}
            for doc in all_docs if doc.get("uuidDoc") and doc.get("nameDoc") != "Matrícula - Luiz Eduardo de Azevedo Cardoso"
        ]
        
        resp = make_response(jsonify(documents_data))
        # Instrução para a Vercel: guarde essa resposta em cache por 300 segundos (5 minutos)
        resp.headers['Cache-Control'] = 's-maxage=300, stale-while-revalidate'
        return resp
        
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/documents/<uuid_doc>/signers', methods=['GET'])
def get_document_signers(uuid_doc):
    """
    Busca os signatários de um ÚNICO documento sob demanda.
    """
    print(f"FUNÇÃO SERVERLESS: Buscando signatários para {uuid_doc}...")
    url = f"https://secure.d4sign.com.br/api/v1/documents/{uuid_doc}/list?tokenAPI={TOKEN_API}&cryptKey={CRYPT_KEY}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        resp = make_response(jsonify(data))
        # Não queremos cache para os detalhes dos signatários, sempre buscar o mais recente
        resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        resp.headers['Pragma'] = 'no-cache'
        resp.headers['Expires'] = '0'
        return resp
        
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

# O bloco if __name__ == '__main__': é removido, pois a Vercel gerencia a execução.