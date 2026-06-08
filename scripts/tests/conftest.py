from collections.abc import Generator, Iterator
from typing import Any

import pytest
from _pytest.fixtures import SubRequest
from gql import Client
from gql.client import SyncClientSession
from gql.transport.requests import RequestsHTTPTransport
from pytezos import pytezos
from pytezos.client import PyTezosClient

from scripts.helpers.contracts.contract import ContractHelper
from scripts.helpers.contracts.ticketer import Ticketer
from scripts.helpers.contracts.xtz_ticketer import XtzTicketer
from scripts.networks import TokenConfig, load_network
from scripts.tests.dto import Bridge
from scripts.tests.dto import Native
from scripts.tests.dto import Token
from scripts.tests.dto import Wallet

_NETWORK = load_network()


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    # Order the integration suite into a sensible sequence (health checks first,
    # deposit before withdraw, cementation last). Integration tests opt in with a
    # module-level `pytestmark = pytest.mark.integration`.
    function_order = {
        "test_indexer_is_healthy": 1,
        "test_l1_asset_whitelisted": 2,
        "test_l2_asset_whitelisted": 3,
        "test_asset_ticket_whitelisted": 4,
        "test_single_token_deposit": 5,
        "test_create_token_withdraw": 6,
        "test_finish_token_withdraw": 100,
    }
    function_mapping = {}
    for item in items:
        item_name = item.name.split('[', 1)[0]
        function_mapping[item] = (
            function_order[item_name] if item_name in function_order else 50
        )

    function_mapping = {
        k: v for k, v in sorted(function_mapping.items(), key=lambda x: x[1])
    }

    items[:] = [item for item in function_mapping]


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(
    item: pytest.Item, call: pytest.CallInfo[Any]
) -> Generator[None, Any, None]:
    outcome = yield
    if 'critical' in [mark.name for mark in item.own_markers]:
        result = outcome.get_result()

        if result.when == 'call' and result.failed:
            print('FAILED')
            pytest.exit('Exiting pytest due to critical test failure', 1)


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line('markers', 'critical: mark test as critical')


def _build_token(client: PyTezosClient, config: TokenConfig) -> Token:
    """Builds an FA token fixture, deriving the ticket data from the ticketer."""

    ticketer = Ticketer.from_address(client, config.l1_ticketer_address)
    wrapped = ticketer.get_token()
    ticket = ticketer.read_ticket()
    return Token(
        l1_asset_id=f'{wrapped.address}_{wrapped.token_id}',
        l1_ticketer_address=config.l1_ticketer_address,
        l1_ticket_helper_address=config.l1_ticket_helper_address,
        l2_token_address=config.l2_token_address,
        ticket_hash=ticket.hash(),
        ticket_content_hex=ticket.content.to_bytes_hex(),
    )


def _build_native(client: PyTezosClient) -> Native:
    """Builds the native XTZ fixture, deriving the ticket data from the ticketer."""

    config = _NETWORK.native
    ticketer = XtzTicketer.from_address(client, config.l1_ticketer_address)
    ticket = ticketer.read_ticket()
    return Native(
        l1_ticketer_address=config.l1_ticketer_address,
        l1_ticket_helper_address=config.l1_ticket_helper_address,
        ticket_hash=ticket.hash(),
        ticket_content_hex=ticket.content.to_bytes_hex(),
    )


@pytest.fixture(scope='session', autouse=True)
def bridge() -> Bridge:
    net = _NETWORK.network
    # Rollup timing are L1 protocol constants — read them off the node.
    constants = pytezos.using(shell=net.l1_rpc_url).shell.head.context.constants()
    return Bridge(
        l1_smart_rollup_address=net.smart_rollup_address,
        l1_rpc_url=net.l1_rpc_url,
        l2_rpc_url=net.l2_rpc_url,
        rollup_rpc_url=net.rollup_rpc_url,
        l2_kernel_address=net.l2_kernel_address,
        l2_withdraw_precompile_address=net.l2_withdraw_precompile_address,
        l2_native_withdraw_precompile_address=net.l2_native_withdraw_precompile_address,
        rollup_commitment_period=int(
            constants['smart_rollup_commitment_period_in_blocks']
        ),
        rollup_challenge_window=int(
            constants['smart_rollup_challenge_window_in_blocks']
        ),
        l1_time_between_blocks=int(constants['minimal_block_delay']),
    )


@pytest.fixture(scope='session', autouse=True)
def wallet() -> Wallet:
    acc = _NETWORK.accounts
    return Wallet(
        l1_private_key=acc.l1_private_key,
        l1_public_key_hash=acc.l1_public_key_hash,
        l2_private_key=acc.l2_private_key,
        l2_public_key=acc.l2_public_key,
        l2_master_key=acc.l2_master_key,
    )


@pytest.fixture(scope='session', autouse=True)
def indexer() -> Iterator[SyncClientSession]:
    transport = RequestsHTTPTransport(url=_NETWORK.network.indexer_graphql_url)
    with Client(transport=transport) as session:
        yield session


@pytest.fixture
def tezos_client(bridge: Bridge, wallet: Wallet) -> PyTezosClient:
    client: PyTezosClient = pytezos.using(
        shell=bridge.l1_rpc_url, key=wallet.l1_private_key
    )
    return client


@pytest.fixture
def native_asset(tezos_client: PyTezosClient) -> Native:
    return _build_native(tezos_client)


@pytest.fixture
def native_asset_helper(tezos_client: PyTezosClient) -> ContractHelper:
    return ContractHelper.from_address(
        tezos_client, _NETWORK.native.l1_ticket_helper_address
    )


@pytest.fixture(params=[token.symbol for token in _NETWORK.tokens])
def token(request: SubRequest, tezos_client: PyTezosClient) -> Token:
    config = next(t for t in _NETWORK.tokens if t.symbol == request.param)
    return _build_token(tezos_client, config)


@pytest.fixture(params=[token.symbol for token in _NETWORK.tokens] + ['xtz'])
def asset(request: SubRequest, tezos_client: PyTezosClient) -> Token | Native:
    if request.param == 'xtz':
        return _build_native(tezos_client)
    config = next(t for t in _NETWORK.tokens if t.symbol == request.param)
    return _build_token(tezos_client, config)


@pytest.fixture
def ticket_router_tester_address() -> str:
    return _NETWORK.network.ticket_router_tester_address
