import streamlit as st
from pathlib import Path


FILES_FOLDER = Path(__file__).parent / "files"

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
    

def main():
   with st.sidebar:
         sidebar()
    
if __name__ == "__main__":
    main()