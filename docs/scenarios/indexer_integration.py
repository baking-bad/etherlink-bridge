from dataclasses import dataclass
import time
import click
from gql import Client, gql

from eth_account.signers.local import LocalAccount
from graphql import DocumentNode
from pytezos.client import PyTezosClient
from pytezos.operation.group import OperationGroup
from scripts.helpers.addressable import get_address
from scripts.helpers.contracts.fast_withdrawal import FastWithdrawal
from scripts.etherlink import xtz_fast_withdraw
from scripts.defaults import (
    XTZ_WITHDRAWAL_PRECOMPILE,
    ETHERLINK_RPC_URL,
    SMART_ROLLUP_ADDRESS,
    TEZOS_PRIVATE_KEY,
    TEZOS_RPC_URL,
)
from pytezos import MichelsonType  # type: ignore
from scripts.helpers.contracts.fast_withdrawal import Withdrawal
from scripts.helpers.formatting import accent, error, wrap
from scripts.helpers.ticket_content import TicketContent
from scripts.helpers.timer import Timer
from scripts.tezos.execute_outbox_message import execute_outbox_message
from datetime import datetime


def random_pkh(client: PyTezosClient) -> str:
    return client.key.generate(export=False).public_key_hash()  # type: ignore


def decode_michelson_nat(byte_value: bytes) -> int:
    nat_type = MichelsonType.match({'prim': 'nat'})
    decoded_pytezos_value = nat_type.unpack(byte_value)
    return int(decoded_pytezos_value)  # type: ignore


def timestamp_to_int(timestamp: str) -> int:
    dt_object = datetime.fromisoformat(timestamp)
    unix_timestamp_float = dt_object.timestamp()
    assert dt_object.microsecond == 0
    return int(unix_timestamp_float)


def create_withdrawal_from_l2_transaction(l2_transaction: dict) -> Withdrawal:
    return Withdrawal(
        withdrawal_id=l2_transaction['kernel_withdrawal_id'],
        full_amount=int(l2_transaction['amount']) // 10**12,
        ticketer=l2_transaction['ticket']['ticketer_address'],
        content=TicketContent(
            token_id=int(l2_transaction['ticket']['ticket_id']),
            token_info=l2_transaction['ticket']['metadata'],
        ),
        timestamp=timestamp_to_int(l2_transaction['timestamp']),
        base_withdrawer=l2_transaction['l1_account'],
        payload=bytes.fromhex(l2_transaction['fast_payload'][2:]),
        l2_caller=l2_transaction['l2_account'],
    )


@dataclass
class IndexerTestEnvironment:
    indexer: Client
    fast_withdrawal: FastWithdrawal
    l2_caller: LocalAccount
    provider: PyTezosClient
    withdrawer_pkh: str
    discount_rate: float

    def make_xtz_withdrawal(self, amount: int) -> str:
        full_amount = amount
        full_amount_wei = full_amount * 10**12
        discounted_amount = int(full_amount * self.discount_rate)

        tx_hash: str = xtz_fast_withdraw.callback(
            target=self.withdrawer_pkh,
            fast_withdrawal_contract=self.fast_withdrawal.address,
            amount=full_amount_wei,
            discounted_amount=discounted_amount,
            withdraw_precompile=XTZ_WITHDRAWAL_PRECOMPILE,
            etherlink_private_key=self.l2_caller.key,
            etherlink_rpc_url=ETHERLINK_RPC_URL,
        )  # type: ignore
        return tx_hash.split('0x')[1]

    def make_payout_withdrawal(self, withdrawal: Withdrawal) -> OperationGroup:

        xtz_amount = decode_michelson_nat(withdrawal.payload)

        return self.fast_withdrawal.payout_withdrawal(
            withdrawal=withdrawal,
            service_provider=get_address(self.provider),
            xtz_amount=xtz_amount,
        ).send()

    def make_withdrawal_settlement(self, outbox_message: dict) -> OperationGroup:
        opg: OperationGroup = execute_outbox_message.callback(
            commitment=outbox_message['commitment']['hash'],
            proof=outbox_message['proof'],
            smart_rollup_address=SMART_ROLLUP_ADDRESS,
            tezos_private_key=TEZOS_PRIVATE_KEY,
            tezos_rpc_url=TEZOS_RPC_URL,
        )  # type: ignore
        return opg


def fast_withdrawal_bridge_operation_query() -> DocumentNode:
    return gql(
        '''
        query QueryWithdrawalByHash(
                $l2_hash: String,
                $kind: String,
                $status: String
            ) {
                bridge_operation(
                where: {
                    withdrawal: {
                        l2_transaction: {transaction_hash: {_eq: $l2_hash}}},
                        kind: {_eq: $kind},
                        status: {_eq: $status}
                }
            ) {
                status
                kind
                is_completed
                is_successful
                l1_account
                l2_account
                withdrawal {
                    l2_transaction {
                        transaction_hash
                        amount
                        kernel_withdrawal_id
                        l1_account
                        l2_account
                        timestamp
                        fast_payload
                        ticket {
                            ticketer_address
                            metadata
                            ticket_id
                        }
                    }
                    outbox_message {
                        builder
                        proof
                        commitment {
                            hash
                        }
                    }
                    l1_transaction {
                        amount
                        sender
                    }
                }
            }
        }
        '''
    )


async def request_bridge_operation_with_high_verbosity(
    test_env: IndexerTestEnvironment,
    l2_hash: str,
    kind: str,
    status: str,
    max_attempts: int = 1000,
    start_sleep: float = 1.0,
    sleep_multiplier: float = 1.4,
) -> dict:
    timer = Timer()
    click.echo('Requesting bridge operation:')
    click.echo('- l2_hash: ' + wrap(accent(l2_hash)))
    click.echo('- kind: ' + wrap(accent(kind)))
    click.echo('- status: ' + wrap(accent(status)))
    click.echo('- attempts: ', nl=False)
    sleep_time = start_sleep

    for _ in range(max_attempts):
        indexer_response = await test_env.indexer.execute_async(
            fast_withdrawal_bridge_operation_query(),
            dict(l2_hash=l2_hash, kind=kind, status=status),
        )
        total_elapsed_seconds = timer.elapsed()
        if total_elapsed_seconds < 60.0:
            click.echo('x', nl=False)
        else:
            click.echo(error('x'), nl=False)

        bridge_operations = indexer_response['bridge_operation']
        if len(bridge_operations) > 0:
            assert len(indexer_response['bridge_operation']) == 1
            bridge_operation: dict = indexer_response['bridge_operation'][0]
            withdrawal = bridge_operation['withdrawal']['l2_transaction']
            withdrawal_id = withdrawal['kernel_withdrawal_id']
            click.echo('')
            click.echo('Found withdrawal, id: ' + wrap(accent(withdrawal_id)))
            click.echo(
                'Elapsed time (seconds): '
                + wrap(accent(f'{total_elapsed_seconds:.1f}'))
            )
            return bridge_operation
        time.sleep(sleep_time)
        sleep_time *= sleep_multiplier

    raise Exception('Max attempts, no bridge operations found')
