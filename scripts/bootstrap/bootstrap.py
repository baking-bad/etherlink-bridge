import os
from typing import Any

import click
import requests
import survey
from pytezos import PyTezosClient
from pytezos import pytezos
from pytezos.rpc import RpcError

from scripts.bootstrap.cli import echo
from scripts.bootstrap.cli import notice_echo
from scripts.bootstrap.cli import survey_table
from scripts.bootstrap.const import DEFAULT_TOKEN_ID
from scripts.bootstrap.const import KERNEL_ADDRESS
from scripts.bootstrap.const import MAINNET_TZKT_API_URL
from scripts.bootstrap.const import MAINNET_WHITELIST
from scripts.bootstrap.const import NETWORK_DEFAULTS
from scripts.bootstrap.dto import TicketerDTO
from scripts.bootstrap.dto import TicketerParamsDTO
from scripts.bootstrap.dto import TokenInfoDTO
from scripts.bootstrap.dto import TokenMetadataDTO
from scripts.bootstrap.dto import UserInputDTO
from scripts.etherlink import deploy_erc20
from scripts.helpers.contracts import TokenHelper
from scripts.tezos import deploy_ticketer
from scripts.tezos import deploy_token_bridge_helper
from scripts.tezos import get_ticketer_params


class EtherlinkBootstrapClient:
    def __init__(
        self,
        rpc_url: str,
        private_key: str,
    ):
        self._rpc_url = rpc_url
        self._private_key = private_key

    def deploy_erc20_proxy(self, ticketer_params: TicketerParamsDTO, metadata: TokenMetadataDTO) -> str:
        return deploy_erc20.callback(
            ticketer_address_bytes=ticketer_params.address_bytes_hex,
            ticket_content_bytes=ticketer_params.content_bytes_hex,
            token_name=metadata.name,
            token_symbol=metadata.symbol,
            token_decimals=metadata.decimals,
            kernel_address=KERNEL_ADDRESS,
            etherlink_private_key=self._private_key,
            etherlink_rpc_url=self._rpc_url,
        )


def ask_origination_confirmation(token_info: TokenInfoDTO) -> None:
    """Prints token info to the console and asks user to confirm origination."""

    supply = token_info.supply / 10 ** token_info.metadata.decimals
    supply_formatted = f'{supply:,}'.replace(',', '_')

    def accent(msg: str) -> str:
        return click.style(msg, fg='bright_cyan')

    echo('  - Name:     ' + accent(token_info.metadata.name))
    echo('  - Symbol:   ' + accent(token_info.metadata.symbol))
    echo('  - Decimals: ' + accent(str(token_info.metadata.decimals)))
    echo('  - Standard: ' + accent(token_info.standard))
    echo('  - Supply:   ' + accent(supply_formatted))

    echo(
        'The following 4 contracts will be deployed: '
        + accent('Token') + ', '
        + accent('Ticker') + ', '
        + accent('ERC20 Proxy') + ' and '
        + accent('Token Bridge Helper')
    )

    if not survey.routines.inquire('Proceed with origination?\n', default=True):
        survey.printers.fail('Good for you!')
        return


