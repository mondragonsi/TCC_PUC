import streamlit as st
import requests
import re
import base64
import io
import os
from dotenv import load_dotenv
from datetime import datetime

#Bruno

# Importar o Azure Form Recognizer
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential

# Importar o OpenAI
from openai import OpenAI

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

st.set_page_config(page_title="Consulta de Proposições", page_icon="📄")

# Definir a URL base para a API
base_url = "https://dadosabertos.camara.leg.br/api/v2"

def main():
    st.title("Consulta de Proposições - Câmara dos Deputados")
    st.write("Digite os parâmetros da proposição que deseja consultar:")
    
    # Lista pré-definida de 'siglaTipo's
    sigla_tipos = ['PL', 'PEC', 'MPV', 'PDC', 'PDL', 'PLC', 'PLP', 'REQ', 'MSC', 'INC', 'EMC', 'REC']
    
    # Coletar entrada do usuário dentro de um formulário
    with st.form(key='consulta_form'):
        numero = st.number_input("Digite o número da proposição:", min_value=1, value=1)
        ano = st.number_input("Digite o ano da proposição:", min_value=1900, max_value=2100, value=2023)
        sigla_tipo = st.selectbox("Selecione a sigla do tipo da proposição:", sigla_tipos)
        submit_button = st.form_submit_button(label='Consultar')
    
    if submit_button:
        consulta_proposicao(numero, ano, sigla_tipo)

    # Exibir detalhes da proposição e PDF se disponível
    display_proposicao()

def consulta_proposicao(numero, ano, sigla_tipo):
    with st.spinner('Consultando proposições...'):
        params = {
            "ordem": "ASC",
            "ordenarPor": "id",
            "itens": 10,
            "numero": int(numero),
            "ano": int(ano),
            "siglaTipo": sigla_tipo,
        }

        # Buscar proposições
        endpoint = "/proposicoes"
        proposicoes = fetch_proposicoes(base_url, endpoint, params)

        if proposicoes:
            # Exibir um selectbox para o usuário escolher uma proposição
            options = [f"{p.get('id', 'N/A')} - {p.get('ementa', 'Sem Ementa')}" for p in proposicoes]
            selected_option = st.selectbox("Selecione a proposição desejada:", options)
            
            # Obter a proposição selecionada
            selected_index = options.index(selected_option)
            selected_proposicao = proposicoes[selected_index]

            # Armazenar a proposição selecionada no session_state
            st.session_state['selected_proposicao'] = selected_proposicao
        else:
            st.write("Nenhuma proposição encontrada com os parâmetros fornecidos.")

def fetch_proposicoes(base_url, endpoint, params):
    try:
        response = requests.get(f"{base_url}{endpoint}", params=params)
        response.raise_for_status()
        data = response.json()

        proposicoes = []
        if "dados" in data and len(data["dados"]) > 0:
            for proposicao in data["dados"]:
                proposicoes.append(proposicao)
            return proposicoes
        else:
            return None

    except requests.exceptions.RequestException as e:
        st.write(f"Erro na requisição: {e}")
        return None

def display_proposicao():
    # Verificar se uma proposição foi selecionada
    if 'selected_proposicao' in st.session_state:
        selected_proposicao = st.session_state['selected_proposicao']
        # Exibir detalhes da proposição
        id_proposicao = selected_proposicao.get("id", "N/A")
        uri_proposicao = selected_proposicao.get("uri", "N/A")
        sigla_tipo = selected_proposicao.get("siglaTipo", "N/A")
        cod_tipo = selected_proposicao.get("codTipo", "N/A")
        numero_proposicao = selected_proposicao.get("numero", "N/A")
        ano_proposicao = selected_proposicao.get("ano", "N/A")
        ementa = selected_proposicao.get("ementa", "N/A")

        st.write(f"**ID:** {id_proposicao}")
        st.write(f"**URI:** {uri_proposicao}")
        st.write(f"**Tipo:** {sigla_tipo}")
        st.write(f"**Código:** {cod_tipo}")
        st.write(f"**Número:** {numero_proposicao}")
        st.write(f"**Ano:** {ano_proposicao}")
        st.write(f"**Ementa:** {ementa}")
        st.write("---")

        # Buscar informações detalhadas
        response = requests.get(uri_proposicao)
        text = response.text

        # Extrair 'urlInteiroTeor'
        match = re.search(r'"urlInteiroTeor":"(.*?)"', text)
        if match:
            url_inteiro_teor = match.group(1).replace('\\', '')
            st.write(f"**URL do Inteiro Teor:** {url_inteiro_teor}")

            # Exibir o PDF dentro do app
            st.write("Visualização do Inteiro Teor:")
            pdf_response = requests.get(url_inteiro_teor)
            if pdf_response.status_code == 200:
                pdf_bytes = pdf_response.content

                # Armazenar o PDF no session_state
                st.session_state['pdf_bytes'] = pdf_bytes

                # Converter bytes do PDF para base64
                base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')

                # Incorporar PDF em HTML
                pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf"></iframe>'

                st.markdown(pdf_display, unsafe_allow_html=True)

                # Botão "Resumir com IA" na tela principal
                resumir_button_clicked = st.button("Resumir com IA")

                if resumir_button_clicked:
                    resumir_com_ia()
            else:
                st.write("Não foi possível carregar o PDF do inteiro teor.")
        else:
            st.write("Não foi possível encontrar o URL do inteiro teor.")

