from pytezos import pytezos
from pytezos.client import PyTezosClient
from tezos.tests.helpers.contracts import (
    Ticketer,
    RollupMock,
    Router,
    TokenHelper,
    TicketHelper,
)
from tezos.tests.helpers.utility import (
    pkh,
    pack,
    make_address_bytes,
)
from typing import Optional
import click
from scripts.environment import load_or_ask
from tezos.tests.helpers.proof import (
    get_proof as get_proof_from_rpc,
    Proof,
)


def get_client() -> PyTezosClient:
    """Returns client with private key and rpc url set in environment variables"""

    rpc_url = load_or_ask('L1_RPC_URL')
    private_key = load_or_ask('L1_PRIVATE_KEY', is_secret=True)
    client: PyTezosClient = pytezos.using(shell=rpc_url, key=private_key)
    return client


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

    private_key = private_key or load_or_ask('L1_PRIVATE_KEY', is_secret=True)
    rpc_url = rpc_url or load_or_ask('L1_RPC_URL')

    manager = pytezos.using(shell=rpc_url, key=private_key)
    Token = TokenHelper.get_cls(token_type)
    balances = {pkh(manager): total_supply}
    opg = Token.originate(manager, balances, token_id).send()
    manager.wait(opg)
    token = Token.from_opg(manager, opg)
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

    private_key = private_key or load_or_ask('L1_PRIVATE_KEY', is_secret=True)
    rpc_url = rpc_url or load_or_ask('L1_RPC_URL')

    manager = pytezos.using(shell=rpc_url, key=private_key)
    ticketer_contract = Ticketer.from_address(manager, ticketer)
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

    private_key = private_key or load_or_ask('L1_PRIVATE_KEY', is_secret=True)
    rpc_url = rpc_url or load_or_ask('L1_RPC_URL')
    # TODO: consider require token_id to be provided if token_type is FA2

    manager = pytezos.using(shell=rpc_url, key=private_key)
    Token = TokenHelper.get_cls(token_type)
    token = Token.from_address(manager, token_address, token_id=token_id)
    extra_metadata = make_extra_metadata(symbol, decimals)
    opg = Ticketer.originate(manager, token, extra_metadata).send()
    manager.wait(opg)
    ticketer = Ticketer.from_opg(manager, opg)

    _ticketer_params = get_ticketer_params.callback(
        ticketer.address, private_key, rpc_url
    )  # type: ignore
    return ticketer


@click.command()
@click.option(
    '--ticketer-address', required=True, help='The address of the ticketer contract.'
)
@click.option('--private-key', default=None, help='Use the provided private key.')
@click.option('--rpc-url', default=None, help='Tezos RPC URL.')
def deploy_ticket_helper(
    ticketer_address: str,
    private_key: Optional[str],
    rpc_url: Optional[str],
) -> TicketHelper:
    """Deploys `ticket_helper` contract for provided ticketer"""

    private_key = private_key or load_or_ask('L1_PRIVATE_KEY', is_secret=True)
    rpc_url = rpc_url or load_or_ask('L1_RPC_URL')

    manager = pytezos.using(shell=rpc_url, key=private_key)
    ticketer = Ticketer.from_address(manager, ticketer_address)
    opg = TicketHelper.originate(manager, ticketer).send()
    manager.wait(opg)
    ticket_helper = TicketHelper.from_opg(manager, opg)
    return ticket_helper


def deploy_router(manager: PyTezosClient) -> Router:
    print('Deploying Router...')
    router_opg = Router.originate(manager).send()
    manager.wait(router_opg)
    router = Router.from_opg(manager, router_opg)
    router_bytes = make_address_bytes(router.address)
    print(f'router address bytes: `{router_bytes}`')
    return router


def deploy_rollup_mock(manager: PyTezosClient) -> RollupMock:
    print('Deploying RollupMock...')
    rm_opg = RollupMock.originate(manager).send()
    manager.wait(rm_opg)
    return RollupMock.from_opg(manager, rm_opg)


