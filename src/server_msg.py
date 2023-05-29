from dataclasses import dataclass
from typing import Union

import discord


@dataclass
class ServerMsg:
    original_message: Union[discord.Message, None]
    display_name: str
    content: str
    created: str

    @classmethod
    def from_discord_message(cls, message: discord.Message):
        return ServerMsg(
            message,
            message.author.display_name,
            message.clean_content,
            message.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        )

    def __str__(self):
        return f"({self.created}) {self.display_name}: {self.content}"
