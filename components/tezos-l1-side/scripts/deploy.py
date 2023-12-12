from pytezos import pytezos
from getpass import getpass
from dotenv import load_dotenv
import os
from pytezos.client import PyTezosClient
from tests.helpers.contracts import (
    Ticketer,
    DepositProxy,
    ReleaseProxy,
    RollupMock,
    FA2,
    Router,
    ContractHelper,
)
from tests.helpers.utility import (
    pkh,
    pack,
    make_address_bytes,
)
from typing import Type, TypeVar, Any
from tests.helpers.tickets import (
    Ticket,
    create_ticket,
    make_ticket_payload_bytes,
)


load_dotenv()
RPC_SHELL = os.getenv('RPC_SHELL') or 'https://rpc.tzkt.io/nairobinet/'
ALICE_PRIVATE_KEY = os.getenv('ALICE_PRIVATE_KEY') or getpass('Enter Alice private key: ')
BORIS_PRIVATE_KEY = os.getenv('BORIS_PRIVATE_KEY') or getpass('Enter Boris private key: ')


ROLLUP_SR_ADDRESS = 'sr1SkqgA2kLyB5ZqQWU5vdyMoNvWjYqtXGYY'
ERC20_PROXY_ADDRESS = '39909EB8b35993013F3Be035BA22804E198F0BBb'
ALICE_L2_ADDRESS = 'bFc6dc08Bd0e8FBa3a25D7A70728E76E627c9A90'


CONTRACTS = {
    'fa2':              (FA2,                  'KT1CoUssNszEUPAwKnxDQVv6nNDf7n4ge8BK'),
    'deposit_proxy':    (DepositProxy,         'KT1JR55jcW9swYumGw8pnQkFVUXZdndqwgQG'),
    'release_proxy':    (ReleaseProxy,         'KT1Gu89N9b8V2Zs8HyYwhXWkikbe22JyZtAR'),
    'ticketer':         (Ticketer,             'KT1VdjDtgKMXpHwhVRCvqbsTBDmWLJt8sfUE'),
    'router':           (Router,               'KT1LX3p9yvBHxhbPeKbhVgTvbovmzT5PxwRj'),

    # Rollup Mock is not deployed by default anymore:
    # 'rollup_mock':      (RollupMock,           ''),
}


def deploy_contracts(
        manager: PyTezosClient,
        balances: dict[str, int],
        deploy_rollup_mock: bool = False,
    ) -> dict[str, ContractHelper]:

    contracts: dict[str, ContractHelper] = {}

    # Tokens deployment:
    print('Deploying FA2...')
    fa2_opg = FA2.originate(manager, balances).send()
    manager.wait(fa2_opg)
    fa2 = FA2.create_from_opg(manager, fa2_opg)

    # Contracts deployment:
    T = TypeVar('T', bound='ContractHelper')
    def deploy_contract(cls: Type[T]) -> T:
        print(f'Deploying {cls.__name__}...')
        opg = cls.originate_default(manager).send()
        manager.wait(opg)
        return cls.create_from_opg(manager, opg)

    deposit_proxy = deploy_contract(DepositProxy)
    release_proxy = deploy_contract(ReleaseProxy)
    router = deploy_contract(Router)

    contracts['fa2'] = fa2
    contracts['deposit_proxy'] = deposit_proxy
    contracts['release_proxy'] = release_proxy
    contracts['router'] = router
    if deploy_rollup_mock:
        contracts['rollup_mock'] = deploy_contract(RollupMock)

    # Deploying Ticketer with external metadata:
    fa2_key = ( "fa2", ( fa2.address, 0 ) )
    fa2_external_metadata = {
        'decimals': pack(0, 'nat'),
        'symbol': pack('TEST', 'string'),
    }

    opg = Ticketer.originate_with_external_metadata(
        manager,
        external_metadata={
            fa2_key: fa2_external_metadata
        },
    ).send()
    manager.wait(opg)
    ticketer = Ticketer.create_from_opg(manager, opg)
    contracts['ticketer'] = ticketer

    ticket = create_ticket(ticketer, fa2)
    ticket_payload = make_ticket_payload_bytes(ticket)
    ticketer_bytes = make_address_bytes(ticketer.address)
    router_bytes = make_address_bytes(router.address)
    print('Data for setup ERC20 Proxy:')
    print(f'ticket address bytes: `{ticketer_bytes}`')
    print(f'ticket payload bytes: `{ticket_payload}`')
    print(f'router address bytes: `{router_bytes}`')

    return contracts


