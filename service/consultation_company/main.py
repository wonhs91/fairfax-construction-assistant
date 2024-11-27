# %%
from dotenv import load_dotenv
load_dotenv()

from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama
from typing import Optional
import os
# D:\projects\AIprojects\fairfax-construction-assistant\service\consultation_company\agents\agents.py
from service.consultation_company.agents import translator

class ChatOpenRouter(ChatOpenAI):
  model_name: str
  api_key: str
  openai_api_base: str
  
  def __init__(self, model_name:str,
               api_key: Optional[str] = None,
               openai_api_base: str = "https://openrouter.ai/api/v1",
              **kwargs):
    api_key = api_key or os.getenv("OPENROUTER_API_KEY")
    super().__init__(openai_api_base=openai_api_base, api_key=api_key, model_name=model_name, **kwargs)
    
    
brain_llm = ChatOpenRouter(model_name="meta-llama/llama-3-405b-instruct:free")
tool_llm = ChatGroq(model="llama-3.1-70b-versatile", temperature=0)
# brain_llm = ChatOllama(model="llama3.2")
# tool_llm = ChatOllama(model="llama3.2")


# %%
# store in vectorsore

from langchain_google_genai import GoogleGenerativeAIEmbeddings

from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma


vectorstore = Chroma(
  collection_name="fairfax_construction_code",
  persist_directory='D:\\projects\\AIprojects\\fairfax-construction-assistant\\service\\consultation_company\\vectorstores\\db',
  embedding_function=GoogleGenerativeAIEmbeddings(model="models/text-embedding-004"),
)

retriever = vectorstore.as_retriever(
  search_type="mmr",
  search_kwargs={
    "k": 5,
    "fetch_k": 20,
    "lambda_mult": 0.7,
  }  
)

# %%
query = "I need help understanding the building permit requirements for a residential extension in Fairfax, Virginia."
# query = "Fairfax, Virginia - Residential - Building Permit Requirements - Clarification on Specific Requirements Needed"
response = retriever.invoke(query)
# %%
from pprint import pprint

for res in response:
  print("===" * 25)
  print(res.metadata)
  print("---" * 25)
  print(res.page_content)


# %%
# State

from pydantic import BaseModel, Field
from typing import Literal, Annotated
from typing_extensions import TypedDict
from langchain_core.documents import Document
from langgraph.graph import add_messages
from langchain_core.messages import AnyMessage

def add_question(questions, new_question):
  questions.append(new_question)
  return questions
  

class OverallState(TypedDict):
  messages: Annotated[list[AnyMessage], add_messages]
  can_assist: bool = False
  questions: Annotated[list[str], add_question]
  documents: list[Document]
  answer: Optional[str] = None

# %%
# Nodes
from langchain_core.messages import HumanMessage, SystemMessage

def initial_consult(state):
  question = state['questions'][-1]
  consultation_result = initial_consultation_agent(brain_llm, question)
  
  return {
    'can_assist': consultation_result.can_assist
  }

def search_docs(state):
  curr_question = state['questions'][-1]
  retrieved_documents = retriever.invoke(curr_question)
  return {
    'documents': retrieved_documents
  }
  

def filter_documents(state):
  class DocumentRelevancy(BaseModel):
    is_relevant: str = Field(
      description="Documents are relevant to the question, 'yes' or 'no'"
    )
  
  structured_relevancy = tool_llm.with_structured_output(DocumentRelevancy)
  
  sys_msg = """
    You are a grader assessing relevance of a retrieved document to a user questions.
    If the document contains keyword(s) or semantic meaning related to the user question, grade it as relevant.
    It does not need to be a stringent test. The goal is to filter out erroneous retrievals.
    Give a binary score 'yes' or 'no' score to indicate wether the document is relevant to the question.
  """
  
  filtered_docs = []
  for doc in state['documents']:
    query = f"user question: {state['questions'][-1]}\n\nRetrieved document:\n\n{doc.page_content}"

    relevancy = structured_relevancy.invoke([
      SystemMessage(content=sys_msg),
      HumanMessage(content=query)
    ])
    if relevancy.is_relevant == "yes":
      filtered_docs.append(doc)
    else:
      continue
  
  return {
    'documents': filtered_docs
  }

  
def generate_answer(state):
  curr_question = state['questions'][-1]
  docs = [doc.page_content for doc in state['documents']]
  
  sys_msg = f"""
  You are an expert for answering questions based on the document provided.
  Use the following pieces of retrieved context to answer the question.
  If you can't answer the question from the provided context, just say you don't have enough information. 

  Context: \n{docs}
  """
  response = brain_llm.invoke([
    SystemMessage(content=sys_msg),
    HumanMessage(content=curr_question)
  ])
  
  return {
    'answer': response
  }
  
