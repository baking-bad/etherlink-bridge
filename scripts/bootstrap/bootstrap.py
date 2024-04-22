import os
from time import sleep
from typing import Any

import click
import requests
import survey
from pytezos import PyTezosClient
from pytezos import pytezos
from pytezos.rpc import RpcError

from scripts.bootstrap.const import DEFAULT_TOKEN_ID
from scripts.bootstrap.const import MAINNET_TZKT_API_URL
from scripts.bootstrap.const import MAINNET_WHITELIST
from scripts.bootstrap.const import NETWORK_DEFAULTS

from scripts.bootstrap.const import KERNEL_ADDRESS
from scripts.bootstrap.dto import TicketerDTO
from scripts.bootstrap.dto import UserInputDTO
from scripts.etherlink import deploy_erc20
from scripts.helpers.cli import notice_echo
from scripts.helpers.cli import prompt_anyof
from scripts.helpers.contracts import TokenHelper
from scripts.tezos import deploy_ticketer
from scripts.tezos import deploy_token_bridge_helper
from scripts.tezos import get_ticketer_params


class RollupBootstrap:
    def __init__(
        self,
        is_mainnet: bool,
        client: PyTezosClient,
        tzkt_api_url: str,
        testrunner_account: str,
        use_test_prefix: bool,
        l2_rpc_url: str,
        l2_private_key: str,
    ):
        self._is_mainnet = is_mainnet
        self._tzkt_api_url = tzkt_api_url
        self._client = client
        self._l1_testrunner_account = testrunner_account
        self._l2_rpc_url = l2_rpc_url
        self._l2_private_key = l2_private_key
        self._test_amount_multiplier = .2
        self._use_test_prefix = use_test_prefix
        self._test_version: int = self._bump_test_version() if use_test_prefix else 0

    def run(self):
        self.deploy_whitelist()
        # deploy_ticket_router_tester

    def deploy_whitelist(self):
        survey.printers.info('Bootstrapping Whitelist...')
        token_counter = 0
        for mainnet_asset_id in MAINNET_WHITELIST:
            token_counter += 1
            survey.printers.info(
                f'Whitelisting Token having asset_id {mainnet_asset_id} in Tezos Mainnet...',
                mark=f'[{token_counter}]',
            )
            asset_id = self.prepare_l1_token(mainnet_asset_id)
            ticketer_data = self.deploy_ticketer(asset_id)
            erc20_proxy_address = self.deploy_erc20_proxy(ticketer_data.ticketer_params, ticketer_data.token_data)
            self.deploy_helper(ticketer_data.token_data, ticketer_data.ticketer.address, erc20_proxy_address)

    def prepare_l1_token(self, asset_id: str) -> str:
        contract_address, token_id = asset_id.split('_')
        try:
            self._client.contract(contract_address)
            assert self._is_mainnet
        except (RpcError, AssertionError):
            # have to deploy test copy of mainnet whitelisted token
            return self.deploy_test_token(asset_id)
        else:
            # looks like we already on mainnet
            return asset_id

    def deploy_test_token(self, asset_id: str) -> str:
        contract_address, token_id = asset_id.split('_')

        survey.printers.text('', end='\r')
        state = None
        with survey.graphics.SpinProgress(
            prefix='Origination of testing Token Contract ',
            suffix=lambda x: state,
        ):
            state = ' fetching original token metadata...'
            token_data = requests.get(f'{MAINNET_TZKT_API_URL}/tokens?contract={contract_address}&tokenId={token_id}').json()[0]
            if self._use_test_prefix:
                token_data['metadata']['name'] = ' '.join(['Test', token_data['metadata']['name'], f'v{self._test_version}'])
                token_data['metadata']['symbol'] = '_'.join(['TEST', token_data['metadata']['symbol'], str(self._test_version)])
            token_info = {k: str(v).encode() for k, v in token_data['metadata'].items()}

            token = TokenHelper.get_cls(token_data['standard'].upper())

            state = ' processing transaction...'
            supply = int(token_data['totalSupply'])
            round_mask = 10 ** (len(str(supply)) - 2)
            test_amount = int(supply * self._test_amount_multiplier / round_mask) * round_mask
            balances = {
                self._client.key.public_key_hash(): abs(supply - test_amount),
                self._l1_testrunner_account: test_amount,
            }
            opg = token.originate(self._client, balances, int(token_id), token_info).send()
            self._client.wait(opg)
            deployed_token = token.from_opg(self._client, opg)

        asset_id = f'{deployed_token.address}_{deployed_token.token_id}'
        survey.printers.done(f'FA Contract deployed: Token `{token_data["metadata"]["name"]}` with asset_id {asset_id}.', re=True)
        return asset_id

    def deploy_ticketer(self, asset_id) -> TicketerDTO:
        contract_address, token_id = asset_id.split('_')
        token_id = int(token_id)

        survey.printers.text('', end='\r')
        state = None
        with survey.graphics.SpinProgress(
            prefix='Ticketer Contract Origination ',
            suffix=lambda x: state,
        ):
            url = f'{self._tzkt_api_url}/tokens?contract={contract_address}&tokenId={token_id}'
            attempt_count = 0
            while True:
                attempt_count += 1
                state = f' fetching {url} for token metadata... Attempt #{attempt_count}.'
                response = requests.get(url).json()
                if response and response[0].get('metadata', {}).get('symbol'):
                    token_data = response[0]
                    break
                sleep(5)

            symbol = token_data['metadata']['symbol']
            decimals = int(token_data['metadata'].get('decimals'), 0)

            state = ' processing transaction...'
            ticketer = deploy_ticketer.callback(
                token_address=contract_address,
                token_type=token_data['standard'].upper(),
                token_id=token_id,
                decimals=decimals,
                symbol=symbol,
                private_key=self._client.context.key,
                rpc_url=self._client.context.shell,
            )

            state = ' fetching ticketer params...'
            ticketer_params = get_ticketer_params.callback(
                ticketer.address,
                self._client.context.key,
                self._client.context.shell,
            )
            ticket_hash = ticketer.get_ticket_hash(ticketer_params)

        survey.printers.done(f'Ticketer Contract deployed for Token ${symbol}: {ticketer.address}.', re=True)
        return TicketerDTO(
            token_data=token_data,
            ticketer=ticketer,
            ticketer_params=ticketer_params,
            ticket_hash=ticket_hash,
        )

    def deploy_erc20_proxy(self, ticketer_params, token_data) -> str:
        survey.printers.text('', end='\r')
        with survey.graphics.SpinProgress(
            prefix='Etherlink ERC20 Proxy Contract Origination ',
            suffix=' processing transaction...',
        ):
            erc20_proxy_address = deploy_erc20.callback(
                ticketer_address_bytes=ticketer_params['address_bytes'],
                ticket_content_bytes=ticketer_params['content_bytes'],
                token_name=token_data['metadata']['name'],
                token_symbol=token_data['metadata']['symbol'],
                decimals=int(token_data['metadata'].get('decimals'), DEFAULT_TOKEN_ID),
                kernel_address=KERNEL_ADDRESS,
                private_key=self._l2_private_key,
                rpc_url=self._l2_rpc_url,
            )

        survey.printers.done(
            f'Etherlink ERC20 Proxy Contract deployed for Token ${token_data["metadata"]["symbol"]}: 0x{erc20_proxy_address}.',
            re=True,
        )
        return erc20_proxy_address.lower()

    def deploy_helper(self, token_data, ticketer_address, erc20_proxy_address):
        survey.printers.text('', end='\r')
        with survey.graphics.SpinProgress(
            prefix='Token Bridge Helper Contract Origination ',
            suffix=' processing transaction...',
        ):
            helper = deploy_token_bridge_helper.callback(
                ticketer_address=ticketer_address,
                proxy_address=erc20_proxy_address,
                private_key=self._client.context.key,
                rpc_url=self._client.context.shell, 
            )

        survey.printers.done(
            f'Token Bridge Helper Contract deployed for Token ${token_data["metadata"]["symbol"]}: {helper.address}.',
            re=True,
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


class BootstrapSurvey:
    def __init__(self, network_defaults: list[dict[str, Any]]):
        self._network_defaults = network_defaults
        self._defaults = {}
        self._l1_rpc_url = ''

    def perform(self) -> UserInputDTO:
        l1_rpc_url = self._get_l1_rpc_url()
        tzkt_api_url=self._get_tzkt_api_url()
        return UserInputDTO(
            l1_rpc_url=l1_rpc_url,
            tzkt_api_url=tzkt_api_url,
            is_mainnet=tzkt_api_url == MAINNET_TZKT_API_URL,
            smart_rollup_address=self._get_smart_rollup_address(),
            l1_private_key=self._get_l1_private_key(),
            l2_rpc_url=self._get_l2_rpc_url(),
            l2_private_key=self._get_l2_private_key(),
            l1_testrunner_account=self._get_l1_testrunner_account(),
            use_test_prefix=self._get_use_test_prefix(),
        )

    def _get_l1_rpc_url(self) -> str:
        options = [network['name'] for network in NETWORK_DEFAULTS]
        options.append('Private')
        comments = [f'Will be used RPC Endpoint {network["rpc_url"]}' for network in NETWORK_DEFAULTS]
        comments.append('Enter custom RPC Endpoint')
        while True:
            network_index, _ = prompt_anyof(
                question='Choose which Tezos Network Smart Rollup for your Bridge is deployed to?',
                options=options,
                comments=comments,
                default=0,
            )
            if network_index == len(options) - 1:
                rpc_url = survey.routines.input('Enter the address of your private RPC Node\n')
            else:
                rpc_url = self._network_defaults[network_index]['rpc_url']
            rpc_url = rpc_url.rstrip('/')
            try:
                survey.printers.text('', end='\r')
                with survey.graphics.SpinProgress(
                    prefix='Checking the specified RPC Endpoint ',
                ):
                    url = f'{rpc_url}/chains/main/blocks/head'
                    response = requests.get(url).json()
                    assert response['protocol']
            except (IOError, AssertionError):
                survey.printers.fail('Could not retrieve the specified RPC Endpoint. Please try again.', re=True)
            else:
                self._network_defaults.append({'name': 'Private Network'})
                self._defaults = self._network_defaults[network_index]
                self._l1_rpc_url = rpc_url
                survey.printers.text('', end='\r', re=True)
                return rpc_url

    def _get_tzkt_api_url(self) -> str:
        return self._defaults.get(
            'tzkt_api_url',
            survey.routines.input('Enter Tzkt API url\n'),
        )

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
                with survey.graphics.SpinProgress(
                    prefix='Checking the specified account ',
                ):
                    balance = pytezos.using(
                        shell=self._l1_rpc_url,
                        key=l1_private_key,
                    ).balance()
                    assert int(balance) > 0
            except (OSError, ValueError, AssertionError):
                survey.printers.fail(
                    'Incorrect Private Key is specified or the Account has insufficient balance to contracts ' +
                    'origination. Please try again.',
                    re=True,
                )
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
        _, use_test_prefix = prompt_anyof(
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
    @staticmethod
    def build(user_input: UserInputDTO):
        tezos_client = pytezos.using(
            shell=user_input.l1_rpc_url,
            key=user_input.l1_private_key,
        )
        return RollupBootstrap(
            is_mainnet=user_input.is_mainnet,
            client=tezos_client,
            tzkt_api_url=user_input.tzkt_api_url,
            testrunner_account=user_input.l1_testrunner_account,
            use_test_prefix=user_input.use_test_prefix,
            l2_rpc_url=user_input.l2_rpc_url,
            l2_private_key=user_input.l2_private_key,
        )
