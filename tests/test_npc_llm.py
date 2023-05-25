from tony.npc_llm import NPCLLM
import dotenv

dotenv.load_dotenv()


def test_llm_prompt():
    llm = NPCLLM.from_config("persona.yaml")
    resp = llm.prompt(
        "zd: I wanna quit my job so bad\nLalo Salamanca: balls man gay\n zd: bruh wtf why my nutsack itchy\nCuck Conoisseur: try some baby powder or just an open flame lol.",
        "Cuck Conoisseur: I hear itchy balls are a big problem in north korea!",
    )
    print(resp)
