from dataclasses import dataclass
import discord

@dataclass
class ServerMsg:
    display_name: str
    content: str
    created: str

    @classmethod
    def from_message(cls, message: discord.Message):
        return ServerMsg(message.author.display_name, message.clean_content, message.created_at)
    
    def __str__(self):
        return f"({self.created}) {self.display_name}: {self.content}"