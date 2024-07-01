import click
from typing import Optional
from scripts.helpers.contracts import Ticketer
from scripts.environment import get_tezos_client
from scripts.helpers.contracts import TokenHelper


# TODO: consider moving this to helpers?
def make_extra_metadata(
    name: Optional[str],
    symbol: Optional[str],
    decimals: Optional[int],
) -> dict[str, bytes]:
    """Creates extra metadata for ticketer content with name, symbol and decimals"""

    extra_metadata = {}
    if name:
        extra_metadata['name'] = name.encode('utf-8')

    if symbol:
        extra_metadata['symbol'] = symbol.encode('utf-8')

    if decimals:
        extra_metadata['decimals'] = str(decimals).encode('utf-8')

    return extra_metadata


@click.command()
@click.option(
    '--token-address', required=True, help='The address of the token contract.'
)
# TODO: consider auto-determine token type by token entrypoints
@click.option(
    '--token-type', required=True, help='Token type, either `FA2` or `FA1.2`.'
)
@click.option(
    '--token-id',
    default=0,
    help='Identifier of the token in the contract (only for FA2), default: 0.',
)
@click.option(
    '--decimals',
    default=None,
    help='Token decimals added to the ticketer metadata content. If not set, will be not added to the content.',
)
@click.option(
    '--symbol',
    default=None,
    help='Token symbol added to the ticketer metadata content.',
)
@click.option(
    '--name',
    default=None,
    help='Token name added to the ticketer metadata content.',
)
@click.option(
    '--private-key',
    default=None,
    help='Private key that would be used to deploy contract on the Tezos network.',
)
@click.option('--rpc-url', default=None, help='Tezos RPC URL.')
def deploy_ticketer(
    token_address: str,
    token_type: str,
    token_id: int,
    decimals: Optional[int],
    symbol: Optional[str],
    name: Optional[str],
    private_key: Optional[str],
    rpc_url: Optional[str],
) -> Ticketer:
    """Deploys `ticketer` contract using provided key as a manager"""

    # TODO: consider require token_id to be provided if token_type is FA2
    # TODO: - it is possible to change Token.from_address implementation so it will
    #       return FA2 or FA1.2 token based on the token entrypoints and fail if
    #       token_id is not provided for FA2

    manager = get_tezos_client(rpc_url, private_key)
    Token = TokenHelper.get_cls(token_type)
    token = Token.from_address(manager, token_address, token_id=token_id)
    extra_metadata = make_extra_metadata(name, symbol, decimals)
    # TODO: consider awaiting action from user before deploying
    opg = Ticketer.originate(manager, token, extra_metadata).send()
    manager.wait(opg)
    ticketer = Ticketer.from_opg(manager, opg)
    # TODO: consider printing ticketer address and params for ERC20?
    return ticketer
