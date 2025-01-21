# %%
from dotenv import load_dotenv
load_dotenv()

import os

# from service.consultation_company.agents.researcher import researcher_builder
from scripts.vectorstores.vectorstore_loader import MyVectorstoreLoader

PINECONE_INDEX_NAME=os.environ.get('PINECONE_INDEX_NAME', "fairfax-county-construction-code")

vectorstore_loader = MyVectorstoreLoader(mode="pinecone", collection_name=PINECONE_INDEX_NAME)

json_path = ".\\scripts\\vectorstores\\web_scraping_data\\json"
pdf_path = ".\\fairfax-construction-assistant\\scripts\\vectorstores\\web_scraping_data\\pdf"
vectorstore_loader.store_json_dir(dir=json_path)
vectorstore_loader.store_pdf_dir(dir=pdf_path)
