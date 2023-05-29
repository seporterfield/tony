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
    def make_revision_chain(cls, persona: Persona) -> LLMChain:
        chat = ChatOpenAI()  # type: ignore[call-arg]
        system_template = (
            "You are a Discord playwright's assistant, you revise plays that take place in a discord server."
            + " Below is a description of the character you will revise a message for. "
            + f"<desc>{persona.make_description()}</desc>. "
        )
        human_template = (
            f"Please revise the new message in this Discord play, which is from {persona.username}. "
            + "<playstart>{chat_history}</playstart> <new_msg>{new_message}</new_msg>."
            + " Clean it so it only contains the message's contents,"
            + " and remove text that does not fit the current context."
            + " Reply with the revised message content between <rev> </rev> tags."
        )

        system_message_prompt = SystemMessagePromptTemplate.from_template(
            system_template
        )
        human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)
        chat_prompt = ChatPromptTemplate.from_messages(
            [system_message_prompt, human_message_prompt]
        )
        return LLMChain(llm=chat, prompt=chat_prompt)

    @classmethod
    def make_new_message_chain(cls, persona: Persona) -> LLMChain:
        chat = ChatOpenAI()  # type: ignore[call-arg]
        system_template = (
            "You are a Discord playwright's assistant, you write plays that take place in a discord server"
            + " message by message. Below is a description of the character you will write a message for. "
            + f"<desc>{persona.make_description()}</desc>. "
            + "A memory comes to you from the past, use it to inform your understanding of the chat."
            + " <memory>{a_memory}</memory>. "
        )
        human_template = (
            "<playstart>{chat_history}</playstart>. "
            + f"Please write the next message in this Discord play, from {persona.username}. <newmsg>"
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
        self.new_message_chain = NPCLLM.make_new_message_chain(self.persona)
        self.revision_chain = NPCLLM.make_revision_chain(self.persona)

    def clean(self, llm_response_str: str) -> str:
        cleaned_str = llm_response_str.split("<rev>")[-1].rsplit("</rev")[0]
        cleaned_str = cleaned_str.split(f"{self.persona.username}:", 1)[-1]
        cleaned_str = cleaned_str.replace("@everyone", "everyone")
        return cleaned_str

    def revise(self, chat_history: str, llm_response_str: str) -> str:
        return self.revision_chain.run(
            chat_history=chat_history, new_message=llm_response_str
        )

    def prompt(self, chat_history: str, a_memory: str):
        response = self.new_message_chain.run(
            a_memory=a_memory, chat_history=chat_history
        )
        response = self.revise(chat_history, response)
        return self.clean(response)
