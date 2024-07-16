from random import randint
from time import sleep

import pytest
from gql import gql
from gql.client import SyncClientSession
from graphql import DocumentNode
from pytezos import pytezos

from scripts.helpers.contracts import ContractHelper
from scripts.helpers.contracts import TokenBridgeHelper
from scripts.helpers.contracts import TicketRouterTester
from scripts.helpers.contracts import Ticketer
from scripts.tests.dto import Bridge
from scripts.tests.dto import Native
from scripts.tests.dto import Token
from scripts.tests.dto import Wallet
from scripts.tezos import deposit


class TestDeposit:
    @pytest.fixture
    def bridge_deposit_query(self) -> DocumentNode:
        return gql(
            '''
            query BridgeDepositQuery($operation_hash: String) {
                bridge_deposit(
                    order_by: {created_at: desc},
                    where: {
                        l1_transaction: {
                            operation_hash: {_eq: $operation_hash}
                        }
                    }
                ) {
                    l1_transaction {
                        operation_hash, l1_account, l2_account, ticket_hash, amount, ticket {token_id}
                    }
                    l2_transaction {
                        l2_account, ticket_hash, amount, l2_token {id}
                    }
                }
            }
            '''
        )

    @pytest.fixture
    def batch_operations_matching_order_query(self) -> DocumentNode:
        return gql(
            '''
            query BatchOperationsMatchingOrderQuery($operation_hash: String) {
                bridge_deposit(
                    order_by: {l1_transaction: {inbox_message_id: asc}},
                    where: {l1_transaction: {operation_hash: {_eq: $operation_hash}}}
                ) {
                    l1_transaction {
                        counter
                        nonce
                        inbox_message_id
                    }
                    l2_transaction {
                        log_index
                        transaction_index
                        inbox_message_id
                    }
                }
            }
            '''
        )

    @pytest.fixture
    def bridge_operation_query(self) -> DocumentNode:
        return gql(
            '''
            query BridgeOperationQuery($operation_hash: String) {
                bridge_operation(
                    order_by: {created_at: desc},
                    where: {
                        deposit: {l1_transaction: {operation_hash: {_eq: $operation_hash}}}
                    }) {
                    deposit {
                        l1_transaction {
                            l1_account, l2_account, amount, ticket {token_id}
                        }
                    }, is_completed, is_successful, status
                }
            }
            '''
        )

    def test_single_token_deposit(
        self,
        bridge: Bridge,
        wallet: Wallet,
        token: Token,
        indexer: SyncClientSession,
        bridge_deposit_query: gql,
    ):
        amount = randint(10, 20)

        operation_hash = deposit.callback(
            token_bridge_helper_address=token.l1_ticket_helper_address,
            amount=amount,
            receiver_address=wallet.l2_public_key,
            smart_rollup_address=bridge.l1_smart_rollup_address,
            tezos_private_key=wallet.l1_private_key,
            tezos_rpc_url=bridge.l1_rpc_url,
        )

        assert operation_hash[0] == 'o'
        assert len(operation_hash) == 51

        query_params = {'operation_hash': operation_hash}

        indexed_operations = []
        for _ in range(20):
            response = indexer.execute(bridge_deposit_query, variable_values=query_params)
            indexed_operations = response['bridge_deposit']
            if len(indexed_operations) and indexed_operations[-1]['l2_transaction'] is not None:
                break
            sleep(3)

        assert indexed_operations == [{
            'l1_transaction': {
                'operation_hash': operation_hash,
                'l1_account': wallet.l1_public_key_hash,
                'l2_account': wallet.l2_public_key.removeprefix('0x').lower(),
                'ticket_hash': str(token.ticket_hash),
                'amount': str(amount),
                'ticket': {
                    'token_id': token.l1_asset_id
                }
            },
            'l2_transaction': {
                'l2_account': wallet.l2_public_key.removeprefix('0x').lower(),
                'ticket_hash': str(token.ticket_hash),
                'amount': str(amount),
                'l2_token': {'id': token.l2_token_address.lower()}
            }
        }]

    def test_batch_token_deposit(
        self,
        bridge: Bridge,
        wallet: Wallet,
        token: Token,
        indexer: SyncClientSession,
        bridge_deposit_query: gql,
        batch_operations_matching_order_query: gql,
    ):
        batch_count = randint(3, 5)
        amount = randint(3, 20)

        manager = pytezos.using(shell=bridge.l1_rpc_url, key=wallet.l1_private_key)
        ticket_helper = TokenBridgeHelper.from_address(manager, token.l1_ticket_helper_address)
        token_helper = ticket_helper.get_ticketer().get_token()

        operations_group = (
           token_helper.disallow(manager, ticket_helper),
           token_helper.allow(manager, ticket_helper),
           ticket_helper.deposit(
               rollup=bridge.l1_smart_rollup_address,
               receiver=bytes.fromhex(wallet.l2_public_key.removeprefix('0x').lower()),
               amount=amount,
           ),
        ) * batch_count

        opg = manager.bulk(*operations_group).send()
        manager.wait(opg)
        operation_hash = opg.hash()

        assert operation_hash[0] == 'o'
        assert len(operation_hash) == 51

        query_params = {'operation_hash': operation_hash}

        indexed_operations = []
        for _ in range(20):
            response = indexer.execute(bridge_deposit_query, variable_values=query_params)
            indexed_operations = response['bridge_deposit']
            if len(indexed_operations) and indexed_operations[-1]['l2_transaction'] is not None:
                break
            sleep(3)

        assert len(indexed_operations) == batch_count
        for _ in range(batch_count):
            assert indexed_operations[_] == {
                'l1_transaction': {
                    'operation_hash': operation_hash,
                    'l1_account': wallet.l1_public_key_hash,
                    'l2_account': wallet.l2_public_key.removeprefix('0x').lower(),
                    'ticket_hash': str(token.ticket_hash),
                    'amount': str(amount),
                    'ticket': {
                        'token_id': token.l1_asset_id
                    }
                },
                'l2_transaction': {
                    'l2_account': wallet.l2_public_key.removeprefix('0x').lower(),
                    'ticket_hash': str(token.ticket_hash),
                    'amount': str(amount),
                    'l2_token': {'id': token.l2_token_address.lower()}
                }
            }

        matched_operations = []
        for _ in range(20):
            response = indexer.execute(batch_operations_matching_order_query, variable_values=query_params)
            matched_operations = response['bridge_deposit']
            if len(matched_operations):
                break
            sleep(3)

        assert len(matched_operations) == batch_count
        for i in range(1, batch_count):
            matched = matched_operations[i]
            previous_matched = matched_operations[i-1]
            assert matched['l1_transaction']['inbox_message_id'] == matched['l2_transaction']['inbox_message_id']
            assert matched['l1_transaction']['inbox_message_id'] > previous_matched['l1_transaction']['inbox_message_id']
            assert matched['l1_transaction']['counter'] > previous_matched['l1_transaction']['counter']
            assert matched['l1_transaction']['nonce'] > previous_matched['l1_transaction']['nonce']
            # assert matched['l2_transaction']['log_index'] > previous_matched['l2_transaction']['log_index']
            # assert matched['l2_transaction']['transaction_index'] > previous_matched['l2_transaction']['transaction_index']

    @pytest.mark.parametrize(
        ('routing_info_proxy', 'expected_is_completed_flag', 'expected_status'),
        [
            # valid proxy address, contract does not exist
            ('0202020202020202020202020202020202020202', True, 'FAILED_INVALID_ROUTING_INFO_REVERTABLE'),
            # valid proxy address, contract exists, implements deposit proxy interface, not linked with the original token
            ('2c9f6e7bec5b8cf2fdd931462e24630fb2ce2f83', False, 'CREATED'),
            # # no proxy address
            ('', True),
            # # invalid proxy address, too long (23 bytes)
            # ('2323232323232323232323232323232323232323232323', False),
            # # invalid proxy address, too short (18 bytes)
            # ('181818181818181818181818181818181818', False),
        ]
    )
    def test_deposit_with_invalid_routing_info(
        self,
        bridge: Bridge,
        wallet: Wallet,
        token: Token,
        ticket_router_tester_address: str,
        routing_info_proxy: str,
        indexer: SyncClientSession,
        bridge_operation_query: gql,
        expected_status: str,
        expected_is_completed_flag: bool,
    ):
        amount = randint(3, 20)

        manager = pytezos.using(shell=bridge.l1_rpc_url, key=wallet.l1_private_key)
        tester = TicketRouterTester.from_address(manager, ticket_router_tester_address)
        ticketer = Ticketer.from_address(manager, token.l1_ticketer_address)

        token_helper = ticketer.get_token()

        ticket = ticketer.read_ticket(manager)
        initial_ticket_supply = ticket.amount

        operations_group = (
            token_helper.disallow(manager, ticketer.address),
            token_helper.allow(manager, ticketer.address),
            ticketer.deposit(amount),
        )
        opg = manager.bulk(*operations_group).send()
        manager.wait(opg)

        ticket = ticketer.read_ticket(manager)
        manager_ticket_balance_update = ticket.amount - initial_ticket_supply

        assert manager_ticket_balance_update == amount

        operations_group = (
            tester.set_rollup_deposit(
                target=f'{bridge.l1_smart_rollup_address}',
                routing_info=bytes.fromhex(wallet.l2_public_key.removeprefix('0x').lower() + routing_info_proxy),
            ),
            ticket.transfer(tester),
        )
        opg = manager.bulk(*operations_group).send()
        manager.wait(opg)
        operation_hash = opg.hash()

        assert operation_hash[0] == 'o'
        assert len(operation_hash) == 51

        query_params = {'operation_hash': operation_hash}

        indexed_operations = []
        for _ in range(20):
            response = indexer.execute(bridge_operation_query, variable_values=query_params)
            indexed_operations = response['bridge_operation']
            try:
                if len(indexed_operations) == 0:
                    raise ValueError
                if expected_is_completed_flag and indexed_operations[0]['status'] == 'CREATED':
                    raise ValueError
            except ValueError:
                sleep(3)
                continue
            else:
                assert len(indexed_operations) == 1
                break

        indexed_operation = indexed_operations[0]
        assert indexed_operation['deposit']['l1_transaction'] == {
            'l1_account': wallet.l1_public_key_hash,
            'l2_account': wallet.l2_public_key.removeprefix('0x').lower(),
            'amount': str(amount),
            'ticket': {
                'token_id': token.l1_asset_id,
            }
        }
        assert indexed_operation['is_completed'] == expected_is_completed_flag
        assert indexed_operation['status'] == expected_status
        assert indexed_operation['is_successful'] is False

    def test_successful_deposit_with_ticket_router_tester(
        self,
        bridge: Bridge,
        wallet: Wallet,
        token: Token,
        ticket_router_tester_address: str,
        indexer: SyncClientSession,
        bridge_operation_query: gql,
    ):
        amount = randint(3, 20)

        manager = pytezos.using(shell=bridge.l1_rpc_url, key=wallet.l1_private_key)
        tester = TicketRouterTester.from_address(manager, ticket_router_tester_address)
        ticketer = Ticketer.from_address(manager, token.l1_ticketer_address)

        token_helper = ticketer.get_token()

        ticket = ticketer.read_ticket(manager)
        initial_ticket_supply = ticket.amount

        operations_group = (
            token_helper.disallow(manager, ticketer.address),
            token_helper.allow(manager, ticketer.address),
            ticketer.deposit(amount),
        )
        opg = manager.bulk(*operations_group).send()
        manager.wait(opg)

        ticket = ticketer.read_ticket(manager)
        manager_ticket_balance_update = ticket.amount - initial_ticket_supply

        assert manager_ticket_balance_update == amount

        operations_group = (
            tester.set_rollup_deposit(
                target=f'{bridge.l1_smart_rollup_address}',
                routing_info=bytes.fromhex(wallet.l2_public_key.removeprefix('0x').lower() + token.l2_token_address.lower()),
            ),
            ticket.transfer(tester),
        )
        opg = manager.bulk(*operations_group).send()
        manager.wait(opg)
        operation_hash = opg.hash()

        assert operation_hash[0] == 'o'
        assert len(operation_hash) == 51

        query_params = {'operation_hash': operation_hash}

        indexed_operations = []
        for _ in range(20):
            response = indexer.execute(bridge_operation_query, variable_values=query_params)
            indexed_operations = response['bridge_operation']
            if len(indexed_operations):
                assert len(indexed_operations) == 1
                break
            sleep(3)

        indexed_operation = indexed_operations[0]
        assert indexed_operation['deposit']['l1_transaction'] == {
            'l1_account': wallet.l1_public_key_hash,
            'l2_account': wallet.l2_public_key.removeprefix('0x').lower(),
            'amount': str(amount),
            'ticket': {
                'token_id': token.l1_asset_id,
            }
        }
        assert indexed_operation['is_completed'] is True
        assert indexed_operation['is_successful'] is True

    def test_single_xtz_deposit(
        self,
        bridge: Bridge,
        wallet: Wallet,
        native_asset: Native,
        ticket_router_tester_address: str,
        indexer: SyncClientSession,
        bridge_deposit_query: gql,
    ):
        amount = randint(1, 5_000_000)

        manager = pytezos.using(shell=bridge.l1_rpc_url, key=wallet.l1_private_key)

        native_asset_helper = ContractHelper.from_address(manager, native_asset.l1_ticket_helper_address)

        opg = manager.bulk(
            native_asset_helper.contract.deposit(
                bridge.l1_smart_rollup_address, bytes.fromhex(wallet.l2_public_key.removeprefix('0x'))
            ).with_amount(amount)
        ).send()
        manager.wait(opg)
        operation_hash = opg.hash()

        assert operation_hash[0] == 'o'
        assert len(operation_hash) == 51

        query_params = {'operation_hash': operation_hash}

        indexed_operations = []
        for _ in range(20):
            response = indexer.execute(bridge_deposit_query, variable_values=query_params)
            indexed_operations = response['bridge_deposit']
            if len(indexed_operations):
                break
            sleep(3)

        assert indexed_operations == [{
            'l1_transaction': {
                'operation_hash': operation_hash,
                'l1_account': wallet.l1_public_key_hash,
                'l2_account': wallet.l2_public_key.removeprefix('0x').lower(),
                'ticket_hash': str(native_asset.ticket_hash),
                'amount': str(amount),
                'ticket': {
                    'token_id': native_asset.l1_asset_id
                }
            },
            'l2_transaction': {
                'l2_account': wallet.l2_public_key.removeprefix('0x').lower(),
                'ticket_hash': str(native_asset.ticket_hash),
                'amount': str(amount)+'0'*12,
                'l2_token': {'id': native_asset.l2_token_address}
            }
        }]

    def test_batch_xtz_deposit(
        self,
        bridge: Bridge,
        wallet: Wallet,
        native_asset: Native,
        ticket_router_tester_address: str,
        indexer: SyncClientSession,
        bridge_deposit_query: gql,
        batch_operations_matching_order_query: gql,
    ):
        batch_count = randint(3, 5)

        amount = randint(1, 5_000_000)

        manager = pytezos.using(shell=bridge.l1_rpc_url, key=wallet.l1_private_key)

        native_asset_helper = ContractHelper.from_address(manager, native_asset.l1_ticket_helper_address)

        operations_group = (
            native_asset_helper.contract.deposit(
                bridge.l1_smart_rollup_address, bytes.fromhex(wallet.l2_public_key.removeprefix('0x'))
            ).with_amount(amount),
        ) * batch_count
        opg = manager.bulk(*operations_group).send()
        manager.wait(opg)
        operation_hash = opg.hash()

        assert operation_hash[0] == 'o'
        assert len(operation_hash) == 51

        query_params = {'operation_hash': operation_hash}

        indexed_operations = []
        for _ in range(20):
            response = indexer.execute(bridge_deposit_query, variable_values=query_params)
            indexed_operations = response['bridge_deposit']
            if len(indexed_operations):
                break
            sleep(3)

        assert len(indexed_operations) == batch_count
        for _ in range(batch_count):
            assert indexed_operations[_] == {
                'l1_transaction': {
                    'operation_hash': operation_hash,
                    'l1_account': wallet.l1_public_key_hash,
                    'l2_account': wallet.l2_public_key.removeprefix('0x').lower(),
                    'ticket_hash': str(native_asset.ticket_hash),
                    'amount': str(amount),
                    'ticket': {
                        'token_id': native_asset.l1_asset_id
                    }
                },
                'l2_transaction': {
                    'l2_account': wallet.l2_public_key.removeprefix('0x').lower(),
                    'ticket_hash': str(native_asset.ticket_hash),
                    'amount': str(amount)+'0'*12,
                    'l2_token': {'id': native_asset.l2_token_address}
                }
            }

        matched_operations = []
        for _ in range(20):
            response = indexer.execute(batch_operations_matching_order_query, variable_values=query_params)
            matched_operations = response['bridge_deposit']
            if len(matched_operations):
                break
            sleep(3)

        assert len(matched_operations) == batch_count
        for i in range(1, batch_count):
            matched = matched_operations[i]
            previous_matched = matched_operations[i-1]
            assert matched['l1_transaction']['inbox_message_id'] == matched['l2_transaction']['inbox_message_id']
            assert matched['l1_transaction']['inbox_message_id'] > previous_matched['l1_transaction']['inbox_message_id']
            assert matched['l1_transaction']['counter'] > previous_matched['l1_transaction']['counter']
            assert matched['l1_transaction']['nonce'] > previous_matched['l1_transaction']['nonce']
            assert matched['l2_transaction']['log_index'] == previous_matched['l2_transaction']['log_index']
            assert matched['l2_transaction']['transaction_index'] > previous_matched['l2_transaction']['transaction_index']
