import click
from eth_account.signers.local import LocalAccount
from web3 import Web3
from pytezos.client import PyTezosClient

from scripts.helpers.utility import (
    get_tezos_client,
    make_address_bytes,
    get_etherlink_account,
    get_etherlink_web3,
)

from scripts.helpers.contracts.token_bridge_helper import TokenBridgeHelper
from scripts.helpers.contracts.tokens.token import TokenHelper
from scripts.helpers.contracts.ticketer import Ticketer
from scripts.helpers.addressable import (
    get_address,
    Addressable,
    EtherlinkAddressable,
    get_etherlink_address,
    make_deposit_routing_info,
    make_withdrawal_routing_info,
)
from scripts.helpers.scenarios import (
    transfer_ticket,
    wrap_tokens_to_tickets,
    setup_ticket_router_tester_to_rollup_deposit,
    etherlink_legacy_transfer,
)
from scripts.helpers.formatting import (
    accent,
    echo_variable,
    wrap,
)
from scripts.tezos import xtz_deposit
from getpass import getpass
from scripts.defaults import (
    SMART_ROLLUP_ADDRESS,
    XTZ_TICKET_HELPER,
    TEZOS_PRIVATE_KEY,
    TEZOS_RPC_URL,
    ETHERLINK_RPC_URL,
    ETHERLINK_PRIVATE_KEY,
    KERNEL_ADDRESS,
    FA_WITHDRAWAL_PRECOMPILE,
    XTZ_WITHDRAWAL_PRECOMPILE,
    ETHERLINK_ROLLUP_NODE_URL,
    PRINT_DEBUG_LOG,
    XTZ_TICKETER_ADDRESS,
)


if PRINT_DEBUG_LOG:
    import logging

    logging.basicConfig(level=logging.DEBUG)


def setup() -> tuple[Web3, LocalAccount, PyTezosClient]:
    web3 = get_etherlink_web3(ETHERLINK_RPC_URL)
    etherlink_account = get_etherlink_account(web3, ETHERLINK_PRIVATE_KEY)
    tezos_account = get_tezos_client(TEZOS_RPC_URL, TEZOS_PRIVATE_KEY)

    wa_tezos_address = wrap(accent(tezos_account.key.public_key_hash()))
    wa_tezos_balance = wrap(accent(f'{tezos_account.balance():.6f} ꜩ'))
    wa_etherlink_address = wrap(accent(etherlink_account.address))
    balance_wei = web3.eth.get_balance(etherlink_account.address)
    wa_etherlink_balance = wrap(accent(f'{web3.from_wei(balance_wei, "ether")} ꜩ'))

    click.echo('Setup:')
    click.echo(
        '- Tezos account: ' + wa_tezos_address + ', balance: ' + wa_tezos_balance
    )
    click.echo(
        '- Etherlink account: '
        + wa_etherlink_address
        + ', balance: '
        + wa_etherlink_balance
    )

    return web3, etherlink_account, tezos_account
