from pytezos import pytezos
from getpass import getpass
from dotenv import load_dotenv
import os
from pytezos.client import PyTezosClient
from tests.helpers.contracts import (
    Ticketer,
    ProxyRouter,
    ProxyTicketer,
    RollupMock,
    FA2,
    ContractHelper,
    Router,
    ProxyL2Burn,
)
from tests.helpers.utility import pkh, pack
from typing import Type, TypeVar, Any
from tests.helpers.routing_data import create_routing_data
from tests.helpers.tickets import create_ticket


load_dotenv()
RPC_SHELL = os.getenv('RPC_SHELL') or 'https://rpc.tzkt.io/nairobinet/'
ALICE_PRIVATE_KEY = os.getenv('ALICE_PRIVATE_KEY') or getpass('Enter Alice private key: ')
BORIS_PRIVATE_KEY = os.getenv('BORIS_PRIVATE_KEY') or getpass('Enter Boris private key: ')


def deploy_contracts(
        manager: PyTezosClient,
        balances: dict[str, int]
    ) -> dict[str, ContractHelper]:

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

    proxy_router = deploy_contract(ProxyRouter)
    proxy_ticketer = deploy_contract(ProxyTicketer)
    proxy_l2_burn = deploy_contract(ProxyL2Burn)
    rollup_mock = deploy_contract(RollupMock)
    router = deploy_contract(Router)

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

    return {
        'fa2': fa2,
        'proxy_router': proxy_router,
        'proxy_ticketer': proxy_ticketer,
        'proxy_l2_burn': proxy_l2_burn,
        'rollup_mock': rollup_mock,
        'router': router,
        'ticketer': ticketer,
    }


def load_contracts(
        manager: PyTezosClient,
        contracts: dict[str, tuple[Type[ContractHelper], str]],
    ) -> dict[str, ContractHelper]:

    return {
        name: cls.create_from_address(manager, address)
        for name, (cls, address) in contracts.items()
    }


CONTRACTS = {
    'fa2':            (FA2,           'KT1XTdYiaN1rHVJd5Tz9JUNF4UrKXggkaeN6'),
    'proxy_router':   (ProxyRouter,   'KT1Sak5wzi1unorD2x6Yx36QwDAjjq52LB1P'),
    'proxy_ticketer': (ProxyTicketer, 'KT1RTUDVanfWh2cxwbYWo2mjxFhbhQtumMaP'),
    'proxy_l2_burn':  (ProxyL2Burn,   'KT1F4LWzfz7N65a6QAzYLHcceD592r1bFWSx'),
    'rollup_mock':    (RollupMock,    'KT1AsGzrvDPnEeYKkX7avLmYZ8dXNzgaJSsJ'),
    'router':         (Router,        'KT1JK3qwyYak5PDgRvKiLUYLWzrdpcmJVdjs'),
    'ticketer':       (Ticketer,      'KT1Ms11t3ADzvW3gvx9K9p84a1ZtW4z9LbjL'),
}


def run_interactions(
        # TODO: is it possible to replace Any with correct types?
        contracts: dict[str, Any],
        alice: PyTezosClient,
        boris: PyTezosClient,
    ) -> None:
    """ This function runs interactions with contracts based on
        the scenario used in tests/test_communication.py """

    # TODO: reuse some of this code in tests/test_communication.py
    fa2 = contracts['fa2']
    proxy_router = contracts['proxy_router']
    proxy_ticketer = contracts['proxy_ticketer']
    proxy_l2_burn = contracts['proxy_l2_burn']
    rollup_mock = contracts['rollup_mock']
    router = contracts['router']
    ticketer = contracts['ticketer']

    l1_ticket = create_ticket(
        ticketer=ticketer.address,
        token_id=0,
        token_info={
            'contract_address': pack(fa2.address, 'address'),
            'token_id': pack(fa2.token_id, 'nat'),
            'token_type': pack('FA2', 'string'),
            'decimals': pack(12, 'nat'),
            'symbol': pack('TEST', 'string'),
        },
    )

    l2_ticket = create_ticket(
        ticketer=rollup_mock.address,
        token_id=0,
        token_info={
            'contract_address': pack(fa2.address, 'address'),
            'token_id': pack(fa2.token_id, 'nat'),
            'token_type': pack('FA2', 'string'),
            'decimals': pack(12, 'nat'),
            'symbol': pack('TEST', 'string'),
            'l1_ticketer': pack(ticketer.address, 'address'),
            'l1_token_id': pack(0, 'nat'),
        },
    )

    # 1. In one bulk we allow ticketer to transfer tokens,
    # deposit tokens to the ticketer, set routing info to the proxy
    # and transfer ticket to the Rollup (Locker) by sending created ticket
    # to the proxy contract, which will send it to the Rollup with routing info:
    opg = alice.bulk(
        fa2.using(alice).allow(ticketer.address),
        ticketer.using(alice).deposit(fa2, 100),
        proxy_router.using(alice).set({
            'data': create_routing_data(
                sender=pkh(alice),
                receiver=pkh(alice),
            ),
            'receiver': f'{rollup_mock.address}%l1_deposit',
        }),
        alice.transfer_ticket(
            ticket_contents = l1_ticket['content'],
            ticket_ty = l1_ticket['content_type'],
            ticket_ticketer = l1_ticket['ticketer'],
            ticket_amount = 25,
            destination = proxy_router.address,
            entrypoint = 'send',
        ),
    ).send()
    alice.wait(opg)

    # 2. Transfer some L2 tickets to Boris's address
    opg = alice.transfer_ticket(
        ticket_contents=l2_ticket['content'],
        ticket_ty=l2_ticket['content_type'],
        ticket_ticketer=l2_ticket['ticketer'],
        ticket_amount=10,
        destination=pkh(boris),
    ).send()
    alice.wait(opg)

    # 3. Boris burns some L2 tickets to get L1 tickets back using proxy:
    opg = boris.bulk(
        proxy_l2_burn.using(boris).set({
            'data': {
                'routing_data': create_routing_data(
                    sender=pkh(boris),
                    receiver=pkh(boris),
                ),
                'router': router.address,
            },
            'receiver': f'{rollup_mock.address}%l2_burn',
        }),
        boris.transfer_ticket(
            ticket_contents=l2_ticket['content'],
            ticket_ty=l2_ticket['content_type'],
            ticket_ticketer=l2_ticket['ticketer'],
            ticket_amount=5,
            destination=proxy_l2_burn.address,
            entrypoint='send',
        ),
    ).send()
    boris.wait(opg)

    # 4. Rollup releases L1 tickets:
    opg = rollup_mock.l1_release(0).send()
    boris.wait(opg)

    # 5. Boris unpacks L1 tickets to get FA2 tokens:
    opg = boris.bulk(
        proxy_ticketer.using(boris).set({
            'data': pkh(boris),
            'receiver': f'{ticketer.address}%release',
        }),
        boris.transfer_ticket(
            ticket_contents=l1_ticket['content'],
            ticket_ty=l1_ticket['content_type'],
            ticket_ticketer=l1_ticket['ticketer'],
            ticket_amount=2,
            destination=proxy_ticketer.address,
            entrypoint='send',
        )
    ).send()
    boris.wait(opg)


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
    run_interactions(contracts, alice, boris)

if __name__ == '__main__':
    main()