class TokenBootstrap:
    def __init__(
        self,
        mainnet_asset_id: str,
        is_mainnet: bool,
        tezos_client: PyTezosClient,
        etherlink_client: EtherlinkBootstrapClient,
        testrunner_account: str,
        use_test_prefix: bool,
        test_version: int,

    ):
        self._mainnet_asset_id = mainnet_asset_id
        self._is_mainnet = is_mainnet
        self._tezos_client = tezos_client
        self._etherlink_client = etherlink_client
        self._l1_testrunner_account = testrunner_account
        self._test_amount_multiplier = .2
        self._use_test_prefix = use_test_prefix
        self._test_version = test_version
        self._token_info: TokenInfoDTO

    def run(self, whitelist_counter: int):
        survey.printers.info(
            f'Whitelisting Token having asset_id {self._mainnet_asset_id} in Tezos Mainnet, parameters:',
            mark=f'[{whitelist_counter}]',
        )

        self._fetch_mainnet_token_metadata()
        ask_origination_confirmation(self._token_info)

        asset_id = self.deploy_test_token()
        # asset_id = self.prepare_l1_token()
        ticketer_data = self.deploy_ticketer(asset_id)
        erc20_proxy_address = self.deploy_erc20_proxy(ticketer_data.ticketer_params)
        self.deploy_helper(ticketer_data.ticketer.address, erc20_proxy_address)

    def prepare_l1_token(self) -> str:
        contract_address, token_id = self._mainnet_asset_id.split('_')
        try:
            self._tezos_client.contract(contract_address)
        except (RpcError, AssertionError):
            # have to deploy test copy of mainnet whitelisted token
            return self.deploy_test_token()
        else:
            # looks like we already on mainnet
            self._fetch_mainnet_token_metadata()
            return self._mainnet_asset_id

    def _fetch_mainnet_token_metadata(self) -> None:
        contract_address, token_id = self._mainnet_asset_id.split('_')

        token_data = requests.get(f'{MAINNET_TZKT_API_URL}/tokens?contract={contract_address}&tokenId={token_id}').json()[0]
        if self._use_test_prefix:
            token_data['metadata']['name'] = ' '.join(['Test', token_data['metadata']['name'], f'v{self._test_version}'])
            token_data['metadata']['symbol'] = '_'.join(['TEST', token_data['metadata']['symbol'], str(self._test_version)])

        self._token_info = TokenInfoDTO(
            metadata=TokenMetadataDTO(
                name=token_data['metadata']['name'],
                symbol=token_data['metadata']['symbol'],
                decimals=token_data['metadata'].get('decimals'),
            ),
            standard=token_data['standard'].upper(),
            supply=int(token_data['totalSupply']),
        )

    def deploy_test_token(self) -> str:
        contract_address, token_id = self._mainnet_asset_id.split('_')

        survey.printers.text('', end='\r', )
        survey.printers.text('\n'*5, re=True)
        survey.printers.text('', end='\r', re=True)
        state = ''
        with survey.graphics.SpinProgress(
            prefix='Origination of testing Token Contract ',
            suffix=lambda x: state,
        ):
            token = TokenHelper.get_cls(self._token_info.standard)

            state = ' processing transaction...'
            supply = self._token_info.supply
            round_mask = 10 ** (len(str(supply)) - 2)
            test_amount = int(supply * self._test_amount_multiplier / round_mask) * round_mask
            balances = {
                self._tezos_client.key.public_key_hash(): abs(supply - test_amount),
                self._l1_testrunner_account: test_amount,
            }

            metadata_encoded = {k: str(v).encode() for k, v in self._token_info.metadata.model_dump().items()}
            opg = token.originate(self._tezos_client, balances, int(token_id), metadata_encoded).send()
            self._tezos_client.wait(opg)
            deployed_token = token.from_opg(self._tezos_client, opg)

        asset_id = f'{deployed_token.address}_{deployed_token.token_id}'
        survey.printers.done(f'FA Contract deployed: Token `{self._token_info.metadata.name}` with asset_id {asset_id}.', re=True)
        return asset_id

    def deploy_ticketer(self, asset_id) -> TicketerDTO:
        contract_address, token_id = asset_id.split('_')
        token_id = int(token_id)

        survey.printers.text('', end='\r', )
        survey.printers.text('\n'*3, re=True)
        survey.printers.text('', end='\r', re=True)
        state = ''
        with survey.graphics.SpinProgress(
            prefix='Ticketer Contract Origination ',
            suffix=lambda x: state,
        ):
            state = ' processing transaction...'
            ticketer = deploy_ticketer.callback(
                token_address=contract_address,
                token_type=self._token_info.standard,
                token_id=token_id,
                token_name=self._token_info.metadata.name,
                token_decimals=self._token_info.metadata.decimals,
                token_symbol=self._token_info.metadata.symbol,
                tezos_private_key=self._tezos_client.context.key,
                tezos_rpc_url=self._tezos_client.context.shell,
            )

            state = ' fetching ticketer params...'
            ticketer_params_dict = get_ticketer_params.callback(
                ticketer.address,
                self._tezos_client.context.key,
                self._tezos_client.context.shell,
            )

            ticket_hash = ticketer.read_ticket().hash()

            ticketer_params = TicketerParamsDTO(
                address_bytes_hex=ticketer_params_dict['address_bytes'],
                content_bytes_hex=ticketer_params_dict['content_bytes'],
            )

        survey.printers.done(f'Ticketer Contract deployed for Token `{self._token_info.metadata.name}`: {ticketer.address}.', re=True)
        return TicketerDTO(
            ticketer=ticketer,
            ticketer_params=ticketer_params,
            ticket_hash=ticket_hash,
        )

    def deploy_erc20_proxy(self, ticketer_params) -> str:
        survey.printers.text('', end='\r', )
        survey.printers.text('\n'*3, re=True)
        survey.printers.text('', end='\r', re=True)
        with survey.graphics.SpinProgress(
            prefix='Etherlink ERC20 Proxy Contract Origination ',
            suffix=' processing transaction...',
        ):
            erc20_proxy_address = self._etherlink_client.deploy_erc20_proxy(
                ticketer_params=ticketer_params,
                metadata=self._token_info.metadata,
            )

        survey.printers.done(
            f'Etherlink ERC20 Proxy Contract deployed for Token `{self._token_info.metadata.name}`: 0x{erc20_proxy_address}.',
            re=True,
        )
        return erc20_proxy_address.lower()

    def deploy_helper(self, ticketer_address, erc20_proxy_address):
        survey.printers.text('', end='\r')
        with survey.graphics.SpinProgress(
            prefix='Token Bridge Helper Contract Origination ',
            suffix=' processing transaction...',
        ):
            helper = deploy_token_bridge_helper.callback(
                ticketer_address=ticketer_address,
                erc20_proxy_address=erc20_proxy_address,
                tezos_private_key=self._tezos_client.context.key,
                tezos_rpc_url=self._tezos_client.context.shell,
                token_symbol=self._token_info.metadata.symbol,
            )

        survey.printers.done(
            f'Token Bridge Helper Contract deployed for Token `{self._token_info.metadata.name}`: {helper.address}.',
            re=True,
        )


