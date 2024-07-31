from scripts.helpers.etherlink.contract import (
    EvmContractHelper,
    make_filename,
)


class Erc20ProxyHelper(EvmContractHelper):
    filename = make_filename('ERC20Proxy')
