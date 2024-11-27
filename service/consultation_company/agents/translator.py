# %%
from google.cloud import translate_v2 as translate
from service.consultation_company.agents.researcher import researcher_builder
from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, ToolMessage
from langgraph.graph import add_messages
from typing import TypedDict, Annotated

translate_client = translate.Client()

class TranslatorState(TypedDict):
  messages: Annotated[list[AnyMessage], add_messages]
  tool_call_id: str = None
  
  original_query: str
  user_language: str
  translated_researcher_response: AIMessage
  
def translate_to_eng(state):
  result = translate_client.translate(state['original_query'], target_language="en-US")

  translated_query = result['translatedText']
  detected_language_code = result['detectedSourceLanguage']
  
  if state.get('tool_call_id'):
    next_msg = ToolMessage(content=translated_query, tool_calll_id=state['tool_call_id'])
  else:
    next_msg = HumanMessage(content=translated_query)
  
  return {
    'user_language': detected_language_code,
    'messages': [next_msg],
    'tool_call_id': None
  }
  
def translate_to_lang(state):
  answer = state['messages'][-1].content
  if not state['user_language'] == 'en-US':
    result = translate_client.translate(answer, state['user_language'], format_="text")
    answer = result['translatedText']

  return {
    'translated_researcher_response': answer
  }

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

memory = MemorySaver()

translator_builder = StateGraph(TranslatorState)
translator_builder.add_node(translate_to_eng)
translator_builder.add_node("researcher", researcher_builder.compile())
translator_builder.add_node(translate_to_lang)

translator_builder.add_edge(START, 'translate_to_eng')
translator_builder.add_edge('translate_to_eng', 'researcher')
translator_builder.add_edge('researcher', 'translate_to_lang')
translator_builder.add_edge('translate_to_lang', END)

translator = translator_builder.compile(checkpointer=memory)
# # %%
# from IPython.display import display, Image

# display(Image(translator.get_graph(xray=1).draw_mermaid_png()))
# %%
# config = {'configurable': {'thread_id': 1}}

# state = {
#   "original_query": '베이스먼트에 창문을 달고 싶어. 괜찮을까?'
#   # "original_query": '공기/덕트 누출 테스트 여기에 대해서 좀더 자세히 알아봐줘'
# }

# translator.invoke(state, config=config)

# %%
