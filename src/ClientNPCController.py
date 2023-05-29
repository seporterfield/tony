import asyncio
from typing import Any

from src.ClientHandler import ClientHandler
from src.NPC import NPC


class ClientNPCController:
    def __init__(
        self, client_handler: ClientHandler, npc: NPC, reading_time: float = 1.0
    ) -> None:
        self.client_handler: ClientHandler = client_handler
        self.npc = npc
        self.reading_time = reading_time
        self.client_handler.set_controller(self)
        self.replying = False

    def generate_reply(self) -> str:
        # Get reply
        response = "..."
        try:
            response = self.npc.get_npc_response()
        except Exception as e:
            print("Failed to get NPC response\n", e.with_traceback(e.__traceback__))
        return response

    async def try_reply_to_message(self, message: Any):
        if await self.client_handler.should_reply_to_msg(message):
            reply = self.generate_reply()
            reply_channel = self.client_handler.get_message_channel(message)
            await self.client_handler.message_channel(reply, reply_channel)

    async def update_message_history(self, message: Any):
        chat_history = await self.client_handler.get_chat_history(message)
        self.npc.fill_messages(msglist=chat_history)

    def on_ready(self):
        self.client_handler.on_ready()

    async def on_resumed(self):
        message = self.client_handler.on_resumed(self.npc.chat_history)
        if message is not None:
            self.try_reply_to_message(message=message)

    async def on_message(self, message):
        if self.replying:
            return
        self.replying = True
        await self.client_handler.on_message(message)
        await self.update_message_history(message)
        await self.try_reply_to_message(message)
        await asyncio.sleep(self.reading_time)
        self.replying = False