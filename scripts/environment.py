from dotenv import load_dotenv
from getpass import getpass
import os


def load_or_ask(var_name: str, secret: bool = False) -> str:
    ask = getpass if secret else input
    return os.getenv(var_name) or ask(f'Enter {var_name}: ')  # type: ignore


load_dotenv()
