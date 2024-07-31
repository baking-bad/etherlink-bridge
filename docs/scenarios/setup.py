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
from scripts.helpers.contracts import (
    TokenBridgeHelper,
    TokenHelper,
    Ticketer,
    TicketRouterTester,
)
from scripts.helpers.etherlink import (
    Erc20ProxyHelper,
    BulkWithdrawalHelper,
    DepositTesterHelper,
    TokenProxyTesterHelper,
    make_filename,
)
from scripts.helpers.addressable import (
    get_address,
    Addressable,
    EtherlinkAddressable,
    get_etherlink_address,
    make_deposit_routing_info,
    make_withdrawal_routing_info,
    tezos_address_to_bytes,
)
from scripts.helpers.scenarios import (
    transfer_ticket,
    wrap_tokens_to_tickets,
    setup_ticket_router_tester_to_rollup_deposit,
    etherlink_legacy_transfer,
    deploy_ticket_router_tester,
)
from scripts.bridge_token import bridge_token
from scripts.helpers.rollup_node import get_tickets_count
from scripts.helpers.formatting import (
    accent,
    echo_variable,
    wrap,
)
from scripts.tezos import (
    xtz_deposit,
    deploy_token,
    deposit,
)
from scripts.etherlink import (
    withdraw,
    xtz_withdraw,
)
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
    TEZOS_TOKEN_ADDRESS,
    TEZOS_TOKEN_TYPE,
    TICKETER_ADDRESS,
    ERC20_PROXY_ADDRESS,
    TOKEN_BRIDGE_HELPER_ADDRESS,
    TICKET_ROUTER_TESTER_ADDRESS,
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


def load_contracts(
    web3: Web3,
    etherlink_account: LocalAccount,
    tezos_account: PyTezosClient,
) -> tuple[TokenHelper, Ticketer, Erc20ProxyHelper, TokenBridgeHelper, TicketRouterTester]:
    # TODO: echo that going to load token from address
    token = TokenHelper.get_cls(TEZOS_TOKEN_TYPE).from_address(
        tezos_account, TEZOS_TOKEN_ADDRESS
    )
    # TODO: echo tokens count on tezos_account address
    # TODO: echo going to load ticketer from address
    ticketer = Ticketer.from_address(tezos_account, TICKETER_ADDRESS)
    # TODO: echo tickets balance on the tezos_account
    # TODO: check ticketer connected to the loaded token, if not show warning
    # TODO: echo going to load ERC20 from address
    erc20 = Erc20ProxyHelper.from_address(web3, etherlink_account, ERC20_PROXY_ADDRESS)
    # TODO: echo ERC20 token balance on etherlink_account
    # TODO: echo going to load token_bridge_helper
    # TODO: echo ERC20 ticketHash
    token_bridge_helper = TokenBridgeHelper.from_address(
        tezos_account, TOKEN_BRIDGE_HELPER_ADDRESS
    )
    # TODO: check token_bridge_helper connected to the loaded L1 token, if not show warning
    # TODO: check token_bridge_helper connected to the loaded L2 token, if not show warning
    # TODO: check token_bridge_helper connected to the loaded L1 ticketer, if not show warning

    # TODO: echo TicketRouterTester address is going to be loaded
    ticket_router_tester = TicketRouterTester.from_address(
        tezos_account, TICKET_ROUTER_TESTER_ADDRESS
    )
    return token, ticketer, erc20, token_bridge_helper, ticket_router_tester