class RollupBootstrap:
    def __init__(
        self,
        is_mainnet: bool,
        tezos_client: PyTezosClient,
        tokens: list[TokenBootstrap],
    ):
        self._is_mainnet = is_mainnet
        self._tezos_client = tezos_client
        self._tokens = tokens

    def run(self):
        self.deploy_whitelist()
        # deploy_ticket_router_tester

    def deploy_whitelist(self):
        survey.printers.info('Bootstrapping Whitelist...')
        for index, token_bootstrap in enumerate(self._tokens):
            token_bootstrap.run(index+1)


class BootstrapSurvey:
    def __init__(self, network_defaults: list[dict[str, Any]]):
        self._network_defaults = network_defaults
        self._defaults = {}
        self._l1_rpc_url: str

    def perform(self) -> UserInputDTO:
        self._get_network()
        l1_rpc_url = self._get_l1_rpc_url()
        return UserInputDTO(
            l1_rpc_url=l1_rpc_url,
            is_mainnet=self._defaults.get('is_mainnet', False),
            smart_rollup_address=self._get_smart_rollup_address(),
            l1_private_key=self._get_l1_private_key(),
            l2_rpc_url=self._get_l2_rpc_url(),
            l2_private_key=self._get_l2_private_key(),
            l1_testrunner_account=self._get_l1_testrunner_account(),
            use_test_prefix=self._get_use_test_prefix(),
        )

    def _get_network(self) -> None:
        network_index = survey.routines.select(
            'Choose which Tezos Network Smart Rollup for your Bridge is deployed to?\n',
            options=[network['name'] for network in NETWORK_DEFAULTS],
            index=0,
        )

        self._defaults = self._network_defaults[network_index]

    def _get_l1_rpc_url(self) -> str:
        while True:
            l1_rpc_url = survey.routines.input(
                'Enter the address of your RPC Node\n',
                value=self._defaults.get('l1_rpc_url', ''),
            ).rstrip('/')
            try:
                survey.printers.text('', end='\r')
                url = f'{l1_rpc_url}/chains/main/blocks/head'
                with survey.graphics.SpinProgress(
                    prefix='Checking the specified RPC Endpoint ',
                    suffix=f' fetching {url}',
                ):
                    response = requests.get(url).json()
                    assert response['protocol']
            except (IOError, AssertionError):
                survey.printers.fail('Could not retrieve the specified RPC Endpoint. Please try again.', re=True)
            else:
                self._l1_rpc_url = l1_rpc_url
                survey.printers.text('', end='\r', re=True)
                return l1_rpc_url

    def _get_tzkt_api_url(self) -> str:
        tzkt_api_url = self._defaults.get('tzkt_api_url')
        if tzkt_api_url:
            return tzkt_api_url

        while True:
            tzkt_api_url = survey.routines.input('Enter Tzkt API Url\n').rstrip('/')
            survey.printers.text('', end='\r')
            try:
                survey.printers.text('', end='\r')
                url = f'{tzkt_api_url}/head'
                with survey.graphics.SpinProgress(
                    prefix='Checking the specified Tzkt API Url ',
                    suffix=f' fetching {url}',
                ):
                    response = requests.get(url).json()
                    assert response['chain']
            except (IOError, AssertionError):
                survey.printers.fail('Could not retrieve the specified Tzkt API Url. Please try again.', re=True)
            else:
                self._tzkt_api_url = tzkt_api_url
                survey.printers.text('', end='\r', re=True)
                return tzkt_api_url

    def _get_smart_rollup_address(self) -> str:
        while True:
            smart_rollup_address = survey.routines.input(
                'Enter the Smart Rollup address\n',
                value=self._defaults.get('smart_rollup_address', ''),
            )
            survey.printers.text('', end='\r')
            try:
                with survey.graphics.SpinProgress(
                    prefix='Checking the specified RPC Endpoint ',
                ):
                    response = requests.get(
                        f'{self._l1_rpc_url}/chains/main/blocks/head/context/smart_rollups/smart_rollup/{smart_rollup_address}' +
                        '/genesis_info',
                    ).json()
                    assert isinstance(response, dict)
                    assert response['level']
            except (IOError, AssertionError):
                survey.printers.fail('Could not retrieve the specified Smart Rollup address. Please try again.', re=True)
            else:
                survey.printers.text('', end='\r', re=True)
                return smart_rollup_address

    def _get_l1_private_key(self) -> str:
        while True:
            l1_private_key = survey.routines.input(
                'Enter the Private Key of Account for contracts origination on the Tezos network\n',
                value=self._defaults.get('l1_private_key', ''),
            )
            survey.printers.text('', end='\r')
            try:
                state = None
                with survey.graphics.SpinProgress(
                    prefix='Checking the specified account ',
                    suffix=lambda x: state,
                ):
                    state = ' fetching balance...'
                    client = pytezos.using(
                        shell=self._l1_rpc_url,
                        key=l1_private_key,
                    )
                    balance = client.balance()
                    assert int(balance) > 0

                    state = ' check if account is revealed...'
                    try:
                        client.reveal().autofill().sign().inject()
                    except RpcError:
                        pass

            except (OSError, ValueError):
                survey.printers.fail('Incorrect Private Key is specified. Please try again.', re=True)
            except AssertionError:
                survey.printers.fail('Account has insufficient balance to contracts origination. Please try again.', re=True)
            else:
                survey.printers.text('', end='\r', re=True)
                return l1_private_key

    def _get_l2_rpc_url(self) -> str:
        l2_rpc_url = survey.routines.input(
            f'Enter Etherlink RPC Endpoint for your Rollup on the {self._defaults["name"]}\n',
            value=self._defaults.get('l2_rpc_url', ''),
        )
        return l2_rpc_url

    def _get_l2_private_key(self) -> str:
        l2_private_key = survey.routines.input(
            'Enter the Private Key of Account for contracts origination on the Etherlink network\n',
            value=self._defaults.get('l2_private_key', ''),
        )
        return l2_private_key

    def _get_l1_testrunner_account(self) -> str:
        l1_testrunner_account = survey.routines.input(
            'Enter the Public Key Hash of Tezos Account for running integration tests\n',
            value=self._defaults.get('l1_testrunner_account', ''),
        )
        return l1_testrunner_account

    @staticmethod
    def _get_use_test_prefix() -> bool:
        _, use_test_prefix = survey_table(
            question='Do you want to use test prefixes for new tokens?',
            options=['No', 'Yes'],
            comments=[
                'Sirius\t\t$SIRS',
                'Test Sirius v42\t$TEST_SIRS_42',
            ],
            default=1,
        )
        return {'Yes': True, 'No': False}[use_test_prefix]


