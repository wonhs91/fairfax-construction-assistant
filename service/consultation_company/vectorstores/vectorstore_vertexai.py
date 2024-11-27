# %%
from dotenv import load_dotenv
load_dotenv()

from langchain_community.document_loaders import PyPDFLoader
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader
import os
import json


class MyVectorstoreLoader():
  def __init__(self, collection_name="fairfax_construction_code", persist_dir="D:\\projects\\AIprojects\\fairfax-construction-assistant\\service\\consultation_company\\vectorstores\\db"):
    self.vectorstore = Chroma(
      collection_name=collection_name,
      persist_directory=persist_dir,
      embedding_function=GoogleGenerativeAIEmbeddings(model="models/text-embedding-004"),
    )
    self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=100)
  
  
  def load_json_files(self, dir):
    documents = []
    for filename in os.listdir(dir):
      if filename.endswith(".json"):
        try: 
          with open(os.path.join(dir, filename), 'r', encoding='utf-8') as f:
            data = json.load(f)
            if 'page_content' in data and 'metadata' in data:
              document = Document(
                page_content=data['page_content'],
                metadata=data['metadata']
              )
              documents.append(document)
            else:
              print(f"Invalid structure in file: {filename}")
        except Exception as e:
          print(f"There was an error processing {filename}: {e}")
    return self.text_splitter.split_documents(documents)
  
  def load_pdf_files(self, dir):
    documents = []
    for filename in os.listdir(dir):
      if filename.endswith('.pdf'):
        filepath = os.path.join(dir, filename)
        try:
          loader = PyPDFLoader(filepath, extract_images=False)
          pdf_documents = loader.load()
          documents.extend(pdf_documents)
        except Exception as e:
          print(f"There was an error processing {filename}: {e}")
    return self.text_splitter.split_documents(documents)
  
  def store_json_dir(self, dir):
    documents = self.load_json_files(dir)
    try:
      self.vectorstore.add_documents(documents)
      return True
    except Exception as e:
      print(f"Failed to add json documents: {e}")
      return False
    
  def store_pdf_dir(self, dir):
    documents = self.load_pdf_files(dir)
    try:
      self.vectorstore.add_documents(documents)
      return True
    except Exception as e:
      print(f"Failed to add pdf documents: {e}")
      return False
  
  def store_pdf_file(self, filepath):
    try:
      loader = PyPDFLoader(filepath, extract_images=False)
      pdf_documents = loader.load()
      split_documents = self.text_splitter.split_documents(pdf_documents)
      self.vectorstore.add_documents(split_documents)
      return True
    except Exception as e:
      print(f"Failed to load document {os.path.basename(filepath)}: {e}")
    
    return False
  
  def store_json_file(self, filepath):
    try:
      
      with open(filepath, 'r') as f:
        data = json.load(f)
        if 'page_content' in data and 'metadata' in data:
          document = Document(
            page_content=data['page_content'],
            metadat=data['metadata']
          )
          split_documents = self.text_splitter.split_documents([document])
          self.vectorstore.add_documents(split_documents)
          return True
        else:
          print(f"Invalid structure in file: {os.path.basename(filepath)}")
    except Exception as e:
      print(f"Failed to load document {os.path.basename(filepath)}: {e}")
    
    return False
  

# # %%
# import time  
vector_loader = MyVectorstoreLoader(collection_name="fairfax_construction_code", persist_dir="D:\\projects\\AIprojects\\fairfax-construction-assistant\\service\\consultation_company\\vectorstores\\db")

# # print("store pdf file")
# # vector_loader.store_pdf_file("D:\\projects\\AIprojects\\fairfax-construction-assistant\\service\\consultation_company\\vectorstores\\2021-virginia-construction-code.pdf")


# # print("store json file")
# # vector_loader.store_json_file("D:\\projects\\AIprojects\\fairfax-construction-assistant\\service\\consultation_company\\vectorstores\\web_scraping_data\\0ac9432e6cdbae6e022d4194635bcfb1.json")


# print("store json dir")
# vector_loader.store_json_dir("D:\\projects\\AIprojects\\fairfax-construction-assistant\\service\\consultation_company\\vectorstores\\web_scraping_data")

# print("store pdf dir")
# vector_loader.store_pdf_dir("D:\\projects\\AIprojects\\fairfax-construction-assistant\\service\\consultation_company\\vectorstores\\web_scraping_data\\pdf")

# # %%
# vector_loader = MyVectorstoreLoader(persist_dir="D:\\projects\\AIprojects\\fairfax-construction-assistant\\service\\consultation_company\\vectorstores\\db")

# retriever = vector_loader.vectorstore.as_retriever()

# invoke_docs = retriever.invoke("What kind of inspections are needed?")
# get_docs = retriever.get_relevant_documents("What are the steps for a construction project?")

# print(invoke_docs)
# vector_loader.vectorstore.similarity_search("inspection")
# # print("\n\n")
# # print("===" * 25)
# # print("\n\n")
# # print(get_docs[1])

# # %%
