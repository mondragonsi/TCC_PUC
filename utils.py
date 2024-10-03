from pathlib import Path

import streamlit as st
from langchain_community.document_loaders.pdf import PyPDFLoader
from langchain_community.vectorstores.faiss import FAISS
from langchain.memory import ConversationBufferMemory
from langchain.chains.conversational_retrieval.base import ConversationalRetrievalChain
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_openai.chat_models import ChatOpenAI

from dotenv import load_dotenv, find_dotenv

_ = load_dotenv(find_dotenv())

FILES_FOLDER = Path(__file__).parent / "files"
MODEL_NAME = "gpt-4o-mini"

def document_importer():
    documents = []
    for file in FILES_FOLDER.glob("*.pdf"):
        loader = PyPDFLoader(str(file))
        documents_file = loader.load()
        documents.extend(documents_file)  # Add the documents to the list

    if not documents:
        print("No documents found in the specified directory.")
    else:
        print(f"Loaded {len(documents)} documents from {file}")

    return documents


def split_documents(documents):
    recur_splitter = RecursiveCharacterTextSplitter(
        chunk_size=2500,
        chunk_overlap=250,
        separators=["\n\n", "\n", ".", " ", ""]
    )
    documents = recur_splitter.split_documents(documents)

    for i, doc in enumerate(documents):
        doc.metadata['source'] = doc.metadata['source'].split('/')[1]
        doc.metadata['doc_id'] = i
    return documents


def create_vector_store(documents):
    embeddings_model = OpenAIEmbeddings()
    vector_store = FAISS.from_documents(
        documents=documents,
        embedding=embeddings_model
    )
    return vector_store


def create_chain_chat():
    
    # Run the functions
    documents = document_importer()
    print(f"Number of documents imported: {len(documents)}")
    documents = split_documents(documents)
    print(f"Number of documents after splitting: {len(documents)}")
    
    if documents:
        vector_store = create_vector_store(documents)
        chat = ChatOpenAI(model_name=MODEL_NAME)
        memory = ConversationBufferMemory(
            return_messages=True,
            memory_key='chat_history',
            output_key='answer',
        )

        retriever = vector_store.as_retriever()
        chat_chain = ConversationalRetrievalChain.from_llm(
            llm=chat,
            memory=memory,
            retriever=retriever,
            return_source_documents=True,
            verbose=True
        )
        st.session.state.chat_chain = chat_chain
    print("Cannot create vector store and chat chain without documents.")
    return None
        
        
    
    