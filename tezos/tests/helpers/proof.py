import requests
from typing import Any, TypedDict


class Proof(TypedDict):
    commitment: str
    proof: str


def get_proof(outbox_num: int) -> Proof:
    method = f'https://etherlink-rollup-nairobi.dipdup.net/global/block/head/helpers/proofs/outbox/{outbox_num}/messages?index=0'
    proof: Proof = requests.get(method).json()
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
