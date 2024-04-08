from scripts.helpers.utility import (
    originate_from_file,
    get_build_dir,
)
from scripts.helpers.contracts import (
    ContractHelper,
    TokenHelper,
    Ticketer,
)
from pytezos.client import PyTezosClient
from pytezos.operation.group import OperationGroup
from os.path import join
from scripts.helpers.metadata import Metadata
from pytezos.contract.call import ContractCall
from scripts.helpers.addressable import (
    Addressable,
    get_address,
)
from typing import Optional


class TokenBridgeHelper(ContractHelper):
    @classmethod
    def originate(
        cls,
        client: PyTezosClient,
        ticketer: Ticketer,
        erc_proxy: bytes,
        token: Optional[TokenHelper] = None,
        symbol: Optional[str] = None,
    ) -> OperationGroup:
        """Deploys Token Bridge Helper"""

        token = token or ticketer.get_token()
        storage = {
            'token': token.as_dict(),
            'ticketer': ticketer.address,
            'erc_proxy': erc_proxy,
            'context': None,
            'metadata': Metadata.make_default(
                name=': '.join(filter(bool, ['Token Bridge Helper', symbol])),
                description='The Token Bridge Helper is a helper contract which helps user to communicate with Etherlink Bridge ' +
                            'components that requires tickets to be packed into external data structure.',
            ),
        }
        filename = join(get_build_dir(), 'token-bridge-helper.tz')

        return originate_from_file(filename, client, storage)

    def deposit(
        self, rollup: Addressable, receiver: bytes, amount: int
    ) -> ContractCall:
        """Deposits given amount of tokens to the L2 address set in routing data"""

        deposit_params = {
            'rollup': get_address(rollup),
            'receiver': receiver,
            'amount': amount,
        }
        return self.contract.deposit(deposit_params)

    def get_ticketer(self) -> Ticketer:
        """Returns ticketer"""

        ticketer_address = self.contract.storage['ticketer']()
        assert isinstance(ticketer_address, str)
        return Ticketer.from_address(self.client, ticketer_address)
