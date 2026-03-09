import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

api_key = os.environ['API_KEY']

# Initialize LLM
llm = ChatOpenAI(
    model="openai.gpt-5.1",  # Specify the OpenAI model you want to use
    base_url="https://openai.generative.engine.capgemini.com/v1",
    api_key=api_key,
    default_headers={"x-api-key": api_key}  # Some implementations require this header
)