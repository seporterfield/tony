import discord
import openai
from enum import Enum
import random
from collections import deque
from logging import Logger
import logging
import json
import asyncio
import yaml
from yaml.loader import SafeLoader
from multiprocessing.context import Process
from multiprocessing import Queue

RANDOM_RESPONSE_ODDS = 40
MAX_TOKENS = 200
MAX_OPENAI_API_CALL_ATTEMPTS = 5
OPENAI_TIMEOUT = 12

class NPCPromptMode(Enum):
    NPC = 1
    RELEVANCE_CHECKER = 2

class NPCResponse(Enum):
    SILENCE = 1
    DIRECT = 2
    RANDOM = 3


class NPC:
    @classmethod
    def make_description(cls, name, username, age, gender, setting, occupation, personality, context):
        return f" Name: {name}, Username: {username}, Age: {age}, Gender: {gender}, " + \
            f"Setting: {setting}, Occupation: {occupation}, Personality traits: {'---'.join(personality)}, " + \
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
                   occupation=data['occupation'],
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
                 occupation: str = "unknown",
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
        self.occupation = occupation
        self.personality = personality
        self.context = context
        
        self.client = client
        self.channel = channel
        self.description = NPC.make_description(name=name, username=username, age=age,
                                                gender=gender, setting=setting, occupation=occupation,
                                                personality=personality, context=context)
        self.system_message = self.make_system_message()
        self.model = model
        self.history_length = history_length
        self.temperature = temperature
        self.frequency_penalty = frequency_penalty
        self.logger = logger
        
        self.messages = deque()
        self.consecutive_message_limit = 3
        self.is_active = False
    
    def make_system_message(self) -> str:
        return f"You are {self.username}, an NPC in a videogame that takes place in a Discord server. " + \
            self.description + " --- Loves chatting on Discord. You are not a helpful assistant, just this person enjoying themselves on Discord." + \
            "You always respond in the format of a verbal conversation, " + \
            "never narrating, never putting your own words in quotes, never anything out of character whatsoever. You identify with messages " + \
            f"starting with {self.username}:, and only respond with a single message, which will be attributed to {self.username}. " + \
            "Vary your vocabulary, and vent about life when you are stuck. Reply with '(AFK)' to stop looking at discord, and with '(Watch)' to continue watching the server but stop responding." + \
            " NEVER pretend to be others. NEVER reply with a message similar to any you see. "
                
    
    def npc_sees_message(self, message: discord.Message) -> bool:
        self.logger.debug(f"sees it?: {message.content}")
        return message.content.strip() != ""
    
    def view_new_message(self, message: discord.Message) -> None:
        if self.npc_sees_message(message):
            self.logger.debug(f"{self.name}|saw it!: {message.content}")
            self.messages.append(message)
            if len(self.messages) > self.history_length:
                popped = self.messages.popleft()
                self.logger.debug(f"{self.name}|popped: {popped.content}")
    
    async def fill_messages(self, channel: discord.TextChannel = None) -> None:
        if channel == None:
            return
        msglist = []
        async for msg in channel.history(limit=self.history_length):
            msglist.append(msg)
        for idx, msg in enumerate(reversed(msglist)):
            self.logger.debug(f"{self.name}|viewing new message {idx}: {msg.content}")
            self.view_new_message(msg)
            
    async def update_messages(self, message: discord.Message) -> None:
        #self.view_new_message(message=message)
        await self.fill_messages(message.channel)
            
    def consecutive_msg_limit_reached(self) -> bool:
        num_consecutive = 0
        for idx, msg in enumerate(reversed(self.messages)):
            self.logger.debug(f"{idx} {msg.content}")
            if msg.author.id != self.client.user.id:
                break
            num_consecutive += 1
        return num_consecutive >= self.consecutive_message_limit
        
    async def is_chat_relevant(self) -> bool:
        new_msg = ""
        if self.messages:
            new_msg: discord.Message = self.messages[-1]
        else:
            raise Exception("Message history was not able to update properly.")
        self.logger.debug("checking relevancy: {0.content}".format(new_msg))
        if self.client.user.mentioned_in(new_msg):
            self.logger.debug(f"{self.username} Mentioned!")
            self.is_active = True
        if new_msg.mention_everyone:
            self.logger.debug("EVERYONE mentioned!")
            self.is_active = True
        if new_msg.reference != None:
            replied_msg: discord.Message = await new_msg.channel.fetch_message(new_msg.reference.message_id)
            if  replied_msg.author.id == self.client.user.id:
                self.logger.debug(f"{self.username} replied to!")
                self.is_active = True
            else:
                self.logger.debug("message was reply but not to bot")
                    
        return self.is_active
    
    def make_completion_messages(self, system_prompt: str, mode: NPCPromptMode = NPCPromptMode.RELEVANCE_CHECKER) -> list[dict]:
        completion_messages = [{"role": "system", "content": system_prompt}]
        if mode == NPCPromptMode.RELEVANCE_CHECKER:
            chat_history = ""
            for message in self.messages:
                content = message.content.replace(str(self.client.user.id), self.username)
                chat_history += message.author.name + ": " + content + "\n"
            completion_messages.append({"role": "user", "content": chat_history})
        elif mode == NPCPromptMode.NPC:
            for message in self.messages:
                role = "assistant" if self.client.user.id == message.author.id else "user"
                completion_messages.append({"role": role, "content": message.author.name + ": " + message.content})
        else:
            raise Exception("chat completion mode set incorrectly. use either 'npc' or 'relevance_checker'.")
        self.logger.debug(completion_messages)
        return completion_messages
    
    def api_call_openai(self, messages, queue: Queue):
        response = None
        try:
            response = (openai.ChatCompletion.create(model=self.model,
                                                    messages=messages,
                                                    max_tokens=MAX_TOKENS,
                                                    temperature=self.temperature,
                                                    frequency_penalty=self.frequency_penalty))
        except Exception:
            response = None
        queue.put(response)
    
    async def prompt_openai(self, completion_messages: list[dict]) -> str:
        print("MADE IT TO PROMPT!!")
        #assert(len(json.dumps(completion_messages)) <= 15000)
        #assert(len(completion_messages) != 0)
        response = ""
        response_queue = Queue()
        for i in range(MAX_OPENAI_API_CALL_ATTEMPTS + 1):
            if i == MAX_OPENAI_API_CALL_ATTEMPTS:
                self.logger.warning("MAX CALLS TO OPENAI API REACHED. SHUTTING OFF BOT CLIENT!")
                await self.client.close()
                break
            
            api_process: Process = Process(target=self.api_call_openai, args=(completion_messages, response_queue))
            api_process.start()
            # Wait for the process to finish, or for the timeout to expire
            await asyncio.sleep(OPENAI_TIMEOUT)
            if api_process.is_alive():
                self.logger.warning(f"OpenAI API Timed out {i+1} times...")
                api_process.terminate()
                continue
            response = response_queue.get()
            if response == None:
                continue
            else:
                break
        self.logger.debug(f"{self.name}|OpenAI response: {response}")
        if response:
            response = response.choices[0].message.content
        else:
            response = "..."
        return response
    
    
    async def get_response_type(self) -> NPCResponse:
        if not await self.is_chat_relevant():
            if random.randint(1, RANDOM_RESPONSE_ODDS) == 1:
                return NPCResponse.RANDOM
            else:
                return NPCResponse.SILENCE
        if self.consecutive_msg_limit_reached():
            return NPCResponse.SILENCE
        return NPCResponse.DIRECT
    
    async def prompt(self) -> str:
        completion_messages = self.make_completion_messages(self.system_message, mode=NPCPromptMode.NPC)
        response = await self.prompt_openai(completion_messages)
        return response
    
    def clean_response(self, response: str) -> str:
        if "(afk)" in response.lower():
            self.active = False
            response = ""
        elif "(watch)" in response.lower():
            self.is_active = True
            response = ""
        else:
            self.is_active = True
            
        pieces = response.split(":")
        if len(pieces) > 1:
            response = " ".join(pieces[1:])
        return response[:2000]
    
def main():
    pass

if __name__ == '__main__':
    main()