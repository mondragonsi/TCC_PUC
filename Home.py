import streamlit as st
from pathlib import Path
import time
from langchain.memory import ConversationBufferMemory


FILES_FOLDER = Path(__file__).parent / "files"

def create_chain_chat() -> None:
    st.session_state.chain = True
    
    
    memory = ConversationBufferMemory(return_messages=True)
    memory.chat_memory.add_user_message('Olá! Sou Usuario! :)')
    memory.chat_memory.add_ai_message('Olá! Como posso te ajudar? Sou uma LLM :)')
    st.session_state.memory = memory
    
    time.sleep(1)
    pass

def sidebar():
    """ Sidebar for navigation Everything ran here will be executed in the sidebar"""
    st.sidebar.title("Proposições Políticas")
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

def chat_window():
    st.header("🇧🇷 ChatBot para Proposições Políticas", divider=True)
    
    if 'chain' not in st.session_state:
        st.error("Nenhum chatbot foi iniciado. Adicione um arquivo PDF para iniciar o chatbot.")
        st.stop() # Stop the script here
        
    # chain = st.session_state.chain
    # memory = st.session_state.memory
    
    memory = st.session_state.memory
    messages = memory.load_memory_variables({})['history']
    
    container = st.container()
    for message in messages:
        chat = container.chat_message(message.type)
        chat.markdown(message.content)
        
    new_message = st.chat_input("Escreva sua pergunta sobre a preposicao")
    if new_message is not None:
        chat = container.chat_message("human")
        chat.markdown(new_message)
        
        chat = container.chat_message("ai")
        chat.markdown('gerando resposta...')
        
        time.sleep(2)
        memory.chat_memory.add_user_message(new_message)
        memory.chat_memory.add_ai_message('OI SOU O CHATBOT LLM aqui de novo!')
        st.rerun()
        
        
    

def main():
   with st.sidebar:
        sidebar()
   chat_window()
    
if __name__ == "__main__":
    main()