@click.command()
def rollout():
    notice_echo('This command will help you to deploy all contracts for a new rollup.')
    bootstrap_survey = BootstrapSurvey(network_defaults=NETWORK_DEFAULTS)
    user_input = bootstrap_survey.perform()

    rollup_bootstrap_service = RollupBootstrapFactory.build(user_input)
    notice_echo('Starting Bridge Application Bootstrap process.')
    rollup_bootstrap_service.run()


class RollupBootstrapFactory:
    @classmethod
    def build(cls, user_input: UserInputDTO):
        tezos_client = pytezos.using(
            shell=user_input.l1_rpc_url,
            key=user_input.l1_private_key,
        )
        etherlink_client = EtherlinkBootstrapClient(
            rpc_url=user_input.l2_rpc_url,
            private_key=user_input.l2_private_key,
        )

        test_version: int = cls._bump_test_version() if user_input.use_test_prefix else 0

        tokens = []
        for mainnet_asset_id in MAINNET_WHITELIST:
            token_bootstrap = TokenBootstrap(
                mainnet_asset_id=mainnet_asset_id,
                is_mainnet=user_input.is_mainnet,
                tezos_client=tezos_client,
                etherlink_client=etherlink_client,
                testrunner_account=user_input.l1_testrunner_account,
                use_test_prefix=user_input.use_test_prefix,
                test_version=test_version,
            )
            tokens.append(token_bootstrap)

        return RollupBootstrap(
            is_mainnet=user_input.is_mainnet,
            tezos_client=tezos_client,
            tokens=tokens,
        )

    @staticmethod
    def _bump_test_version() -> int:
        filename = '.version'
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                version = int(f.read().strip())
        else:
            version = 0
        version += 1
        with open(filename, 'w') as f:
            f.write(str(version))
        return version
