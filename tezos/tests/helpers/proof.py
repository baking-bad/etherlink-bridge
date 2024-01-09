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


# TODO: is this function needed?
def get_messages(level: int) -> Any:
    method = f'https://etherlink-rollup-nairobi.dipdup.net/global/block/cemented/outbox/{level}/messages'
    return requests.get(method).json()


# TODO: create function to make execute_outbox_message calls, example:
# proof_fa12 = get_proof(2475504)
# proof_fa2 = get_proof(2475536)
# client.smart_rollup_execute_outbox_message(rollup_address, proof_fa12['commitment'], bytes.fromhex(proof_fa12['proof': f'])).send()
# client.smart_rollup_execute_outbox_message(rollup_address, proof_fa2['commitment'], bytes.fromhex(proof_fa2['proof': f'])).send()
