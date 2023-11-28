from pytezos import pytezos
from getpass import getpass
from dotenv import load_dotenv
import os
from pytezos.client import PyTezosClient
from tests.helpers.contracts import (
    Ticketer,
    ProxyRouterDeposit,
    ProxyTicketer,
    RollupMock,
    FA2,
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


ROLLUP_SR_ADDRESS = 'sr1JDmHhBg8yKzkUWpVqL9n8brCqhxdBTtq4'
ERC20_WRAPPER_ADDRESS = '6686644C9D285b3EBd5D880bb2650B1EF33699e6'
ALICE_L2_ADDRESS = '31E0aC684f33D86C10FdC10482cBAC073B750264'


CONTRACTS = {
    'fa2':              (FA2,                  'KT1GZiNJSELE2Ad5JcfT6sN38ABeKHvkPLMx'),
    'proxy_deposit':    (ProxyRouterDeposit,   'KT1NB4C5m7vnEq47EgN5QexXX6d4RCeHQKwL'),
    'proxy_ticketer':   (ProxyTicketer,        'KT1X9T9VWMsEHghd6nsVcjFfeFcNHYY2JJ84'),
    'ticketer':         (Ticketer,             'KT1DeNCweBiRRpgBwQatZmaSqB2nJ65HVhJ6'),

    # Rollup Mock is not deployed by default anymore:
    # 'rollup_mock':      (RollupMock,           ''),
}


def create_ticket_from_fa2(ticketer: Ticketer, fa2: FA2) -> Ticket:
    # TODO: this ticket has hardcoded metadata, it would be better to
    # create it from ticketer and FA2 contract metadata:
    return create_ticket(
        ticketer=ticketer.address,
        token_id=0,
        token_info={
            'contract_address': pack(fa2.address, 'address'),
            'token_id': pack(fa2.token_id, 'nat'),
            'token_type': pack('FA2', 'string'),
            'decimals': pack(0, 'nat'),
            'symbol': pack('TEST', 'string'),
        },
    )


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

    proxy_deposit = deploy_contract(ProxyRouterDeposit)
    proxy_ticketer = deploy_contract(ProxyTicketer)

    contracts['fa2'] = fa2
    contracts['proxy_deposit'] = proxy_deposit
    contracts['proxy_ticketer'] = proxy_ticketer
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

    ticket = create_ticket_from_fa2(ticketer, fa2)
    ticket_payload = make_ticket_payload_bytes(ticket)
    ticketer_bytes = make_address_bytes(ticketer.address)
    print('Data for setup ERC20 Wrapper:')
    print(f'ticket address bytes: `{ticketer_bytes}`')
    print(f'ticket payload bytes: `{ticket_payload}`')

    return contracts


def load_contracts(
        manager: PyTezosClient,
        contracts: dict[str, tuple[Type[ContractHelper], str]],
    ) -> dict[str, ContractHelper]:

    return {
        name: cls.create_from_address(manager, address)
        for name, (cls, address) in contracts.items()
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
    proxy_deposit = contracts['proxy_deposit']
    proxy_ticketer = contracts['proxy_ticketer']
    ticketer = contracts['ticketer']
    ticket = create_ticket_from_fa2(ticketer, fa2)

    # 1. In one bulk we allow ticketer to transfer tokens,
    # deposit tokens to the ticketer, set routing info to the proxy
    # and transfer ticket to the Rollup (Locker) by sending created ticket
    # to the proxy contract, which will send it to the Rollup with routing info:
    wrapper = bytes.fromhex(ERC20_WRAPPER_ADDRESS)
    receiver = bytes.fromhex(ALICE_L2_ADDRESS)

    opg = alice.bulk(
        fa2.using(alice).allow(ticketer.address),
        ticketer.using(alice).deposit(fa2, 100),
        proxy_deposit.using(alice).set({
            # router_info is first 20 bytes is wrapper, second is 20b receiver
            'data': wrapper + receiver,
            'receiver': ROLLUP_SR_ADDRESS,
        }),
        alice.transfer_ticket(
            ticket_contents = ticket['content'],
            ticket_ty = ticket['content_type'],
            ticket_ticketer = ticket['ticketer'],
            ticket_amount = 5,
            destination = proxy_deposit.address,
            entrypoint = 'send',
        ),
    ).send()
    alice.wait(opg)

    # TODO: remove this L2 logic:
    '''
    l2_ticket = create_ticket(
        ticketer=rollup_mock.address,
        token_id=0,
        token_info={
            'contract_address': pack(fa2.address, 'address'),
            'token_id': pack(fa2.token_id, 'nat'),
            'token_type': pack('FA2', 'string'),
            'decimals': pack(0, 'nat'),
            'symbol': pack('TEST', 'string'),
            'l1_ticketer': pack(ticketer.address, 'address'),
            'l1_token_id': pack(0, 'nat'),
        },
    )

    # 2. Transfer some L2 tickets to Boris's address
    opg = alice.transfer_ticket(
        ticket_contents=l2_ticket['content'],
        ticket_ty=l2_ticket['content_type'],
        ticket_ticketer=l2_ticket['ticketer'],
        ticket_amount=10,
        destination=pkh(boris),
    ).send()
    alice.wait(opg)

    # 3. Boris creates outbox message bridging some L2 tokens to L1:
    opg = rollup_mock.using(boris).create_outbox_message({
        'ticket_id': 0,
        'amount': 5,
        'routing_data': pack(pkh(boris), 'address'),
    }).send()
    boris.wait(opg)

    # 4. Rollup releases L1 tickets:
    opg = rollup_mock.execute_outbox_message(0).send()
    boris.wait(opg)
    '''

    # TODO: move this logic to separate interaction function:
    '''
    # 5. Alice unpacks tickets to get FA2 tokens:
    opg = alice.bulk(
        proxy_ticketer.using(alice).set({
            'data': pkh(alice),
            'receiver': f'{ticketer.address}%release',
        }),
        alice.transfer_ticket(
            ticket_contents=ticket['content'],
            ticket_ty=ticket['content_type'],
            ticket_ticketer=ticket['ticketer'],
            ticket_amount=2,
            destination=proxy_ticketer.address,
            entrypoint='send',
        )
    ).send()
    alice.wait(opg)
    '''


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
