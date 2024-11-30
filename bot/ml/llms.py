from pathlib import Path
import os

from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from langchain_groq import ChatGroq

from evraz_model_wrapper import ChatMistralNemo
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")


class LLMFactory:
    @staticmethod
    def get_llm(llm_name: str) -> BaseChatModel:
        if llm_name == "mistral-nemo-instruct-2407":
            return ChatMistralNemo(
                base_url=os.environ["EVRAZ_BASE_URL"],
                api_key=os.environ["EVRAZ_GPT_KEY"],
                model_name="mistral-nemo-instruct-2407",
            )
        elif llm_name == "Qwen/Qwen2.5-Coder-32B-Instruct":
            return ChatOpenAI(
                model="Qwen/Qwen2.5-Coder-32B-Instruct",
                api_key=os.environ["QWEN_CODER_KEY"],
                base_url="https://api.deepinfra.com/v1/openai",
                # temperature=0,
            )
        elif llm_name == "llama-3.1-70b-versatile":
            return ChatGroq(
                model="llama-3.1-70b-versatile",
                temperature=0,
                max_tokens=None,
                timeout=None,
                max_retries=2,
                api_key=os.environ["GROQ_API_KEY"],
            )
        elif llm_name == "qwen2.5-coder:7b":
            return ChatOllama(
                model="qwen2.5-coder:7b",
                temperature=0,
            )
        elif llm_name == "qwen2.5-coder:32b":
            return ChatOllama(
                model="qwen2.5-coder:32b",
                temperature=0,
            )
        elif llm_name == "chatgpt":
            return ChatOpenAI(
                model="gpt-4o",
                api_key=os.environ["OPENAI_API_KEY"],
                temperature=0,
                max_tokens=None,
                timeout=None,
                max_retries=2,
            )
        elif llm_name == "Phind/Phind-CodeLlama-34B-v2":
            return ChatOpenAI(
                model="Phind/Phind-CodeLlama-34B-v2",
                api_key=os.environ["QWEN_CODER_KEY"],
                base_url="https://api.deepinfra.com/v1/openai",
            )
        else:
            raise ValueError(f"Unknown LLM name: {llm_name}")
