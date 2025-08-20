import os
from langchain_litellm import ChatLiteLLM
import litellm
os.environ["OPENAI_API_KEY"] = os.environ["LITELLM_CONSULT_OPENAI_API_KEY"]
os.environ["OPENAI_API_BASE"] = os.environ["LLM_GATEWAY_URL"]

litellm._turn_on_debug()

import requests
from langchain.schema import HumanMessage   


try:
    response = requests.get(os.environ["LLM_GATEWAY_URL"])
    print("Gateway status:", response.status_code)
except Exception as e:
    print("Gateway connection error:", e)

llm = ChatLiteLLM(
    model="gpt-4o",
    temperature=0,
)

test_prompt = "Write a short haiku about autumn."

messages = [HumanMessage(content="Write a short haiku about autumn.")]
result = llm(messages)
print("LLM response:", result)  



