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

# Valida se as variáveis de ambiente foram carregadas corretamente
if not TOKEN_API or not CRYPT_KEY:
    @app.route('/api/<path:path>')
    def missing_env_vars(path=None):
        error_message = {"error": "Credenciais da API não configuradas. Verifique as Variáveis de Ambiente no painel da Vercel."}
        return jsonify(error_message), 500

@app.route('/api/documents', methods=['GET'])
def get_documents():
    """Busca a lista completa de documentos da D4Sign, lidando com paginação de forma segura."""
    all_docs = []
    page = 1
    
    # Adiciona um limite máximo de páginas para evitar loops infinitos acidentais
    MAX_PAGES = 100 

    while page <= MAX_PAGES:
        url = f"https://secure.d4sign.com.br/api/v1/documents?tokenAPI={TOKEN_API}&cryptKey={CRYPT_KEY}&pg={page}"
        try:
            response = requests.get(url)
            response.raise_for_status()
            
            # Verificação crucial: tenta decodificar o JSON.
            # Se a resposta for vazia ou não for um JSON válido (ex: erro), um erro ocorrerá.
            current_page_docs = response.json()
            
            # A API retorna uma lista. Se a lista estiver vazia (ou não for uma lista), paramos.
            if not isinstance(current_page_docs, list) or not current_page_docs:
                break # Condição de parada segura: sai do loop se não houver mais documentos.
                
            all_docs.extend(current_page_docs)
            page += 1
            
        except requests.exceptions.RequestException as e:
            # Se uma requisição falhar (ex: 404, 500), para o processo e retorna o erro.
            print(f"Erro ao buscar a página {page}: {e}")
            return jsonify({"error": f"Erro na comunicação com a API D4Sign na página {page}. Detalhes: {e}"}), 500
        except ValueError:
            # Se a resposta não for um JSON válido (pode acontecer na última página),
            # consideramos que a lista de documentos terminou.
            break

    documents_data = [
        {"uuidDoc": doc.get("uuidDoc"), "nameDoc": doc.get("nameDoc")}
        for doc in all_docs if doc.get("uuidDoc")
    ]
    
    resp = make_response(jsonify(documents_data))
    resp.headers['Cache-Control'] = 's-maxage=300, stale-while-revalidate'
    return resp

@app.route('/api/documents/<uuid_doc>/signers', methods=['GET'])
def get_document_signers(uuid_doc):
    """Busca os signatários de um documento específico."""
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