import streamlit as st
from pathlib import Path
import time


FILES_FOLDER = Path(__file__).parent / "files"

def create_chain_chat():
    st.session_state.chain = True
    time.sleep(1)
    pass

def sidebar():
    """ Sidebar for navigation Everything ran here will be executed in the sidebar"""
    st.sidebar.title("Navigation")
    uploaded_pdfs = st.file_uploader("Adicione as preoposições em PDF aqui",
                     type=".pdf", 
                     key="pdf_file",
                     accept_multiple_files=True
                     )
    if uploaded_pdfs is not None:
        for file in FILES_FOLDER.glob("*.pdf"):
            file.unlink()
        for pdf in uploaded_pdfs:
            with open(FILES_FOLDER / pdf.name, "wb") as file:
                file.write(pdf.read())
                
    label_button = 'Iniciar ChatBot'
    if 'chain' in st.session_state:
        label_button = 'Atualizar ChatBot'
    if st.button(label_button, use_container_width=True):
        if len(list(FILES_FOLDER.glob("*.pdf"))) == 0:
            st.error("Nenhum arquivo PDF foi carregado. Adicione um arquivo PDF iniciar o chatbot.")
        else:
            st.success("Iniciando chatbot...")
            create_chain_chat()
            st.rerun()

def main():
   with st.sidebar:
         sidebar()
    
if __name__ == "__main__":
    main()