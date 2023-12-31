from pytezos import pytezos
from getpass import getpass
from dotenv import load_dotenv
import os
from pytezos.client import PyTezosClient
from tests.helpers.contracts import (
    Ticketer,
    RollupMock,
    Router,
    ContractHelper,
    TokenHelper,
    TicketHelper,
    FA12,
    FA2,
)
from tests.helpers.utility import (
    pkh,
    pack,
    make_address_bytes,
)
from typing import Type, TypeVar, Any, TypedDict, Union, Optional
from tests.helpers.tickets import Ticket


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


load_dotenv()
RPC_SHELL = os.getenv('RPC_SHELL') or 'https://rpc.tzkt.io/nairobinet/'
ALICE_PRIVATE_KEY = os.getenv('ALICE_PRIVATE_KEY') or getpass(
    'Enter Alice private key: '
)
BORIS_PRIVATE_KEY = os.getenv('BORIS_PRIVATE_KEY') or getpass(
    'Enter Boris private key: '
)


ROLLUP_SR_ADDRESS = 'sr1SkqgA2kLyB5ZqQWU5vdyMoNvWjYqtXGYY'
ERC20_PROXY_ADDRESS = ''
ALICE_L2_ADDRESS = ''


CONTRACT_ADDRESSES: AddressesType = {
    'fa12': {
        'token': '',
        'ticketer': '',
        'helper': '',
    },
    'fa2': {
        'token': '',
        'ticketer': '',
        'helper': '',
    },
    'router': '',
    'rollup_mock': '',
}


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
    amount: int = 100,
    rollup_address: str = ROLLUP_SR_ADDRESS,
) -> None:
    """This function wraps token to ticket and deposits it to rollup"""

    print(f'Depositing {amount} of {type(contracts["token"])} to {rollup_address}')
    token = contracts['token']
    ticketer = contracts['ticketer']
    helper = contracts['helper']
    ticket = ticketer.get_ticket()

    ticket_receiver = bytes.fromhex(ERC20_PROXY_ADDRESS)
    receiver = bytes.fromhex(ALICE_L2_ADDRESS)

    routing_info = ticket_receiver + receiver
    opg = client.bulk(
        token.allow(pkh(client), ticketer.address),
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
    fa12_external_metadata = {
        'decimals': pack(0, 'nat'),
        'symbol': pack('FA1.2-TST', 'string'),
    }
    fa12 = deploy_token_ticketer_helper(
        alice, FA12, balances, fa12_external_metadata
    )

    fa2_external_metadata = {
        'decimals': pack(0, 'nat'),
        'symbol': pack('FA2-TST', 'string'),
    }
    fa2 = deploy_token_ticketer_helper(
        alice, FA2, balances, fa2_external_metadata
    )

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

alice = pytezos.using(shell=RPC_SHELL, key=ALICE_PRIVATE_KEY)
boris = pytezos.using(shell=RPC_SHELL, key=BORIS_PRIVATE_KEY)


# If you use new accounts, you need to reveal them:
# alice.reveal().send()
# boris.reveal().send()


balances = {
    pkh(alice): 1_000_000,
    pkh(boris): 1_000_000,
}


def main() -> None:
    contracts = deploy_new(alice)
    contracts = load_contracts(alice, CONTRACT_ADDRESSES)
    deposit_to_l2(alice, contracts['fa12'], 100)
    # unpack_ticket(boris, contracts['fa12'], 10)


if __name__ == '__main__':
    main()