def resumir_com_ia():
    with st.spinner('Extraindo texto do PDF e resumindo...'):
        try:
            # Extrair texto do PDF usando Azure Form Recognizer
            st.write("Iniciando extração do texto com Azure Form Recognizer...")
            # Configurar o cliente do Azure Form Recognizer
            endpoint = os.environ.get("AZURE_ENDPOINT")
            key = os.environ.get("AZURE_KEY")
            if not endpoint or not key:
                st.error("Chaves do Azure não configuradas. Verifique seu arquivo .env.")
                st.stop()

            document_analysis_client = DocumentAnalysisClient(
                endpoint=endpoint, credential=AzureKeyCredential(key)
            )

            pdf_bytes = st.session_state.get('pdf_bytes', None)
            if pdf_bytes is None:
                st.error("PDF não encontrado. Por favor, consulte uma proposição primeiro.")
                return

            # Chamar a função analyze_general_documents para obter o conteúdo do texto
            text_content = analyze_general_documents(document_analysis_client, pdf_bytes)

            if text_content:
                st.write("Texto extraído com sucesso. Iniciando resumo com OpenAI...")

                # Truncar o texto se necessário
                max_tokens = 4096
                if len(text_content) > max_tokens * 4:
                    text_content = text_content[:max_tokens * 4]

                # Preparar o log de mensagens
                message_log = [
                    {
                        "role": "system",
                        "content": "Você é um assistente que ajuda a população brasileira a entender melhor as proposições da Câmara dos Deputados. Por favor, resuma e simplifique o texto do inteiro teor da proposição a seguir. Use uma linguagem acessível e clara e também considere analfabetos funcionais. Adicione no final, uma conclusão de como essa proposição pode afetar a vida das pessoas."
                    },
                    {
                        "role": "user",
                        "content": text_content
                    }
                ]

                # Chamar a API da OpenAI
                summary = send_message(message_log)

                st.subheader("Resumo da Proposição:")
                st.write(summary)
            else:
                st.write("Não foi possível extrair texto do PDF.")
        except Exception as e:
            st.write(f"Erro ao processar o PDF: {e}")

def send_message(message_log):
    # Chamar a API da OpenAI para obter o resumo
    
    api_key = os.environ.get("OPENAI_API_KEY")
    
    if not api_key:
        st.error("Chave da OpenAI não configurada. Verifique seu arquivo .env.")
        st.stop()
    
    client = OpenAI(api_key=api_key)
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=message_log,
        max_tokens=4096
    )
    
    for choice in response.choices:
        if "text" in choice:
            return choice.text
    return response.choices[0].message.content

def analyze_general_documents(document_analysis_client, pdf_bytes):
    try:
        poller = document_analysis_client.begin_analyze_document(
            "prebuilt-document", document=pdf_bytes
        )
        result = poller.result()

        st.write("Analisando documento...")
        st.write(f"Documento tem {len(result.pages)} páginas.")

        # Extrair o conteúdo do texto do resultado
        text_content = ""
        for page in result.pages:
            # st.write(f"--- Analisando página #{page.page_number} ---")
            # st.write(
            #     f"A página tem largura: {page.width} e altura: {page.height}, medida em unidades: {page.unit}"
            # )
            for line_idx, line in enumerate(page.lines):
                #st.write(f"Linha #{line_idx}: '{line.content}'")
                text_content += line.content + "\n"

        return text_content

    except Exception as e:
        st.write(f"Ocorreu um erro durante a análise do documento: {e}")
        return None

if __name__ == "__main__":
    main()
