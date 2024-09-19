# TODO: consider splitting to multiple files (?)

from scripts.helpers.etherlink.contract import (
    EvmContractHelper,
    make_filename,
)
from web3.types import TxReceipt


class BulkWithdrawalHelper(EvmContractHelper):
    filename = make_filename('BulkWithdrawal')