from langchain import LLMChain
from langchain.chat_models import ChatOpenAI
from langchain.prompts.chat import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)

from src.persona import Persona


class NPCLLM:
    @classmethod
    def from_config(cls, config_path: str):
        return NPCLLM(Persona(config_path=config_path))

    @classmethod
    def make_chain(cls, persona: Persona) -> LLMChain:
        chat = ChatOpenAI()  # type: ignore[call-arg]
        system_template = (
            "You are a Discord playwright's assistant, you write plays that take place in a discord server"
            + " message by message. Below is a description of the character you will write a message for. "
            + f"<desc>{persona.make_description()}</desc>. "
            + "A memory comes to you from the past, use it to inform your understanding of the chat."
            + " <memory>{a_memory}</memory>. "
        )
        human_template = (
            f"Please write the next message in this Discord play, from {persona.username}. "
            + "<playstart>{chat_history}</playstart><newmsg>"
        )

        system_message_prompt = SystemMessagePromptTemplate.from_template(
            system_template
        )
        human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)
        chat_prompt = ChatPromptTemplate.from_messages(
            [system_message_prompt, human_message_prompt]
        )
        return LLMChain(llm=chat, prompt=chat_prompt)

    def __init__(self, persona: Persona) -> None:
        self.persona = persona
        self.chain = NPCLLM.make_chain(self.persona)

    def clean(self, llm_response_str: str) -> str:
        cleaned_str = llm_response_str.split(f"{self.persona.username}:")[1].strip()
        cleaned_str = cleaned_str.replace("@everyone", "everyone")
        return cleaned_str

    def prompt(self, chat_history: str, a_memory: str):
        # We need a chain for completing a new chat
        # Give it a template with instructions, pass in persona desc., pass in message history, pass in memory
        response = self.chain.run(a_memory=a_memory, chat_history=chat_history)
        return self.clean(response)