def transform_query(state):
  curr_question = state['questions'][-1]
  
  sys_msg = """
  You are a Query Transformation Agent for Construction Manual Retrieval.

  PRIMARY OBJECTIVES:
  - Transform user queries for precise document retrieval
  - Extract critical contextual information
  - Generate technically accurate search queries

  CORE WORKFLOW:
  1. Initial Query Analysis
  - Deconstruct original query
  - Identify technical information gaps
  - Assess query's specificity and clarity

  2. Clarification Protocol
  When query lacks details, immediately ask targeted questions:
  - What specific construction type? (Residential/Industrial)
  - Which exact system or component?
  - What is your primary problem or goal?
  - What is your current construction stage?
  - What is your technical expertise level?

  3. Query Transformation Rules
  - Preserve original user intent
  - Convert colloquial language to technical terminology
  - Generate multiple precise query variants
  - Optimize for vector database retrieval

  4. Output Requirements
  Produce JSON with:
  {
      "original_query": "",
      "clarification_questions": [],
      "transformed_queries": [],
      "retrieval_keywords": [],
      "reasoning": ""
  }

  CRITICAL CONSTRAINTS:
  - Never assume unstated details
  - Prioritize user-provided information
  - Maintain technical accuracy
  - Focus on retrievability
  """
  
  response = brain_llm.invoke([
    SystemMessage(content=sys_msg),
    HumanMessage(content=f"Rewrite the current question into more comprehensive format.\nquestion: {curr_question}\n")
  ])
  return {
    'questions': response.content
  }

# Edges  
def evaluate_documents(state) -> Literal["no_docs", "yes_docs"]:
  documents = state['documents']

  if not documents:
    return "no_docs"
  else:
    return "yes_docs"  
  
  
def evaluate_answer(state) -> Literal["valid_answer", "invalid_answer", "infactual_answer"]:
  answer = state['answer'].content
  doc_contents = [doc.page_content for doc in state['documents']]
  class FactGrade(BaseModel):
    fact_grounded: str = Field(
      description="Answer is fact-grounded, 'yes' or 'no'"
    )
  
  structured_fact_llm = tool_llm.with_structured_output(FactGrade)
  
  fact_sys_msg = """
  You are a grader assessing if the answer is fact grounded based on provided documents.
  If the answer is grounded by the provided documents, grade it as fact-grounded.
  If there is any part of the answer that cannot be backed by the provided documents, the answer is not fact-grounded.
  Give a binary score 'yes' or 'no' score to indicate wether the answer is fact-grounded.
  
  If the answer says it doesn't know or have enough information, it is fact-grounded.
  """
  
  fact_based = structured_fact_llm.invoke([
    SystemMessage(content=fact_sys_msg),
    HumanMessage(content=f"answer: {answer}\n\ndocuments:\n\n{doc_contents}")
  ])
  
  if fact_based.fact_grounded == "yes":
    # check if answer addresses the question
    class GradeAnswer(BaseModel):
      does_address: str = Field(
        description="Answer addresses the question, 'yes' or 'no'"
      )
    
    structured_answer_llm = tool_llm.with_structured_output(GradeAnswer)
    
    answer_sys_msg = """
    You are a grader assessing whether an answer addresses / resolves a question.
    Give a binary score 'yes' or 'no'. 'yes' means that the answer resolves the question.
    """
    
    original_question = state['questions'][0]
    answer_grade = structured_answer_llm.invoke([
      SystemMessage(content=answer_sys_msg),
      HumanMessage(content=f"answer: {answer}\n\nquestion: {original_question}")
    ])
    if answer_grade.does_address == "yes":
      return "valid_answer"
    else:
      return "invalid_answer"
    
  else:
    return "infactual_answer"
  
  
  
# %%
from langgraph.graph import StateGraph, START, END

builder = StateGraph(OverallState)
builder.add_node(retrieve_docs)
builder.add_node(filter_documents)
builder.add_node(generate_answer)
builder.add_node(transform_query)

builder.add_edge(START, "retrieve_docs")
builder.add_edge("retrieve_docs", "filter_documents")
builder.add_conditional_edges(
  "filter_documents",
  evaluate_documents,
  {"yes_docs": "generate_answer", "no_docs": "transform_query"})
builder.add_edge("transform_query", "retrieve_docs")
builder.add_conditional_edges(
  "generate_answer",
  evaluate_answer,
  {'valid_answer': END, 'invalid_answer': 'transform_query', 'infactual_answer': 'generate_answer'}
)

agent = builder.compile()

# %%
from IPython.display import display, Image
display(Image(agent.get_graph().draw_mermaid_png()))
# %%
question = """How many inspections are there?"""

response = retriever.invoke(question)
 #%%
# print(response)

# %%
if __name__ == "__main__":

  question = """
  What is the minimum number of inspections required for addition work?
  """
  
  # I am building an residential addition. I just passes the foundation inspection. Now what inspection whould I prepare for?
  test_state = {
    "questions": question
  }

  response = agent.invoke(test_state, {"recursion_limit": 10})
  response['answer'].pretty_print()


# %%
