from typing import Dict, List, Optional

import yaml
from yaml.loader import SafeLoader


class BadNPCConfigError(Exception):
    def __init__(self, config_path):
        super().__init__(f"Bad NPC config yaml file: {config_path}")


class Persona:
    def __init__(self, config_path) -> None:
        # sourcery skip: raise-specific-error
        self.unique_traits: Dict[str, str] = {}
        self.personality: List[str] = []
        self.context: List[str] = []
        data: Optional[dict] = None
        with open(config_path) as f:
            data = yaml.load(f, Loader=SafeLoader)
        if data is None:
            raise BadNPCConfigError(config_path)

        for name, item in data.items():
            if not isinstance(item, list):
                self.unique_traits[name] = item
            elif name == "personality":
                self.personality = item
            elif name == "context":
                self.context = item
            else:
                raise BadNPCConfigError(config_path)
        if (
            "username" not in self.unique_traits.keys()
            or "name" not in self.unique_traits.keys()
        ):
            raise BadNPCConfigError(config_path)
        self.username: str = self.unique_traits["username"]
        self.name: str = self.unique_traits["name"]

    def make_description(self):
        traits_str = "".join(
            [f"{name}: {trait}, " for name, trait in self.unique_traits.items()]
        )
        personality_str = f"Personality traits: {', '.join(self.personality)}"
        context_str = f"Additional context: {', '.join(self.context)}. "
        return traits_str + "\n" + personality_str + "\n" + context_str
