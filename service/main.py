from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uuid

from service.consultation_company.agents import translator

app = FastAPI()

app.add_middleware(
  CORSMiddleware,
  allow_origins=["*"],
  allow_headers=["*"],
  allow_methods=["*"]
)

@app.get("/")
async def get():
  return {"message": "Welcome to Fairfax Construction World!"}

class ConstructionQuery(BaseModel):
  question: str
  
@app.post("/api/fairfax-construction-assistant/")
async def start_chat(req_body: ConstructionQuery):
  thread_id = str(uuid.uuid4())
  config = {"configurable": {"thread_id": thread_id}}
  state = {
    "original_query": req_body.question
  }
  
  response = translator.invoke(state, config=config)
  
  return {"answer": response['translated_researcher_response'], "thread_id": thread_id}


@app.post("/api/fairfax-construction-assistant/{thread_id}")
async def continue_chat(req_body: ConstructionQuery, thread_id: str):
  config = {"configurable": {"thread_id": thread_id}}
  state = {
    "original_query": req_body.question
  }
  
  response = translator.invoke(state, config=config)
  
  return {"answer": response['translated_researcher_response'], "thread_id": thread_id}
