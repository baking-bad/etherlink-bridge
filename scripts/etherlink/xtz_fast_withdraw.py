import click
from eth_typing import ChecksumAddress
from web3.contract import Contract  # type: ignore
from eth_account.signers.local import LocalAccount
from web3.types import HexBytes, TxReceipt  # type: ignore
from web3 import Web3
from scripts.helpers.utility import (
    get_etherlink_web3,
    get_etherlink_account,
    pack,
)
from scripts.helpers.formatting import (
    accent,
    echo_variable,
    wrap,
    format_int,
)
from scripts import cli_options


# TODO: consider reusing EvmContractHelper for FastWithdrawal as well?
# (would require to have a contract with ABI and bytecode OR changes to the EvmContractHelper)
def load_withdraw_precompile(
    precompile_address: ChecksumAddress, web3: Web3
) -> Contract:
    FAST_WITHDRAWALS_ABI = [
        {
            "type": "function",
            "name": "fast_withdraw_base58",
            "constant": False,
            "payable": True,
            "inputs": [
                {"type": "string", "name": "target"},
                {"type": "string", "name": "fast_withdrawal_contract"},
                {"type": "bytes", "name": "payload"},
            ],
        }
    ]

    return web3.eth.contract(address=precompile_address, abi=FAST_WITHDRAWALS_ABI)


def make_fast_withdrawal(
    etherlink_account: LocalAccount,
    web3: Web3,
    precompile_contract: Contract,
    target: str,
    fast_withdrawals_contract: str,
    payload: bytes,
    wei_amount: int,
) -> TxReceipt:
    call = precompile_contract.functions.fast_withdraw_base58(
        target,
        fast_withdrawals_contract,
        payload,
    )

    transaction = call.build_transaction(
        {
            'from': etherlink_account.address,
            'value': web3.to_wei(wei_amount, 'wei'),
            'nonce': web3.eth.get_transaction_count(etherlink_account.address),
            'chainId': web3.eth.chain_id,
        }
    )

    signed_txn = web3.eth.account.sign_transaction(transaction, etherlink_account.key)
    txn_hash = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
    txn_receipt = web3.eth.wait_for_transaction_receipt(txn_hash)

    return txn_receipt


@click.command()
@click.option(
    '--target',
    required=True,
    prompt='Target receiver address',
    help='The address of the recipient receiving the tokens on the Tezos side.',
)
@click.option(
    '--fast-withdrawal-contract',
    required=True,
    prompt='Fast Withdrawal contract address on the Tezos side',
    help='The address of the Fast Withdrawal contract that routes tickets from the Smart Rollup on the Tezos side',
)
# TODO: this is duplicated copy from xtz_withdraw.py, probably should be moved to a common place:
# TODO: consider providing amount in mutez too?
@click.option(
    '--amount',
    required=True,
    type=int,
    default=1_000_000_000_000_000_000,
    prompt='Amount (wei)',
    help='The amount of xtz to withdraw in wei. Note that 1 xtz on Etherlink side is 10**18 wei. NOTE: it is impossible to withdraw values that have residuals less than 1 mutez (10**12 wei).',
)
@click.option(
    '--discounted-amount',
    required=True,
    prompt='Discounted withdrawal amount (mutez)',
    help='The discounted amount of the Fast Withdrawal that the Service Provider on the Tezos side can accept. Measured in mutez (1 mutez = 10**12 wei), it is included in the Fast Withdrawal payload.',
)
@cli_options.xtz_withdraw_precompile
@cli_options.etherlink_private_key
@cli_options.etherlink_rpc_url
# TODO: consider changing name to some verb
def xtz_fast_withdraw(
    target: str,
    fast_withdrawal_contract: str,
    amount: int,
    discounted_amount: int,
    withdraw_precompile: str,
    etherlink_private_key: str,
    etherlink_rpc_url: str,
) -> str:
    """Creates a Fast Withdrawal transaction on the Etherlink side"""

    web3 = get_etherlink_web3(etherlink_rpc_url)
    account = get_etherlink_account(web3, etherlink_private_key)

    amount_mutez = amount // 10**12
    fee = amount_mutez - discounted_amount
    payload = pack(discounted_amount, 'nat')

    click.echo('Making Fast Withdrawal, XTZ:')
    echo_variable('  - ', 'Sender', account.address)
    echo_variable('  - ', 'Etherlink RPC node', etherlink_rpc_url)
    click.echo('  - Withdrawal params:')
    echo_variable('      * ', 'Target', target)
    echo_variable('      * ', 'Fast Withdrawal contract', fast_withdrawal_contract)
    echo_variable('      * ', 'Payload bytes', payload.hex())
    echo_variable('      * ', 'Amount (mutez)', format_int(amount_mutez))
    echo_variable('      * ', 'Discounted amt (mutez)', format_int(discounted_amount))
    echo_variable('      * ', 'Fee (mutez)', format_int(fee))

    checksum_addr = Web3.to_checksum_address(withdraw_precompile)
    precompile_contract = load_withdraw_precompile(checksum_addr, web3)
    receipt = make_fast_withdrawal(
        etherlink_account=account,
        web3=web3,
        precompile_contract=precompile_contract,
        target=target,
        fast_withdrawals_contract=fast_withdrawal_contract,
        payload=payload,
        wei_amount=amount,
    )

    tx_hash: HexBytes = receipt.transactionHash  # type: ignore
    click.echo(
        'Successfully initiated XTZ Fast Withdrawal, tx hash: '
        + wrap(accent(tx_hash.hex()))
    )
    return tx_hash.hex()
