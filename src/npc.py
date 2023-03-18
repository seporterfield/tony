import discord
import openai
from enum import Enum
import random
from collections import deque
from logging import Logger
import json

RANDOM_RESPONSE_ODDS = 40

class NPCResponse(Enum):
    SILENCE = 1
    DIRECT = 2
    RANDOM = 3


class NPC:
    @classmethod
    def make_description(cls, name, username, age, gender, setting, job, personality, context):
        return f" Name: {name}, Username: {username}, Age: {age}, Gender: {gender}, " + \
            f"Setting: {setting}, Job: {job}, Personality traits: {'-'.join(personality)}, " + \
            f"Additional context: {'-'.join(context)}. "
    
    def __init__(self,
                 client: discord.Client,
                 history_length: int,
                 name: str = "unknown",
                 username: str = "unknown",
                 age: int = -1,
                 gender: str = "unknown",
                 setting: str = "unknown",
                 job: str = "unknown",
                 personality: list[str] = ["unknown"],
                 context: list[str] = ["unknown"],
                 model: str = "gpt-3.5-turbo",
                 temperature: float = 0.5,
                 frequency_penalty: float = 0,
                 logger: Logger = None) -> None:
        self.name = name
        self.username = username
        self.age = age
        self.gender = gender
        self.setting = setting
        self.job = job
        self.personality = personality
        self.context = context
        
        self.client = client
        self.description = NPC.make_description(name=name, username=username, age=age,
                                                gender=gender, setting=setting, job=job,
                                                personality=personality, context=context)
        self.system_message = self.make_system_message()
        self.model = model
        self.history_length = history_length
        self.temperature = temperature
        self.frequency_penalty = frequency_penalty
        self.logger = logger
        
        self.messages = deque()
        self.consecutive_message_limit = 3
    
    def make_system_message(self) -> str:
        return "You are an NPC in a videogame that takes place in a Discord server. " + \
            self.description + \
            "You always respond in the format of a verbal conversation, " + \
            "never narrating or putting your own words in quotes. You always start your message " + \
            f"with {self.username}:, but you most definitely never pretend to be other users." 
    
    
    async def update_messages(self, message: discord.Message) -> None:
        if len(self.messages) == 0:
            self.messages = deque([msg async for msg in message.channel.history(limit=self.history_length)][::-1])
            return
        self.messages.popleft()
        self.messages.append(message)
        
    def consecutive_msg_limit_reached(self) -> bool:
        num_consecutive = 0
        for msg in list(self.messages)[::-1]:
            if msg.author.id != self.client.user.id:
                break
            num_consecutive += 1
        return num_consecutive >= self.consecutive_message_limit
        
    def is_chat_relevant(self) -> bool:
        for msg in self.messages:
            if msg.author.id == self.client.user.id:
                return True
            elif self.client.user.mentioned_in(msg):
                return True
            elif msg.mention_everyone:
                return True
        return False
    
    def make_completion_messages(self, system_prompt: str, role: str = 'npc') -> list[dict]:
        completion_messages = [{"role": "system", "content": system_prompt}]
        for message in self.messages:
            role, signature = "", ""
            if message.author.id == self.client.user.id and role == 'npc':
                role = "assistant"
                signature = ""
            else:
                role = "user"
                signature = message.author.name + ": "
            completion_messages.append({"role": role, "content": signature + message.content})
        return completion_messages
    
    def prompt_openai(self, completion_messages: list[dict]) -> str:
        assert(len(json.dumps(completion_messages)) <= 15000)
        assert(len(completion_messages) != 0)
        print(completion_messages)
        response = openai.ChatCompletion.create(model=self.model, messages=completion_messages,
                                            max_tokens=200, temperature=self.temperature,
                                            frequency_penalty=self.frequency_penalty)
        response = response.choices[0].message.content
        print(response)
        return response
    
    def is_response_appropriate(self) -> bool:
        # We're gonna run this through another OpenAI Prompt.
        system_prompt = f"Classify whether anything in this discord channel is related to anything in the following description <{self.description}>. Please answer concisely with either " + \
                        "'AFFIRMATIVE' or 'NEGATIVE'. Do respond with anything else."
        completion_messages = self.make_completion_messages(system_prompt, role='classifier')
        
        response = self.prompt_openai(completion_messages=completion_messages)
        return "AFFIRMATIVE" in response
    
    def get_response_type(self) -> NPCResponse:
        if not self.is_chat_relevant():
            if random.randint(1, RANDOM_RESPONSE_ODDS) == 1:
                return NPCResponse.RANDOM
            else:
                return NPCResponse.SILENCE
        if self.consecutive_msg_limit_reached():
            return NPCResponse.SILENCE
        if self.is_response_appropriate():
            return NPCResponse.DIRECT
        return NPCResponse.SILENCE
    
    def prompt(self) -> str:
        completion_messages = self.make_completion_messages(self.system_message, role='npc')
        response = self.prompt_openai(completion_messages=completion_messages)
        return response
    
    def clean_response(self, response: str) -> str:
        pieces = response.split(self.username + ":")
        print(pieces)
        if len(pieces) < 2:
            return "bababooey"
        return response.split(self.username + ":")[1][:2000] # TODO Test API call pipeline, add to this if necessary, otherwise remove.
    
def main():
    pass

if __name__ == '__main__':
    main()