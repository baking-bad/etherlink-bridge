import pytest
from _pytest.fixtures import SubRequest
from gql import Client
from gql.client import SyncClientSession
from gql.transport.requests import RequestsHTTPTransport
from pytezos import PyTezosClient
from pytezos import pytezos

from scripts.helpers.contracts import ContractHelper
from scripts.tests.dto import Bridge
from scripts.tests.dto import Native
from scripts.tests.dto import Token
from scripts.tests.dto import Wallet


def pytest_collection_modifyitems(items):
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
        function_mapping[item] = function_order[item_name] if item_name in function_order else 50

    function_mapping = {k: v for k, v in sorted(function_mapping.items(), key=lambda x: x[1])}

    items[:] = [item for item in function_mapping]


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    if 'critical' in [mark.name for mark in item.own_markers]:
        result = outcome.get_result()

        if result.when == 'call' and result.failed:
            print('FAILED')
            pytest.exit('Exiting pytest due to critical test failure', 1)


def pytest_configure(config):
    config.addinivalue_line(
        'markers', 'critical: mark test as critical'
    )


token_bridge_data_collection: dict[str, Token] = {
    'tzBTC': Token(
        l1_asset_id='KT1Vq1toL9mQquJhCvVRbbcC8PbZJWM4bPui_0',
        l1_ticketer_address='KT1AAi4DCQiTUv5MYoXtdiFwUrPH3t3Yhkjo',
        l1_ticket_helper_address='KT1FcXb4oFBWtUVbEa96Do4DfQZXn6878yu1',
        l2_token_address='87dcBf128677ba36E79D47dAf4eb4e51610e0150',
        ticket_hash=105445818636660971509319453679864437153611706067407130365033371751245074533863,
        ticket_content_hex='0707000005090a000000a205020000009c07040100000010636f6e74726163745f616464726573730a000000244b5431567131746f4c396d5171754a6843765652626263433850625a4a574d346250756907040100000008646563696d616c730a0000000138070401000000046e616d650a00000005747a4254430704010000000673796d626f6c0a00000005747a4254430704010000000a746f6b656e5f747970650a000000054641312e32'
    ),
    'SIRS': Token(
        l1_asset_id='KT1DCKKboEMmpUtVnf7hTCnArxgNpFneHcv5_0',
        l1_ticketer_address='KT1GfTvzB5SG4eSsBEoNRyMyrspycaMHtUxu',
        l1_ticket_helper_address='KT1Gy188nbnThwYBwSKotZ4Zmp1s8nGfzQpG',
        l2_token_address='cB5d40c6B1bdf5Cd51b3801351b0A68D101a561b',
        ticket_hash=34922436212149484313669598314771677674007367402780603600217449304651574835404,
        ticket_content_hex='0707000005090a0000008d05020000008707040100000010636f6e74726163745f616464726573730a000000244b543144434b4b626f454d6d705574566e66376854436e417278674e70466e6548637635070401000000046e616d650a000000065369726975730704010000000673796d626f6c0a00000004534952530704010000000a746f6b656e5f747970650a000000054641312e32'
    ),
    'USDt': Token(
        l1_asset_id='KT1K6uyg7cjNRoPkYw6SfyCm1f2tPLHfVUez_0',
        l1_ticketer_address='KT1JT3T9jodxKchWEcwMtHzKTcM5pKD4phFp',
        l1_ticket_helper_address='KT1G4athp6hNRmy65MdM1stv3bXXh82NEvCH',
        l2_token_address='8554cD57C0C3E5Ab9d1782c9063279fA9bFA4680',
        ticket_hash=43575650035100448921274483650638746080150222307264247442952657670828945392893,
        ticket_content_hex='0707000005090a000000b90502000000b307040100000010636f6e74726163745f616464726573730a000000244b54314b3675796737636a4e526f506b597736536679436d31663274504c48665655657a07040100000008646563696d616c730a0000000136070401000000046e616d650a0000000a546574686572205553440704010000000673796d626f6c0a000000045553447407040100000008746f6b656e5f69640a00000001300704010000000a746f6b656e5f747970650a00000003464132'
    ),
}

xtz_bridge_data: Native = Native(
    l1_asset_id='xtz',
    l1_ticketer_address='KT1Bdyc1UcmjgPr3prJziMyfjSCPK6SEjfqs',
    l1_ticket_helper_address='KT1MJxf4KVN3sosR99VRG7WBbWTJtAyWUJt9',
    l2_token_address='xtz',
    ticket_hash=101110688806598147204195024607088171938890486509454352328316628879467313623014,
    ticket_content_hex='070700000306',
)


@pytest.fixture
def native_asset() -> Native:
    return xtz_bridge_data


@pytest.fixture
def tezos_client(bridge, wallet) -> PyTezosClient:
    return pytezos.using(shell=bridge.l1_rpc_url, key=wallet.l1_private_key)


@pytest.fixture
def native_asset_helper(tezos_client) -> ContractHelper:
    return ContractHelper.from_address(tezos_client, xtz_bridge_data.l1_ticket_helper_address)


@pytest.fixture
def fa1_2_token() -> Token:
    return token_bridge_data_collection['FA1.2']


@pytest.fixture
def fa2_token() -> Token:
    return token_bridge_data_collection['FA2']


@pytest.fixture(params=[token for token in token_bridge_data_collection.values()])
def token(request: SubRequest) -> Token:
    yield request.param


@pytest.fixture(params=[asset for asset in (token_bridge_data_collection | {'xtz': xtz_bridge_data}).values()])
def asset(request: SubRequest) -> Token | Native:
    yield request.param


@pytest.fixture
def ticket_router_tester_address() -> str:
    return 'KT19qCLRCbctH6KXaSFWptNgQebhDJgNrzER'


@pytest.fixture(scope='session', autouse=True)
def bridge() -> Bridge:
    return Bridge(
        l1_smart_rollup_address='sr1GBHEgzZmpWH4URqshZEZFCxBpqzi6ahvL',
        l1_rpc_url='https://rpc.tzkt.io/parisnet',
        l2_rpc_url='https://etherlink.dipdup.net',
        rollup_rpc_url='https://etherlink-rollup-paris.dipdup.net',
        l2_kernel_address='0x0000000000000000000000000000000000000000',
        l2_withdraw_precompile_address='0xff00000000000000000000000000000000000002',
        l2_native_withdraw_precompile_address='0xff00000000000000000000000000000000000001',
        rollup_commitment_period=20,
        rollup_challenge_window=40,
        l1_time_between_blocks=7,
    )


@pytest.fixture(scope='session', autouse=True)
def wallet() -> Wallet:
    return Wallet(
        l1_private_key='edskRvrUVVsEDcuupaGY94gcwajN9HUHPBBZci8jkaeWn3VXGaKqYHepDFmiTpBL4kVpzS7swQCEMJBwW2t4oTHC1FVSevbkTy',
        l1_public_key_hash='tz1TZDn2ZK35UnEjyuGQRVeM2NC5tQScJLpQ',
        l2_private_key='8636c473b431be57109d4153735315a5cdf36b3841eb2cfa80b75b3dcd2d941a',
        l2_public_key='0xBefD2C6fFC36249ebEbd21d6DF6376ecF3BAc448',
        l2_master_key='9722f6cc9ff938e63f8ccb74c3daa6b45837e5c5e3835ac08c44c50ab5f39dc0',
    )


@pytest.fixture(scope='session', autouse=True)
def indexer() -> SyncClientSession:
    transport = RequestsHTTPTransport(
        url='https://etherlink-bridge-indexer.dipdup.net/v1/graphql'
    )
    with Client(transport=transport) as session:
        yield session
