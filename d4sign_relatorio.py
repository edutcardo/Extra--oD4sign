import requests
import pandas as pd

# 1. Configurar suas credenciais da API
TOKEN_API = 'live_52449bbd01229efbbeaaf4ce6ee511df175bef8707b57ff35604039dc7714c48'
CRYPT_KEY = 'live_crypt_rwJd9DYWs28IYUI1bPhhWDnVtJg5yeb8'

def get_all_documents():
    """
    Função para obter a lista de todos os documentos da sua conta.
    """
    url = f"https://secure.d4sign.com.br/api/v1/documents?tokenAPI={TOKEN_API}&cryptKey={CRYPT_KEY}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Erro ao buscar documentos: {e}")
        return None

def get_signatures_for_document(document_uuid):
    """
    Função para obter a lista de signatários de um documento específico.
    """
    url = f"https://secure.d4sign.com.br/api/v1/documents/{document_uuid}/list?tokenAPI={TOKEN_API}&cryptKey={CRYPT_KEY}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return None

def main():
    """
    Função principal que executa o fluxo completo.
    """
    print("Iniciando a coleta de dados da D4Sign...")

    # --- PASSO 1: Obter a lista de todos os documentos ---
    documents_data_raw = get_all_documents()
    if not documents_data_raw:
        print("Nenhum documento encontrado ou erro na resposta da API. Encerrando.")
        return

    documents_data = documents_data_raw
    all_data = []

    # --- PASSO 2: Iterar sobre os documentos e buscar os dados de contato ---
    for doc in documents_data:
        doc_uuid = doc.get('uuidDoc')
        doc_title = doc.get('nameDoc')

        # Ignora documentos com o nome específico
        if doc_title == "Matrícula - Luiz Eduardo de Azevedo Cardoso":
            continue

        if not doc_uuid:
            continue

        signatures_data = get_signatures_for_document(doc_uuid)

        if signatures_data and 'list' in signatures_data:
            for signature in signatures_data['list']:
                # Pega o nome do signatário e as informações de contato
                signer_name = signature.get('name')
                phone = signature.get('phone')
                whatsapp = signature.get('whatsapp')

                # Se encontrar o telefone ou o WhatsApp, adiciona aos dados
                if phone or whatsapp:
                    all_data.append({
                        'Documento': doc_title,
                        'UUID Documento': doc_uuid,
                        'Nome Signatário': signer_name,
                        'Telefone': phone,
                        'Whatsapp': whatsapp
                    })
        else:
            # Adiciona o documento mesmo que não encontre signatários
            all_data.append({
                'Documento': doc_title,
                'UUID Documento': doc_uuid,
                'Nome Signatário': 'N/A',
                'Telefone': 'N/A',
                'Whatsapp': 'N/A'
            })


    # --- PASSO 3: Criar e exportar a planilha ---
    if all_data:
        df = pd.DataFrame(all_data)
        file_name = 'relatorio_contatos_d4sign.csv'
        df.to_csv(file_name, index=False, encoding='utf-8')
        print(f"\nRelatório gerado com sucesso! Verifique o arquivo '{file_name}' no diretório do script.")
    else:
        print("\nNenhum dado para criar o relatório.")

if __name__ == "__main__":
    main()