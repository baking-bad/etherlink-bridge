from pytezos.client import PyTezosClient
from pytezos.rpc.query import RpcQuery


# TODO: consider improving this generic list type
def get_all_ticket_balances(client: PyTezosClient, address: str) -> list:
    # TODO: this might be not the best / easiest way to make RPC call,
    # need to research more to find good way to do this:
    last_block_hash = client.shell.head.hash()
    query = RpcQuery(
        node=client.shell.node,
        path='/chains/{}/blocks/{}/context/contracts/{}/all_ticket_balances',
        params=['main', last_block_hash, address]
    )

    result = query()
    assert type(result) is list
    return result
