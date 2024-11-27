
# %%
from dotenv import load_dotenv

load_dotenv()

from typing import TypedDict, Annotated, Literal
from langchain_ollama import ChatOllama
from langchain_groq import ChatGroq
from langchain_core.documents import Document
from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage, AIMessage
from langchain_core.tools import tool
from langgraph.graph import add_messages, StateGraph, START, END
from langgraph.constants import Send
from langchain_community.tools import DuckDuckGoSearchResults

# from vectorstores import MyVectorstoreLoader # not work

llm = ChatOllama(model="llama3.2")
# llama-3.1-70b-versatile
# llama-3.2-90b-vision-preview
llm = ChatGroq(model="llama-3.1-70b-versatile")

def add_documents(documents: list[Document], new_docs: list[Document]):
  return documents + new_docs

class ResearcherInputState(TypedDict):
  messages: Annotated[list[AnyMessage], add_messages]
  
class ResearcherOutputState(TypedDict):
  messages: Annotated[list[AnyMessage], add_messages]

   
# tools
from service.consultation_company.vectorstores.vectorstore_vertexai import vector_loader


@tool
def vectordb_search(search_query: str):
  """Search the query from Fairfax County webpages/PDFs vectorstore db

  Args:
      search_query: query to search in vectorstore db
  """
  vectorstore = vector_loader.vectorstore
  
  retriever = vectorstore.as_retriever()
  retrieved_docs = retriever.invoke(search_query)
  # return evaluate_documents(search_query, retrieved_docs)
  return retrieved_docs

@ tool
def internet_search(search_query: str):
  """Search the query from internet

  Args:
      user_question: original  user question to be addressed
      search_query: Exact search terms
  """
  search = DuckDuckGoSearchResults(output_format="list")
  retrieved_snippets = search.invoke(search_query)
  
  return retrieved_snippets


@tool
def user_ask(question: str):
  """Ask the user for any clarification or more information

  Args:
      question: question to ask the user
  """
  # # Probably will be replaced by api call
  # user_input = input(f"{question}\n\nanswer: ")
  # return user_input
  pass

search_tools = [vectordb_search, internet_search, user_ask]

llm_with_tools = llm.bind_tools(search_tools, parallel_tool_calls=False)

# main agent
def research_agent(state):
  sys_msg = """
  You are a ReAct Research Agent for Fairfax Construction Information

CORE CAPABILITIES:
- Research and answer Fairfax construction-related queries
- Utilize two primary research tools:
  1. Vectorstore (Static Fairfax County webpages/PDFs)
  2. Internet search
- Employ clarification agent for additional user context

STRICT RULES:
- NEVER make up or assume any information
- ALL information MUST be sourced from tools
- Citations MUST follow this format:
  * For Web Pages:
    [Source: URL | Section: specific section | Retrieved: date]
  * For PDF Documents:
    [Source: PDF filename | Page: page number | Section: section title]
  * For Vector Database:
    [Source: Document ID | Type: PDF/Web | Location: specific location]
- If information cannot be found through tools, acknowledge the limitation

RESEARCH METHODOLOGY (ReAct Framework):
1. Thought: Analyze query comprehensively
   - Identify specific information needs
   - Determine research strategy
   - Plan tool utilization

2. Action: Execute targeted research
   - Search Vectorstore first
   - Perform internet search if needed
   - Request user clarifications via clarification agent

3. Observation: Synthesize findings
   - Validate information accuracy
   - Cross-reference sources
   - Identify potential knowledge gaps

RESEARCH PROTOCOL:
- Prioritize official Fairfax County sources
- Maintain strict relevance to query
- Provide clear, structured responses

CRITICAL CONSTRAINTS:
- Focus on Fairfax construction information
- Ensure response accuracy
- Transparently document research process
  """

  response = llm_with_tools.invoke([SystemMessage(content=sys_msg)] + state['messages'])
  return {
    'messages': [response]
  }

class UserClarificationState(TypedDict):
  question: str
  tool_call_id: str
  
def ask_user(state: UserClarificationState):
  question = state['question']
  tool_call_id = state['tool_call_id']
  
  return {
    'messages': [AIMessage(content=question)],
    'tool_call_id': tool_call_id
  }

def tools_condition_route(state) -> Literal['tools', "ask_user", END]:
  ai_message = state['messages'][-1]
  if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
    tool_calls = ai_message.tool_calls
    for tool_call in tool_calls:
      tool_name = tool_call['name']
      tool_args = tool_call['args']
      tool_call_id = tool_call['id']
      if tool_name == 'user_ask':
        return Send("ask_user", {'question': tool_args['question'], 'tool_call_id': tool_call_id})
        # next_routes.append(Send("ask_user", {'orig_question': state['messages'][0], 'question': tool_args['question'], 'tool_call_id': tool_call_id}))
      else: 
        return "tools"
  else:
    return END

from langgraph.prebuilt import ToolNode, tools_condition

researcher_builder = StateGraph(input=ResearcherInputState, output=ResearcherOutputState)

researcher_builder.add_node(research_agent)
researcher_builder.add_node(ToolNode(search_tools))
researcher_builder.add_node(ask_user)

researcher_builder.add_edge(START, 'research_agent')
researcher_builder.add_conditional_edges('research_agent', tools_condition_route)
researcher_builder.add_edge('tools', 'research_agent')
researcher_builder.add_edge('ask_user', END)


resesarcher_agent = researcher_builder.compile()

# %%
# if __name__ == "__main__":
# from IPython.display import display, Image
# display(Image(resesarcher_agent.get_graph().draw_mermaid_png()))

# # %%
# client_query = "싱글하우스 집에 애디션을 만들고 싶어. 필요한 인스펙션이 뭔지 알려줘"

# state = {
#   'messages': [HumanMessage(content=client_query)]
# }

# response = resesarcher_agent.invoke(state)
  
# # %%
# for m in response['messages']:
#   m.pretty_print()
  
# # # %%

# %%
