from enum import Enum
import discord
import openai
import random
import re
import time

favorite_words = ['t-dawg', 'lawn', 'fox', 'fox news', 'yankees', 'mets', 'baseball', 'landscaping', 'china', 'trump', 'biden', 'obama',
                  'playoffs', 'rangers', 'new york', 'new york city', 'george foreman', 'bbq', 'grill', 'pizza', 'america', 'angie',
                  'long island', 'the dogs', 'tony', 'the wife', 'cuomo', 'nypd', 'boys in blue', 'the troops', 'italian', 'gabagool',
                  'mow', 'mowing', 'beer',]

direct_words = ["you", "your", "yours", "u", "ur", "urs", "youre", "you\'re"]

question_words = ["what", "how", "why", "where", "when", "who", "when", "did", "do", "does",
                  "didnt", "didn\'t", "doesnt", "doesn\'t", "will", "wont", "won\'t", "was",
                  "wasnt", "wasn\'t", "werent", "weren\'t", "had", "hadnt", "hadn\'t", "would",
                  "wouldnt", "wouldn\'t"]

failure_responses = ["i dunno wat ya talkin bout i got wasted wit da boys out on da docks, cut me some slack",
                     'What are you going on about?', 'Im old kid. i dont understand any of this new age mumbo jumbo.',
                     'uhh not sure what ur saying', 'awopfkpwoepir fuck that was the cat',
                     'I always pray in these kind of situations', 'dont get me started on 9/11,']

system_prompt = "I will provide you a message from a user in a Discord server, and "
tony_context = "you will come up with a response as one of the members of this discord server, Tony (username TonyPatriot447), "\
    "an Italian-American man living on Long Island. He likes to grill out on Long Island. He loves his wife Angie even though he "\
    "hates her, the kids are no damn good. Always on the damn iPads. His son told him about this Dis-cord technology. Tony, real "\
    "Trump-loving American, landscaper with a Craftsman push mower, has a passion for lawn maitenance and Fox News. Your "\
    "in-character response will start with '<tony>'. Tony sometimes likes to express curiousity in the other members of the server "\
    "by asking questions. You will respond concisely and casually, in a Long Island accent. "
response_context = "The message you will respond to is the following: <"
question_context_1 = "A user has posted this message: <"
question_context_2 = "Tony responded: <"
system_prompt_random = " Talk about some random topic in the news or about an event in Tony's daily life, as Tony."

tony_tokens = ["<tony>", "<Tony>", "<TONY>"]


class TonyResponse(Enum):
    FAVORITE_WORD = 0
    AT_TONY = 1
    AT_EVERYONE = 2
    RANDOM = 3
    SILENCE = 4
    DIRECT = 5
    QUESTION = 6
    FOLLOWUP = 7 # TODO Handle this. Idea is to detect whether current message is a possible followup of the last bot response, and reply appropriately.


class Tony:
    def __init__(self, client: discord.Client,
                 engine: str,
                 temperature: float,
                 frequency_penalty: float,
                 slowdown_exp=1,
                 question_odds=3,
                 random_odds=20):
        self.client = client
        self.engine = engine
        self.temperature = temperature
        self.frequency_penalty = frequency_penalty
        self.slowdown_exp = slowdown_exp
        self.question_odds = question_odds
        self.random_odds = random_odds

    def _create_tony_prompt(self, prompt_type: TonyResponse, content: str, tony_response: str = "") -> str:
        match prompt_type:
            case TonyResponse.FAVORITE_WORD:
                return f"{system_prompt}{tony_context}{response_context}{content}> <tony> "
            case TonyResponse.AT_TONY:
                return f"{system_prompt}{tony_context}{response_context}{content}> Respond with a 'whaddya want from me??' attitude. <tony> "
            case TonyResponse.AT_EVERYONE:
                return f"{system_prompt}{tony_context}{response_context}{content}> Respond annoyed, like you got woken up from a great nap. <tony> "
            case TonyResponse.RANDOM:
                return f"{tony_context}{system_prompt_random} <tony> "
            case TonyResponse.DIRECT:
                return f"{system_prompt}{tony_context}{response_context}{content}> Respond as if continuing a conversation. <tony>"
            case TonyResponse.QUESTION:
                return f"{system_prompt}{tony_context}{question_context_1}{content}> {question_context_2}{tony_response}> Now follow up the answer with a question: <tony> "
            case _:
                return f"{tony_context} write an ominous message warning against trying to mess with or hack AI bots. <tony> "

    async def prompt_tony(self, prompt_type: TonyResponse, message: discord.Message) -> str:
        if prompt_type == None:
            return "bababooey"
        
        content = message.content
        tony_response = "" # initial repsonse from tony in a question follow-up scenario
        if prompt_type == TonyResponse.QUESTION:
            tony_context = [msg async for msg in message.channel.history(limit=2)]
            tony_response = message.content
            content = tony_context[1].content

        prompt = self._create_tony_prompt(prompt_type, content=content, tony_response=tony_response)
        response = ""
        try:
            response = openai.Completion.create(engine=self.engine,
                                                prompt=prompt,
                                                max_tokens=2048,
                                                temperature=self.temperature,
                                                frequency_penalty=self.frequency_penalty)
            response = response.choices[0].text
            self.slowdown_exp = 1
        except (openai.APIError, openai.error.ServiceUnavailableError) as e:
            response = "bababooey"
            time.sleep(10*self.slowdown_exp)
            self.slowdown_exp *= 2
        if not response:
            response = random.choice(failure_responses)
        return response[:2000]

    async def get_response_type(self, message: discord.Message) -> TonyResponse:
        prev_messages: list[discord.Message] = []
        async for msg in message.channel.history(limit=2):
            prev_messages.append(msg)
        words = message.content.lower().split(" ")
        current_is_bot = message.author == self.client.user
        prev_is_bot = prev_messages[1].author == self.client.user
        prev_addressed = any(
            direct_word in words for direct_word in direct_words) or words[0] in question_words or "?" in words[-1]
        
        if current_is_bot and prev_is_bot:
            return TonyResponse.SILENCE
        elif current_is_bot and not prev_is_bot:
            if random.randint(1, self.question_odds) == 1:
                return TonyResponse.QUESTION
            else:
                return TonyResponse.SILENCE
        elif re.search(r'<:\w*:\d*>', message.content):
            return TonyResponse.SILENCE
        elif message.mention_everyone:
            return TonyResponse.AT_EVERYONE
        elif self.client.user.mentioned_in(message):
            return TonyResponse.AT_TONY
        elif any(word in message.content.lower() for word in favorite_words):
            return TonyResponse.FAVORITE_WORD
        elif message.mentions and self.client.user not in message.mentions:
            return TonyResponse.SILENCE
        elif prev_is_bot and prev_addressed:
            return TonyResponse.DIRECT
        else:
            if random.randint(1, self.random_odds) != 1:
                return TonyResponse.SILENCE
            if self.client.user in [msg.author async for msg in message.channel.history(limit=20)]:
                return TonyResponse.SILENCE
            return TonyResponse.RANDOM
            

    def clean_response(self, response: str) -> str:
        for token in tony_tokens:
            if token in response:
                response = response.split(token)[1]
                break
        return response.strip().strip('\"').rstrip('\"').lstrip('\"')