@click.command()
@click.option(
    '--ticket-helper-address',
    required=True,
    help='The address of the Tezos ticket helper contract.',
)
@click.option(
    '--proxy-address',
    required=True,
    help='The address of the ERC20 proxy token contract which should mint token.',
)
@click.option(
    '--amount', required=True, type=int, help='The amount of tokens to be deposited.'
)
@click.option(
    '--receiver-address',
    default=None,
    help='The address of the Etherlink receiver contract which should receive token.',
)
@click.option(
    '--rollup-address', default=None, help='The address of the rollup contract.'
)
@click.option('--private-key', default=None, help='Use the provided private key.')
@click.option('--rpc-url', default=None, help='Tezos RPC URL.')
def deposit(
    ticket_helper_address: str,
    proxy_address: str,
    amount: int,
    receiver_address: Optional[str],
    rollup_address: Optional[str],
    private_key: Optional[str],
    rpc_url: Optional[str],
) -> None:
    """Deposits given amount of given token to the Etherlink Bridge"""

    def prepare_routing_info(proxy_address: str, receiver_address: str) -> bytes:
        proxy_address = proxy_address.replace('0x', '')
        receiver_address = receiver_address.replace('0x', '')
        proxy = bytes.fromhex(proxy_address)
        receiver = bytes.fromhex(receiver_address)
        return receiver + proxy

    private_key = private_key or load_or_ask('L1_PRIVATE_KEY', is_secret=True)
    receiver_address = receiver_address or load_or_ask('L2_PUBLIC_KEY')
    rpc_url = rpc_url or load_or_ask('L1_RPC_URL')
    rollup_address = rollup_address or load_or_ask('L1_ROLLUP_ADDRESS')

    manager = pytezos.using(shell=rpc_url, key=private_key)
    ticket_helper = TicketHelper.from_address(manager, ticket_helper_address)
    token = ticket_helper.get_ticketer().get_token()

    routing_info = prepare_routing_info(proxy_address, receiver_address)
    opg = manager.bulk(
        # TODO: there is a problem with UnsafeAllowanceChange for FA1.2 token (!)
        token.allow(pkh(manager), ticket_helper.address),
        ticket_helper.deposit(rollup_address, routing_info, amount),
    ).send()
    manager.wait(opg)
    print(f'Succeed, transaction hash: {opg.hash()}')


@click.command()
@click.option('--level', required=True, type=int, help='The level of the outbox.')
@click.option('--index', required=True, type=int, help='The index of the message.')
@click.option('--rpc-url', default=None, help='Etherlink RPC URL.')
def get_proof(
    level: int,
    index: int,
    rpc_url: Optional[str],
) -> Proof:
    """Makes call to the RPC and returns proof info required to execute outbox_message"""

    rpc_url = rpc_url or load_or_ask('L2_RPC_URL')
    proof = get_proof_from_rpc(rpc_url, level, index)
    print(f'proof: {proof}')
    return proof


'''
	- [ ] execute_outbox_message
		- Action: executes outbox message using provided `commitment` and `proof`
		- Parameters:
			- `commitment`
			- `proof`
			- OPTIONAL: `private_key: str` (`.env`: `L1_PRIVATE_KEY`)
		- Returns:
			- `transaction_hash: bytes`
'''


@click.command()
@click.option(
    '--commitment', required=True, help='The commitment of the outbox message.'
)
@click.option('--proof', required=True, help='The proof of the outbox message.')
@click.option(
    '--rollup-address', default=None, help='The address of the rollup contract.'
)
@click.option('--private-key', default=None, help='Use the provided private key.')
@click.option('--rpc-url', default=None, help='Tezos RPC URL.')
def execute_outbox_message(
    commitment: str,
    proof: str,
    private_key: Optional[str],
    rpc_url: Optional[str],
) -> None:
    """Executes outbox message using provided `commitment` and `proof`"""

    rollup_address = load_or_ask('L1_ROLLUP_ADDRESS')
    private_key = private_key or load_or_ask('L1_PRIVATE_KEY', is_secret=True)
    rpc_url = rpc_url or load_or_ask('L1_RPC_URL')

    manager = pytezos.using(shell=rpc_url, key=private_key)
    opg = manager.smart_rollup_execute_outbox_message(
        rollup_address, commitment, bytes.fromhex(proof)
    ).send()
    manager.wait(opg)
    print(f'Succeed, transaction hash: {opg.hash()}')


# TODO: rework these functions:
'''
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
'''
