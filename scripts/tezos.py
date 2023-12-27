from pytezos import pytezos
from pytezos.client import PyTezosClient
from tezos.tests.helpers.contracts import (
    Ticketer,
    RollupMock,
    Router,
    ContractHelper,
    TokenHelper,
    TicketHelper,
    FA12,
    FA2,
)
from tezos.tests.helpers.utility import (
    pkh,
    pack,
    make_address_bytes,
)
from typing import Type, TypeVar, Any, TypedDict, Union, Optional
from tezos.tests.helpers.tickets import Ticket
import click
from scripts.environment import load_or_ask
from enum import Enum


# TODO: remove this types:
class TokenSet(TypedDict):
    token: TokenHelper
    ticketer: Ticketer
    helper: TicketHelper


class ContractsType(TypedDict):
    fa12: TokenSet
    fa2: TokenSet
    router: Optional[Router]
    rollup_mock: Optional[RollupMock]


class AddressesType(TypedDict):
    fa12: dict[str, str]
    fa2: dict[str, str]
    router: str
    rollup_mock: str


def get_client() -> PyTezosClient:
    """Returns client with private key and rpc url set in environment variables"""

    rpc_url = load_or_ask('L1_RPC_URL')
    private_key = load_or_ask('L1_PRIVATE_KEY')
    client: PyTezosClient = pytezos.using(shell=rpc_url, key=private_key)
    return client


# TODO: consider moving this logic to TokenHelper
def get_token_cls(token_type: str) -> Type[TokenHelper]:
    """Returns token class by token type"""

    assert token_type in ['FA2', 'FA1.2']
    return FA12 if token_type == 'FA1.2' else FA2


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
@click.option('--private-key', default=None, help='Use the provided private key.')
@click.option('--rpc-url', default=None, help='Tezos RPC URL.')
def deploy_token(
    token_type: str,
    token_id: int,
    total_supply: int,
    private_key: Optional[str],
    rpc_url: Optional[str],
) -> TokenHelper:
    """Deploys token contract using provided key as a manager"""

    private_key = private_key or load_or_ask('L1_PRIVATE_KEY')
    rpc_url = rpc_url or load_or_ask('L1_RPC_URL')

    manager = pytezos.using(shell=rpc_url, key=private_key)
    Token = get_token_cls(token_type)
    balances = {pkh(manager): total_supply}
    opg = Token.originate(manager, balances, token_id).send()

    manager.wait(opg)
    token = Token.create_from_opg(manager, opg)
    return token


@click.command()
@click.option('--ticketer', required=True, help='The address of the ticketer contract.')
@click.option('--private-key', default=None, help='Use the provided private key.')
@click.option('--rpc-url', default=None, help='Tezos RPC URL.')
def get_ticketer_params(
    ticketer: str,
    private_key: Optional[str],
    rpc_url: Optional[str],
) -> dict[str, str]:
    """Founds ticketer in L1 and returns it params required for L2 ERC20 token deployment"""

    private_key = private_key or load_or_ask('L1_PRIVATE_KEY')
    rpc_url = rpc_url or load_or_ask('L1_RPC_URL')

    manager = pytezos.using(shell=rpc_url, key=private_key)
    ticketer_contract = Ticketer.create_from_address(manager, ticketer)
    ticket = ticketer_contract.get_ticket()
    address_bytes = make_address_bytes(ticketer_contract.address)
    content_bytes = ticket.make_bytes_payload()
    print(f'address_bytes: {address_bytes}')
    print(f'content_bytes: {content_bytes}')
    return {
        'address_bytes': address_bytes,
        'content_bytes': content_bytes,
    }


def make_extra_metadata(
    symbol: Optional[str],
    decimals: Optional[int],
) -> dict[str, bytes]:
    """Creates extra metadata for ticketer content with symbol and decimals"""

    extra_metadata = {}
    if decimals:
        extra_metadata['decimals'] = pack(decimals, 'nat')

    if symbol:
        extra_metadata['symbol'] = pack(symbol, 'string')
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
@click.option('--private-key', default=None, help='Use the provided private key.')
@click.option('--rpc-url', default=None, help='Tezos RPC URL.')
def deploy_ticketer(
    token_address: str,
    token_type: str,
    token_id: int,
    decimals: Optional[int],
    symbol: Optional[str],
    private_key: Optional[str],
    rpc_url: Optional[str],
) -> Ticketer:
    """Deploys `ticketer` contract using provided key as a manager"""

    private_key = private_key or load_or_ask('L1_PRIVATE_KEY')
    rpc_url = rpc_url or load_or_ask('L1_RPC_URL')
    # TODO: consider require token_id to be provided if token_type is FA2

    manager = pytezos.using(shell=rpc_url, key=private_key)
    Token = get_token_cls(token_type)
    token = Token.create_from_address(manager, token_address, token_id=token_id)
    extra_metadata = make_extra_metadata(symbol, decimals)
    opg = Ticketer.originate(manager, token, extra_metadata).send()
    manager.wait(opg)
    ticketer = Ticketer.create_from_opg(manager, opg)

    ticketer_params = get_ticketer_params.callback(
        ticketer.address, private_key, rpc_url
    )
    return ticketer


def deploy_router(manager: PyTezosClient) -> Router:
    print(f'Deploying Router...')
    router_opg = Router.originate_default(manager).send()
    manager.wait(router_opg)
    router = Router.create_from_opg(manager, router_opg)
    router_bytes = make_address_bytes(router.address)
    print(f'router address bytes: `{router_bytes}`')
    return router


def deploy_rollup_mock(manager: PyTezosClient) -> RollupMock:
    print(f'Deploying RollupMock...')
    rm_opg = RollupMock.originate_default(manager).send()
    manager.wait(rm_opg)
    return RollupMock.create_from_opg(manager, rm_opg)


