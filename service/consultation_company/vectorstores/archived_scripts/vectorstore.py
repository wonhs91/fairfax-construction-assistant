# %%
# RAG
import os
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

# load
construction_file = "2021-virginia-construction-code.pdf"
construction_code_path = os.path.join(os.getcwd(), construction_file)

pdf_loader = PyPDFLoader(file_path=construction_code_path, extract_images=False)
pages = pdf_loader.load()


# %%
# split
splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=200)
pdf_docs = splitter.split_documents(pages)
# TODO: clean docs? remove \n s and stuff



# %%
# store in vectorsore

from langchain.embeddings import OpenAIEmbeddings
from langchain_chroma import Chroma


vectorstore = Chroma.from_documents(
  documents=pdf_docs,
  embedding=OpenAIEmbeddings(),
  collection_name="fairfax_construction_code",
  collection_metadata={'file_name': construction_file},
  persist_directory='./openai-db/'
)

# %%
retriever = vectorstore.as_retriever()

retriever.invoke("what is inspection")