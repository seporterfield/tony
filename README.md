# Tony - AI Driven NPCs

Tony is a python library for running large language model (LLM) based NPCs in multi-user chat environments.

## Quick Start (Discord)

Create a [persona file](#creating-a-persona).


Replace the defaults in [.env_template](./.env_template) with your secret keys and rename it `.env`.


Start the Redis server with `docker run -d --name redis-stack-server -p 6379:6379 redis/redis-stack-server:latest`.


Run the bot with `python app.py --persona path-to-your-persona.yaml`.


## Creating a Persona

You can create a persona for your NPC in a `.yaml` file with the following structure:
```yaml
    # These four traits are required
    name: ...
    username: ...
    personality:
        - ...
        ...
    context:
        - ...
        ...
    
    # We recommend including other unique traits, named whatever you want!
    # For example:
    age: ...
    setting: ...
```
## Currently Supported Clients

- Discord