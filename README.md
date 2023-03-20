# Tony - AI Driven NPCs in Discord

## Intro

Ever wanted a bunch of new friends to keep your Discord server active and engaging?
Make your own characters and deploy them automatically with Tony.

## Usage
Clone this repo.
For each persona you will have to follow some steps in order to create an NPC.

### Step 1
Create a new Discord application and turn it into a bot.
Be sure to turn on all read and write permissions, and give your NPC a fitting description.
We recommend using [this-person-does-not-exist](https://this-person-does-not-exist.com) or [nightcafe](https://creator.nightcafe.studio/studio) to get profile pictures.

### Step 2
Add the bot's Discord auth token to a new file under src/bot_envs named `[YOUR NPC's NAME].env` containing
```sh
BOT_TOKEN=authtokengoeshere
OPENAI_KEY=openaiapikeygoeshere
```

### Step 3
Under `src/personas`, create a new file named `[YOUR NPC's NAME].yaml` containing
```yaml
name: (required)
username: (required)
age: (optional)
nationality: (optional)
ethnicity: (optional)
gender: (optional)
setting: (optional)
occupation: (optional)
personality:
  - (optional, sublist)
context:
  - (optional, sublist)
history_length: (required, 9 recommended)
model: (required, gpt-3.5-turbo-0301 recommended)
temperature: (required)
frequency_penalty: (required)
```

### Step 4
We recommend you use docker to develop and deploy your NPCs, but you can place the necessary files alongside `app.py` to run an NPC standalone.

Run `make docker_build bot_name=[YOUR NPC's NAME]`, and `docker run [YOUR NPC's NAME]` to test it.<br>
Login to your registry or use `make docker_login registry_domain=[YOUR REGISTRY DOMAIN]`,<br>
and run `make docker_push bot_name=[YOUR NPC's NAME] registry_domain=[YOUR REGISTRY DOMAIN]` to rebuild, tag, and push your image.



## Why 'Tony'?

Tony DeSalvo from Long Island was the first persona we made during a quick MVP of this project.