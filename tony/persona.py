import yaml
from yaml.loader import SafeLoader


class Persona:
    def __init__(self, config_path) -> None:
        # sourcery skip: raise-specific-error
        self.unique_traits = {}
        self.personality = []
        self.context = []
        data = None
        with open(config_path) as f:
            data: dict = yaml.load(f, Loader=SafeLoader)
        if data is None:
            raise Exception(
                "Bad NPC config yaml file: %s", config_path
            )  # TODO custom exception

        for name, item in data.items():
            if not isinstance(item, list):
                self.unique_traits[name] = item
            elif name == "personality":
                self.personality = item
            elif name == "context":
                self.context = item
            else:
                raise Exception(
                    "Bad NPC config yaml file: %s", config_path
                )  # TODO custom exception
        if (
            "username" not in self.unique_traits.keys()
            or "name" not in self.unique_traits.keys()
        ):
            raise Exception(
                "Bad NPC config yaml file: %s", config_path
            )  # TODO custom exception
        self.username = self.unique_traits["username"]
        self.name = self.unique_traits["name"]

    def make_description(self):
        traits_str = "".join(
            [f"{name}: {trait}, " for name, trait in self.unique_traits.items()]
        )
        personality_str = f"Personality traits: {', '.join(self.personality)}"  # TODO input error handling/testing
        context_str = f"Additional context: {', '.join(self.context)}. "
        return traits_str + "\n" + personality_str + "\n" + context_str
