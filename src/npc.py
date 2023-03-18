import discord
import openai
from enum import Enum
import random
from collections import deque
from logging import Logger
import json
import asyncio
import yaml
from yaml.loader import SafeLoader

RANDOM_RESPONSE_ODDS = 40

class NPCPromptMode(Enum):
    NPC = 1
    RELEVANCE_CHECKER = 2

class NPCResponse(Enum):
    SILENCE = 1
    DIRECT = 2
    RANDOM = 3


class NPC:
    @classmethod
    def make_description(cls, name, username, age, gender, setting, job, personality, context):
        return f" Name: {name}, Username: {username}, Age: {age}, Gender: {gender}, " + \
            f"Setting: {setting}, Job: {job}, Personality traits: {'---'.join(personality)}, " + \
            f"Additional context: {'---'.join(context)}. "
            
    @classmethod
    def from_yaml(cls, filepath: str, client: discord.Client, logger: Logger = None, channel: discord.TextChannel = None):
        data = None
        with open(filepath) as f:
            data = yaml.load(f, Loader=SafeLoader)
        if data == None:
            raise Exception("Bad NPC config yaml file: %s", filepath)
        return NPC(client=client,
                   history_length=data['history_length'],
                   name=data['name'],
                   username=data['username'],
                   age=data['age'],
                   gender=data['gender'],
                   setting=data['setting'],
                   job=data['job'],
                   personality=data['personality'],
                   context=data['context'],
                   model=data['model'],
                   temperature=data['temperature'],
                   frequency_penalty=data['frequency_penalty'],
                   channel=channel,
                   logger=logger)
    
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
                 channel: discord.TextChannel = None,
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
        self.channel = channel
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
        self.consecutive_message_limit = 4
    
    def make_system_message(self) -> str:
        return f"You are {self.username}, an NPC in a videogame that takes place in a Discord server. " + \
            self.description + " --- Loves chatting on Discord. You are not a helpful assistant, just this person enjoying themselves on Discord." + \
            "You always respond in the format of a verbal conversation, " + \
            "never narrating, never putting your own words in quotes, never anything out of character whatsoever. You always start your message " + \
            f"with {self.username}:, and only respond with a single message, which will be attributed to {self.username}. " + \
            f"Remember, you only respond with a SINGLE message. NEVER pretend to be others. NEVER repeat what you see in the chat. " + \
            "Vary your vocabulary, and talk about your life when you are stuck." 
    
    def npc_sees_message(self, message: discord.Message) -> bool:
        return message.content.strip() != ""
    
    def update_messages(self, message: discord.Message) -> None:        
        if self.npc_sees_message(message):
            self.messages.appendleft(message)
            if len(self.messages) >= self.history_length:
                self.messages.pop()
    
    async def fill_messages(self) -> None:
        if self.channel == None:
            return
        async for msg in self.channel.history(limit=self.history_length):
            self.update_messages(msg)
            
    def consecutive_msg_limit_reached(self) -> bool:
        num_consecutive = 0
        for msg in list(self.messages):
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
    
    def make_completion_messages(self, system_prompt: str, mode: NPCPromptMode = NPCPromptMode.RELEVANCE_CHECKER) -> list[dict]:
        completion_messages = [{"role": "system", "content": system_prompt}]
        if mode == NPCPromptMode.RELEVANCE_CHECKER:
            chat_history = ""
            for message in reversed(self.messages):
                content = message.content.replace(str(self.client.user.id), self.username)
                chat_history += message.author.name + ": " + content + "\n"
            completion_messages.append({"role": "user", "content": chat_history})
        elif mode == NPCPromptMode.NPC:
            for message in reversed(self.messages):
                role = "assistant" if self.client.user.id == message.author.id else "user"
                completion_messages.append({"role": role, "content": message.author.name + ": " + message.content})
        else:
            raise Exception("chat completion mode set incorrectly. use either 'npc' or 'relevance_checker'.")
        return completion_messages
    
    def prompt_openai(self, completion_messages: list[dict]) -> str:
        assert(len(json.dumps(completion_messages)) <= 15000)
        assert(len(completion_messages) != 0)
        response = "bababooey"
        try:
            response = openai.ChatCompletion.create(model=self.model, messages=completion_messages,
                                                max_tokens=200, temperature=self.temperature,
                                                frequency_penalty=self.frequency_penalty)
            response = response.choices[0].message.content
        except Exception as e:
            print(e.args)
        return response
    
    async def is_response_appropriate(self) -> bool:
        # We're gonna run this through another OpenAI Prompt.
        system_prompt = "You are provided with a chat history, and you must judge how likely it is that " + \
                        "the a future response in this discord channel will " + \
                        f"come from the user described as follows: <{self.description}>. Please answer " + \
                        "concisely with either a number from 1 to 9. Do respond with anything else."
        completion_messages = self.make_completion_messages(system_prompt, mode=NPCPromptMode.RELEVANCE_CHECKER)
        
        response = await asyncio.to_thread(self.prompt_openai, completion_messages)
        for i in range(4,10):
            if str(i) in response:
                return True
        return False
    
    async def get_response_type(self) -> NPCResponse:
        if not self.is_chat_relevant():
            if random.randint(1, RANDOM_RESPONSE_ODDS) == 1:
                return NPCResponse.RANDOM
            else:
                return NPCResponse.SILENCE
        if self.consecutive_msg_limit_reached():
            return NPCResponse.SILENCE
        if await self.is_response_appropriate():
            return NPCResponse.DIRECT
        return NPCResponse.SILENCE
    
    async def prompt(self) -> str:
        completion_messages = self.make_completion_messages(self.system_message, mode=NPCPromptMode.NPC)
        response = await asyncio.to_thread(self.prompt_openai, completion_messages)
        return response
    
    def clean_response(self, response: str) -> str:
        pieces = response.split(":")
        if len(pieces) > 1:
            response = " ".join(pieces[1:])
        return response[:2000]
    
def main():
    pass

if __name__ == '__main__':
    main()