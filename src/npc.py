from persona import Persona
class DiscordNPC:

    name: str

    def __init__(self, persona: Persona, user, logger):
        pass

    def prompt(self):
        # Prep inputs from persona
        # Get response from langchain
        pass

    async def fill_messages(self):
        # Get messages from user.channel
        # Fill langchain conversation
        # Fill embeddings store
        pass

    async def update_messages(self, message):
        # Add message to langchain conversation
        # Add message to embeddings store
        pass

    async def get_response_type(self):
        # Decide whether or not to be silent
        # Emotional threshold? Bool?
        pass