def deploy_token_ticketer_helper(
    manager: PyTezosClient,
    token_type: type[TokenHelper],
    balances: dict[str, int],
    extra_metadata: dict[str, bytes],
) -> TokenSet:
    # Token deployment:
    print(f'Deploying token {token_type}...')
    token_opg = token_type.originate(manager, balances).send()
    manager.wait(token_opg)
    token = token_type.create_from_opg(manager, token_opg)

    # Deploying Ticketer with external metadata:
    ticketer_opg = Ticketer.originate(manager, token, extra_metadata).send()
    manager.wait(ticketer_opg)
    ticketer = Ticketer.create_from_opg(manager, ticketer_opg)

    # Deploying TicketHelper:
    print(f'Deploying TicketHelper...')
    ticket_helper_opg = TicketHelper.originate(manager, token, ticketer).send()
    manager.wait(ticket_helper_opg)
    ticket_helper = TicketHelper.create_from_opg(manager, ticket_helper_opg)

    ticket_payload = ticketer.get_ticket().make_bytes_payload()
    ticketer_bytes = make_address_bytes(ticketer.address)
    print('Data for setup ERC20 Proxy:')
    print(f'ticket address bytes: `{ticketer_bytes}`')
    print(f'ticket payload bytes: `{ticket_payload}`')
    return {
        'token': token,
        'ticketer': ticketer,
        'helper': ticket_helper,
    }


def load_token_set(
    manager: PyTezosClient,
    token_type: type[TokenHelper],
    addresses: dict[str, str],
) -> TokenSet:
    return {
        'token': token_type.create_from_address(manager, addresses['token']),
        'ticketer': Ticketer.create_from_address(manager, addresses['ticketer']),
        'helper': TicketHelper.create_from_address(manager, addresses['helper']),
    }


def deposit_to_l2(
    client: PyTezosClient,
    contracts: TokenSet,
    amount: int,
    rollup_address: str,
) -> None:
    """This function wraps token to ticket and deposits it to rollup"""

    print(f'Depositing {amount} of {type(contracts["token"])} to {rollup_address}')
    token = contracts['token']
    ticketer = contracts['ticketer']
    helper = contracts['helper']
    ticket = ticketer.get_ticket()

    proxy = bytes.fromhex(ERC20_PROXY_ADDRESS)
    receiver = bytes.fromhex(ALICE_L2_ADDRESS)

    routing_info = receiver + proxy
    opg = client.bulk(
        # TODO: there is a problem with UnsafeAllowanceChange for FA1.2 token (!)
        token.allow(pkh(client), helper.address),
        helper.deposit(rollup_address, routing_info, 100),
    ).send()
    client.wait(opg)
    print(f'Succeed, transaction hash: {opg.hash()}')


def unpack_ticket(
    client: PyTezosClient,
    contracts: TokenSet,
    amount: int = 3,
) -> None:
    """This function run ticket unpacking for given client"""

    helper = contracts['helper']
    ticketer = contracts['ticketer']
    ticket = ticketer.get_ticket()
    entrypoint = f'{helper.address}%withdraw'
    opg = ticket.using(client).transfer(entrypoint, amount).send()
    client.wait(opg)


def deploy_new(manager: PyTezosClient) -> ContractsType:
    balances = {pkh(manager): 1_000_000}
    fa12_external_metadata = {
        'decimals': pack(0, 'nat'),
        'symbol': pack('FA1.2-TST', 'string'),
    }
    fa12 = deploy_token_ticketer_helper(manager, FA12, balances, fa12_external_metadata)

    fa2_external_metadata = {
        'decimals': pack(0, 'nat'),
        'symbol': pack('FA2-TST', 'string'),
    }
    fa2 = deploy_token_ticketer_helper(manager, FA2, balances, fa2_external_metadata)

    return {
        'fa12': fa12,
        'fa2': fa2,
        'router': None,
        'rollup_mock': None,
    }


def load_contracts(
    manager: PyTezosClient,
    addresses: AddressesType,
) -> ContractsType:
    contracts: ContractsType = {
        'fa12': load_token_set(manager, FA12, addresses['fa12']),
        'fa2': load_token_set(manager, FA2, addresses['fa2']),
        'router': None,
        'rollup_mock': None,
    }
    router_address = addresses['router']
    if router_address:
        contracts['router'] = Router.create_from_address(
            manager,
            router_address,
        )

    rollup_mock_address = addresses['rollup_mock']
    if rollup_mock_address:
        contracts['rollup_mock'] = RollupMock.create_from_address(
            manager,
            rollup_mock_address,
        )

    return contracts


# TODO: sort this out:
import requests


class Proof(TypedDict):
    commitment: str
    proof: str


def get_proof(outbox_num: int) -> Proof:
    method = f'https://etherlink-rollup-nairobi.dipdup.net/global/block/head/helpers/proofs/outbox/{outbox_num}/messages?index=0'
    proof: Proof = requests.get(method).json()
    return proof


proof_fa12 = get_proof(2475504)
proof_fa2 = get_proof(2475536)

# alice.smart_rollup_execute_outbox_message(CONTRACT_ADDRESSES['rollup'], proof_fa12['commitment'], bytes.fromhex(proof_fa12['proof': f'])).send()
# alice.smart_rollup_execute_outbox_message(CONTRACT_ADDRESSES['rollup'], proof_fa2['commitment'], bytes.fromhex(proof_fa2['proof': f'])).send()


# TODO: is this function needed?
def get_messages(level: int) -> Any:
    method = f'https://etherlink-rollup-nairobi.dipdup.net/global/block/cemented/outbox/{level}/messages'
    return requests.get(method).json()
