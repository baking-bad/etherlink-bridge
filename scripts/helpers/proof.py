import requests
from typing import Any, TypedDict
from urllib.parse import urlparse, urlunparse, urlencode


class Proof(TypedDict):
    commitment: str
    proof: str


def get_proof(rpc_url: str, outbox_level: int, index: int) -> Proof:
    parts = urlparse(rpc_url)
    parts = parts._replace(
        path=f'global/block/head/helpers/proofs/outbox/{outbox_level}/messages',
        query=urlencode(dict(index=index)),
    )
    url = urlunparse(parts)
    proof: Proof = requests.get(url).json()
    return proof


def get_messages(rollup_rpc_url: str, outbox_level: int) -> Any:
    # NOTE: ROLLUP_RPC_URL is not the same as L2_RPC_URL

    parts = urlparse(rollup_rpc_url)
    parts = parts._replace(
        path=f'global/block/cemented/outbox/{outbox_level}/messages',
    )
    url = urlunparse(parts)
    print(url)
    return requests.get(url).json()
