import click
from typing import Optional
from scripts.environment import load_or_ask
from scripts.helpers.utility import make_address_bytes
from scripts.helpers.etherlink import FaWithdrawalPrecompileHelper, load_contract_type
from scripts.environment import get_etherlink_web3, get_etherlink_account


@click.command()
@click.option(
    '--proxy-address',
    required=True,
    help='The address of the ERC20 proxy token contract which should burn token.',
)
@click.option(
    '--router-address',
    required=True,
    help='The address of the Router contract on the Tezos side (Ticketer address for FA2 and FA1.2 tokens).',
)
@click.option(
    '--amount', required=True, type=int, help='The amount of tokens to be withdrawn.'
)
# TODO: consider get ticketer address bytes and content from the router address provided (make optional?)
@click.option(
    '--ticketer-address-bytes',
    required=True,
    help='The address of the ticketer contract encoded in forged form: `| 0x01 | 20 bytes | 0x00 |`. Use `get_ticketer_params` function to get the correct value for a given ticket address.',
)
@click.option(
    '--ticket-content-bytes',
    required=True,
    help='The content of the ticket as micheline expression is in its forged form, **legacy optimized mode**. Use `get_ticket_params` function to get the correct value for a given ticket address.',
)
# TODO: consider making mandatory and rename to `--to`
@click.option(
    '--receiver-address',
    default=None,
    help='The address of the receiver of the tokens in Tezos.',
)
@click.option(
    '--withdraw-precompile',
    default=None,
    help='The address of the withdraw precompile contract.',
)
@click.option(
    '--private-key',
    default=None,
    help='Private key on the Etherlink side that should execute withdrawal.',
)
@click.option('--rpc-url', default=None, help='Etherlink RPC URL.')
def withdraw(
    proxy_address: str,
    router_address: str,
    amount: int,
    ticketer_address_bytes: str,
    ticket_content_bytes: str,
    receiver_address: Optional[str],
    withdraw_precompile: Optional[str],
    private_key: Optional[str],
    rpc_url: Optional[str],
) -> None:
    """Withdraws token from L2 to L1"""

    web3 = get_etherlink_web3(rpc_url)
    account = get_etherlink_account(web3, private_key)
    withdraw_precompile = withdraw_precompile or load_or_ask(
        'L2_WITHDRAW_PRECOMPILE_ADDRESS'
    )

    receiver_address = receiver_address or load_or_ask('L1_PUBLIC_KEY_HASH')
    receiver_address_bytes = make_address_bytes(receiver_address)
    router_address_bytes = make_address_bytes(router_address)
    routing_info_str = receiver_address_bytes + router_address_bytes
    routing_info = bytes.fromhex(routing_info_str)
    ticketer = bytes.fromhex(ticketer_address_bytes.replace('0x', ''))
    content = bytes.fromhex(ticket_content_bytes.replace('0x', ''))

    fa_withdrawal_precompile = FaWithdrawalPrecompileHelper.from_address(
        # TODO: consider adding FaWithdrawalPrecompile ABI to the repo
        contract_type=load_contract_type(web3, 'KernelMock'),
        web3=web3,
        account=account,
        # TODO: check: is it required `0x` to be added?
        address=withdraw_precompile,
    )

    receipt = fa_withdrawal_precompile.withdraw(
        ticket_owner=proxy_address,
        routing_info=routing_info,
        amount=amount,
        ticketer=ticketer,
        content=content,
    )

    tx_hash = receipt.transactionHash  # type: ignore
    print(f'Successfully called withdraw, tx hash: {tx_hash.hex()}')