def load_contracts(
        manager: PyTezosClient,
        contracts: dict[str, tuple[Type[ContractHelper], str]],
    ) -> dict[str, ContractHelper]:

    return {
        name: cls.create_from_address(manager, address)
        for name, (cls, address) in contracts.items()
    }


def deposit_to_l2(
        # TODO: is it possible to replace Any with correct types?
        contracts: dict[str, Any],
        client: PyTezosClient,
    ) -> None:
    """ This function wraps fa2 token to ticket and deposits it to rollup """

    # TODO: reuse some of this code in tests/test_communication.py
    fa2 = contracts['fa2']
    deposit_proxy = contracts['deposit_proxy']
    release_proxy = contracts['release_proxy']
    ticketer = contracts['ticketer']
    ticket = create_ticket(ticketer, fa2)

    # 1. In one bulk we allow ticketer to transfer tokens,
    # deposit tokens to the ticketer, set routing info to the proxy
    # and transfer ticket to the Rollup (Locker) by sending created ticket
    # to the proxy contract, which will send it to the Rollup with routing info:
    ticket_receiver = bytes.fromhex(ERC20_PROXY_ADDRESS)
    receiver = bytes.fromhex(ALICE_L2_ADDRESS)

    opg = client.bulk(
        fa2.using(client).allow(ticketer.address),
        ticketer.using(client).deposit(fa2, 50),
        deposit_proxy.using(client).set({
            # router_info is first 20 bytes is receiver (the one who get token),
            # then second 20 bytes is the proxy contract (the one who get ticket)
            'data': receiver + ticket_receiver,
            'receiver': ROLLUP_SR_ADDRESS,
        }),
        client.transfer_ticket(
            ticket_contents = ticket['content'],
            ticket_ty = ticket['content_type'],
            ticket_ticketer = ticket['ticketer'],
            ticket_amount = 50,
            destination = deposit_proxy.address,
            entrypoint = 'send',
        ),
    ).send()
    client.wait(opg)


def unpack_ticket(
        contracts: dict[str, Any],
        client: PyTezosClient,
        amount: int = 3,
    ) -> None:
    """ This function run ticket unpacking for given client """

    fa2 = contracts['fa2']
    release_proxy = contracts['release_proxy']
    ticketer = contracts['ticketer']
    ticket = create_ticket(ticketer, fa2)

    opg = client.bulk(
        release_proxy.using(client).set({
            'data': pkh(client),
            'receiver': f'{ticketer.address}%release',
        }),
        client.transfer_ticket(
            ticket_contents=ticket['content'],
            ticket_ty=ticket['content_type'],
            ticket_ticketer=ticket['ticketer'],
            ticket_amount=amount,
            destination=release_proxy.address,
            entrypoint='send',
        )
    ).send()
    client.wait(opg)


alice = pytezos.using(shell=RPC_SHELL, key=ALICE_PRIVATE_KEY)
boris = pytezos.using(shell=RPC_SHELL, key=BORIS_PRIVATE_KEY)


# If you use new accounts, you need to reveal them:
# alice.reveal().send()
# boris.reveal().send()


balances = {
    pkh(alice): 1_000,
    pkh(boris): 1_000,
}


def main() -> None:
    # contracts = deploy_contracts(alice, balances)
    contracts = load_contracts(alice, CONTRACTS)
    # deposit_to_l2(contracts, alice)
    unpack_ticket(contracts, boris)

if __name__ == '__main__':
    main()
