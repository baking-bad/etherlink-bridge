import requests
from typing import Any, TypedDict
from urllib.parse import urlparse, urlunparse, urlencode


class Proof(TypedDict):
    commitment: str
    proof: str


def get_proof(rollup_rpc_url: str, outbox_level: int, index: int) -> Proof:
    parts = urlparse(rollup_rpc_url)
    parts = parts._replace(
        path=f'global/block/head/helpers/proofs/outbox/{outbox_level}/messages',
        query=urlencode(dict(index=index)),
    )
    url = urlunparse(parts)
    proof: Proof = requests.get(url).json()
    return proof


def get_cemented_messages(rollup_rpc_url: str, outbox_level: int) -> Any:
    parts = urlparse(rollup_rpc_url)
    parts = parts._replace(
        path=f'global/block/cemented/outbox/{outbox_level}/messages',
    )
    url = urlunparse(parts)
    return requests.get(url).json()


def get_messages(rollup_rpc_url: str, outbox_level: int) -> Any:
    parts = urlparse(rollup_rpc_url)
    parts = parts._replace(
        path=f'global/block/head/outbox/{outbox_level}/messages',
    )
    url = urlunparse(parts)
    return requests.get(url).json()
