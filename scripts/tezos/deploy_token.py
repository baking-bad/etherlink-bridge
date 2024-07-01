import click
from typing import Optional
from scripts.helpers.contracts import TokenHelper
from scripts.environment import get_tezos_client
from scripts.helpers.addressable import Addressable


# TODO: add logic from the bootstrap branch
@click.command()
@click.option(
    '--token-type',
    required=True,
    help='Token type used for deploy, either `FA2` or `FA1.2`.',
)
@click.option(
    '--token-id',
    default=0,
    help='Identifier for the token in the contract (only for FA2), default: 0.',
)
@click.option(
    '--total-supply',
    default=1_000_000,
    help='Total supply of originated token which will be mint for the manager, default: 1_000_000.',
)
@click.option(
    '--private-key',
    default=None,
    help='Private key that would be used to deploy token on the Tezos network.',
)
@click.option('--rpc-url', default=None, help='Tezos RPC URL.')
def deploy_token(
    token_type: str,
    token_id: int,
    total_supply: int,
    private_key: Optional[str],
    rpc_url: Optional[str],
) -> TokenHelper:
    """Deploys token contract using provided key as a manager"""

    manager = get_tezos_client(rpc_url, private_key)
    Token = TokenHelper.get_cls(token_type)
    balances: dict[Addressable, int] = {manager: total_supply}
    opg = Token.originate(manager, balances, token_id).send()
    manager.wait(opg)
    token = Token.from_opg(manager, opg)
    return token
