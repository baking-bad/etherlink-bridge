# Etherlink FA Token Bridge

Smart contracts for an FA tokens bridge between Tezos and Etherlink, implementation of [TZIP-029](https://gitlab.com/baking-bad/tzip/-/blob/wip/029-etherlink-token-bridge/drafts/current/draft-etherlink-token-bridge/etherlink-token-bridge.md) standard.

Tezos side:
- [**Ticketer**](tezos/contracts/ticketer/ticketer.mligo). Enables wrapping of **FA1.2** and **FA2** tokens into tickets. These tickets can then be sent to the bridge using a permissionless ticket transport mechanism.
- [**TokenBridgeHelper**](tezos/contracts/token-bridge-helper/token-bridge-helper.mligo). Designed to allow users to transfer tickets even without the support for the **ticket_transfer** operation in the current Tezos infrastructure. The Token Bridge Helper implementation focused on FA1.2 and FA2 tokens only.

Etherlink side:
- [**ERC20Proxy**](etherlink/src/ERC20Proxy.sol). An ERC20 contract that implements the L2 proxy [deposit interface](https://gitlab.com/baking-bad/tzip/-/blob/wip/029-etherlink-token-bridge/drafts/current/draft-etherlink-token-bridge/etherlink-token-bridge.md#l2-proxy-deposit-interface) and [withdraw interface](https://gitlab.com/baking-bad/tzip/-/blob/wip/029-etherlink-token-bridge/drafts/current/draft-etherlink-token-bridge/etherlink-token-bridge.md#l2-proxy-withdraw-interface).

### Setup
1. To run FA Token Bridge scripts it is required for the [Poetry](https://python-poetry.org/) to be installed in the system:
```shell
curl -sSL https://install.python-poetry.org | python3 -
```

2. Install all Python dependencies with:
```shell
poetry install
```

3. To rebuild and test contracts it is also required to install Foundry and LIGO, see [compilation and running tests](#compilation-and-running-tests).

### Bridging a new Token
> To set up environment, run `poetry run init_wallets`. It will ask Tezos and Etherlink keys, RPC node URIs and other variables used in scripts.

> To get some funds in to pay for the execution fees:
> - Tezos testnets [faucet](https://faucet.pariscnet.teztnets.com/)
> - Etherlink testnets [faucet](https://faucet.etherlink.com/)

To establish a new bridge between Tezos and Etherlink for existing `FA1.2` and `FA2` tokens there is a `bridge_token` command that would deploy three contracts:
- Ticketer contract on the Tezos side,
- ERC20 contract on the Etherlink side,
- Token Bridge Helper on the Tezos side.

This command requires a user to provide all necessary information about the token as argument parameters:
- `--token-address`: The address of the token contract.
- `--token-type`: Token type, either `FA2` or `FA1.2`.
- `--token-id`: Identifier of the token in the contract (only for FA2), default: `0`.
- `--decimals`: Token decimals added to the bridged ERC20 token and ticketer metadata content.
- `--symbol`: Token symbol added to the bridged ERC20 token and ticketer metadata content.
- `--name`: Token name added to the ERC20 token and ticketer metadata content.

There are also optional parameters that should be provided via environment variable or as a parameters to the `bridge_token` command:
- `--tezos-private-key`: Private key that would be used to deploy contracts on the Tezos network.
- `--tezos-rpc-url`: Tezos RPC URL.
- `--etherlink-private-key`: Private key that would be used to deploy contract on the Etherlink side.
- `--etherlink-rpc-url`: Etherlink RPC URL.
- `--kernel-address`: The address of the Etherlink kernel that will be managing the token.

Here is an example of the command to deploy an `FA1.2 tzBTC` Token bridge contracts in the Ghostnet:
```shell
poetry run bridge_token \
    --token-address KT1P8RdJ5MfHMK5phKJ5JsfNfask5v2b2NQS \
    --token-type "FA1.2" \
    --decimals 8 \
    --symbol "tzBTC" \
    --name "tzBTC test token" \
    --tezos-rpc-url "https://rpc.tzkt.io/ghostnet/" \
    --etherlink-rpc-url "https://node.ghostnet.etherlink.com/"
```

To find out the details of how the FA Bridge contracts deployed and communicate with each other, see: [bridge configuration](docs/Bridge-configuration.md)

### Deposit
To deposit a token, users need to wrap tokens to tickets and then transfer them to the smart rollup address, along with routing info provided in the [specified format](https://gitlab.com/baking-bad/tzip/-/blob/wip/029-etherlink-token-bridge/drafts/current/draft-etherlink-token-bridge/etherlink-token-bridge.md#deposit): a 40 bytes payload comprising `| receiver | proxy |`. The Token Bridge Helper contract allows users to perform these operations in one call. To deposit a token users may utilize `deposit` command and provide the `--token-bridge-helper-address` and a bridged `--amount` as parameters. Here is an example:
```shell
poetry run deposit --token-bridge-helper-address KT1RWw9NyPDZm9jeiEA1hXMd4PgGQVPHYrzj --amount 77
```
Here are examples of these operations on the [Tezos](https://oxfordnet.tzkt.io/opKzkXfctBRH7cBHSKm6r3EJR4YcWBoSQyjWdvmird8esAssatS/228619) and [Etherlink](http://blockscout.dipdup.net/tx/0x35f7b104df97784a22b75ac78708bcdc9286fccd5a193915d19cb56380e1e94c) sides.

### Withdrawal Process
The withdrawal process consists of two steps:
1. Initiating the withdrawal on the Etherlink side, leading to the creation of an outbox message from Etherlink to Tezos.
2. Finalizing the withdrawal on the Tezos side by executing the outbox message, after the settlement of the commitment.

#### Etherlink Withdrawal
To initiate a withdrawal on the Etherlink side, users must invoke the withdrawal precompile. An **ERC20Proxy** address along with routing info should be provided. The [specified format](https://gitlab.com/baking-bad/tzip/-/blob/wip/029-etherlink-token-bridge/drafts/current/draft-etherlink-token-bridge/etherlink-token-bridge.md#withdrawal) of the routing info is a 44-byte concatenation of two forged contracts: `| receiver | proxy |`.

To demonstrate this operation, the `withdraw` script is provided, which requires the `--proxy-address` (an ERC20 token address), the `--router-address` (a ticketer address which will process the ticket from the rollup), and the bridged `--amount` to withdraw from Etherlink. Furthermore, `--ticketer-address-bytes` and `--ticketer-content-bytes` are required to enable the **ERC20Proxy** to validate the token before burning it.

NOTE: The **Ticketer** implements a router withdrawal interface, and it will automatically unwrap tickets for a specified `receiver`.

Below is an example demonstrating the execution of a script that initiates the withdrawal of 18 tokens previously deposited on Etherlink.
```shell
poetry run withdraw --proxy-address 0x03E39FF2b379FBcd9284Ab457113D82fF4daBBF4 --amount 18 --ticketer-address-bytes 0125cf30bfba37ed7907f524f7b4eaf304e03d097600 --ticket-content-bytes 0707000005090a0000005f05020000005907040100000010636f6e74726163745f616464726573730a0000001c050a0000001601aca11e3f7734be9b46df1642a7d5f7d66c7bf6e8000704010000000a746f6b656e5f747970650a0000000b0501000000054641312e32 --router-address KT1C2gmhvA1FrscWe8KbrHf8dWG9XJETR127
```
Here is an example of the [withdraw](http://blockscout.dipdup.net/tx/0x51b9f37dbd18ca24b6c92f8685713f5d9767fbd1bdb3b8b8a00b88197c42c73c) operation.

#### Finalizing Tezos Withdrawal
To finalize the withdrawal process on the Tezos side, users must invoke the outbox message after it has been settled. To do this, the **commitment** hash and **proof** bytes need to be acquired, which in turn are obtainable from the rollup node by **outboxLevel** and **outboxMsgId**. These parameters are part of the **Withdrawal** event that is emitted during the withdrawal process on the Etherlink side.

Since both **outboxLevel** and **outboxMsgId** are of type `uint256`, to extract **outboxMsgId**, users should take the last 32 bytes from the **Withdrawal** event logs. For **outboxLevel**, the preceding 32 bytes should be taken and both should be converted into integers. Here's how this process can be executed:

- Link to the block explorer with the withdrawal transaction: [blockscout](http://blockscout.dipdup.net/tx/0x51b9f37dbd18ca24b6c92f8685713f5d9767fbd1bdb3b8b8a00b88197c42c73c/logs)
- **Withdrawal** event data: `0x0000000000000000000000007e6f6ccfe485a087f0f819eabfdbfb1a49b9767700000000000000000000000003e39ff2b379fbcd9284ab457113d82ff4dabbf40000a79057282732a2736064001cf4b4c56b84ec31ee000000000000000000000000000000000000000000000000000000000000000000000000000000000012000000000000000000000000000000000000000000000000000000000012071e0000000000000000000000000000000000000000000000000000000000000000`
- **outboxMsgId**: The last 32 bytes are `0000000000000000000000000000000000000000000000000000000000000000`, which is integer `0`.
- **outboxLevel**: The 32 bytes preceding those are `000000000000000000000000000000000000000000000000000000000012071e`, which is integer `1181470`.

The `parse_withdrawal_event` script allows to parse withdrawal event by transaction hash:
```shell
poetry run parse_withdrawal_event --tx-hash 0x51b9f37dbd18ca24b6c92f8685713f5d9767fbd1bdb3b8b8a00b88197c42c73c
```

After the withdrawal transaction is settled, users can retrieve the **commitment** and **proof**, which are necessary for the `execute_outbox_message` call. This involves making a call to the `global/block/head/helpers/proofs/outbox/{outbox_level}/messages` endpoint of the Rollup RPC Node. The `get_proof` script can be used to get this information:
```shell
poetry run get_proof --level 1181470 --index 0
```

Since the outbox message has settled on the L1 side, users can execute it by initiating the `execute_outbox_message` operation. Bellow a script `execute_outbox_message` used to finalize withdrawal for the test **FA1.2** token where acquired `--commitment` and `--proof` are provided:
```shell
poetry run execute_outbox_message --commitment src13PirA1PzjLWRYJvNFJL5V6tfdbhzmAgML2UtQHuojjjFv6ARsf --proof 03000251dd09b9e7c635d0a23a9a02c6268edcf2a3e74a9980cd8ce568612f8dd6886951dd09b9e7c635d0a23a9a02c6268edcf2a3e74a9980cd8ce568612f8dd688690005820764757261626c65d09177f273e0b4b3646d59424754cbc1a5368b75a201a7fa133551e39afbc25b3903746167c00800000004536f6d650003c02411766c7a6adf7e0f2f3a1608fdde179275ff6881c5712387bd21d401d9365c820576616c7565810370766d8107627566666572738205696e707574820468656164c00100066c656e677468c00100066f75747075740004820132810a6c6173745f6c6576656cc0040012072b0133810f76616c69646974795f706572696f64c00400013b0082013181086f7574626f7865730200013b00c07dc3e23702625eb3ecd86216a989553e1c95c9611f209e54fcefbf598f96b849019e68014f18c0dda898697e4f913f5af0017d501c8dd825696ea12f41168fd98a1243d3d4b0ae0127a40113bf0109f2c0f8d9aa295d40a87361a32f534a539c3304d87286125baf97fad5692209f5e1a40104cec02e83ddeb15e1e93ccc0b9eeaa17453499b0acccefb56831e4b57f084467da05b01027101013800b1c00a9ab9a19d10248b3810f3be53af9fa0012280024e512fce2dc30653e85b94f20054002a0017c0e68c3b7ad7e6f130881c5da857a5992daf77fb911cf6a94fb669f9eeb6a11a23000ec0e48a085d60ed9f24c26a44d4d9825d545098165a8aec0a518059431f1a564ea30005c0ba795987ddd0ec6bbcaef394f12f322b7fe73ee5b5f53c0b95466fc9b9e165270004c0f37ede9ba69186bc32eb2d85541fe28de505097a3755fb0eed841ffe20ae0ace820731313230323030820468656164c00100066c656e677468c0010007313138313437300003810468656164c001008208636f6e74656e7473810130c0d3000000cf00000000ca07070a000000160000a79057282732a2736064001cf4b4c56b84ec31ee07070a000000160125cf30bfba37ed7907f524f7b4eaf304e03d09760007070707000005090a0000005f05020000005907040100000010636f6e74726163745f616464726573730a0000001c050a0000001601aca11e3f7734be9b46df1642a7d5f7d66c7bf6e8000704010000000a746f6b656e5f747970650a0000000b0501000000054641312e3200120125cf30bfba37ed7907f524f7b4eaf304e03d097600000000087769746864726177066c656e677468c00101c0ad7442a17d12b3355594da691f158d37a0d44a7eae4a901f02b78819014efa26c05bc495b3831636f3f356a681b5e81bc47c250151048452fd09ab24f5550d6334c00bece9f7a7ae300e23932bbc972eeebc35b64f82ddbf3ca35f3f911fe96189e0c0760bdf103b185a9ca7234e7a0b631c7e5a2c45d4a86aad483758c36db0017107c008796620943748d80efa68d459f16839f0b95891b566ec5ccbfa80e120e0f420c0ebe4e9a10f88ea5b510233f903f66ee80a8faa3c212a5bddf27421cc0deb7362c09cfb372f3f6c6f9659e15f9a8a9b3b3d2824a707c426d43eb8711e83bf2252990134810d6d6573736167655f6c696d6974c002a401047761736dd0d535afa926245d335484f18570628898b144af4686673c5dbd96fa2431025e4d0012071e0000000000ca07070a000000160000a79057282732a2736064001cf4b4c56b84ec31ee07070a000000160125cf30bfba37ed7907f524f7b4eaf304e03d09760007070707000005090a0000005f05020000005907040100000010636f6e74726163745f616464726573730a0000001c050a0000001601aca11e3f7734be9b46df1642a7d5f7d66c7bf6e8000704010000000a746f6b656e5f747970650a0000000b0501000000054641312e3200120125cf30bfba37ed7907f524f7b4eaf304e03d097600000000087769746864726177
```
Here is an example of the finished [withdrawal](https://oxfordnet.tzkt.io/oo9FJdy6byfy6HoTqpnzs68eLrpfwu1aouvnM8bv6HCbjrsXPF2/228622).

## Compilation and Running Tests
1. Install Foundry by following the [installation guide](https://book.getfoundry.sh/getting-started/installation)

2. Install Solidity dependencies with Forge (part of the Foundry toolchain). Installation should be executed from the `etherlink` directory:
```shell
(cd etherlink && forge install)
```

Forge uses [git submodules](https://git-scm.com/book/en/v2/Git-Tools-Submodules) to manage dependencies. It is possible to check versions of the Solidity libraries installed by running `git submodule status`. Here are the versions used to compile contracts:
```shell
1d9650e951204a0ddce9ff89c32f1997984cef4d etherlink/lib/forge-std (v1.6.1)
fd81a96f01cc42ef1c9a5399364968d0e07e9e90 etherlink/lib/openzeppelin-contracts (v4.9.3)
```

### Compilation
#### 1. Tezos side:
To compile Tezos-side contracts, the LIGO compiler must be installed. The most convenient method is to use the Docker version of the LIGO compiler. Compilation of all contracts using the dockerized LIGO compiler can be initiated with the following command:
```shell
poetry run build_tezos_contracts
```
NOTE: This repository includes built Tezos side contracts which are located in the [tezos/build](tezos/build/) directory.

#### 2. Etherlink side:
To compile contracts on the Etherlink side, Foundry must be installed. To initiate the compilation, navigate to the [etherlink](etherlink/) directory and run `forge build`, or execute the following script from the root directory:
```shell
poetry run build_etherlink_contracts
```
NOTE: This repository includes built Etherlink side contracts which are located in the [etherlink/build](etherlink/build/) directory.

### Tests
#### 1. Tezos side:
The testing stack for Tezos contracts is based on Python and requires [poetry](https://python-poetry.org/), [pytezos](https://pytezos.org/), and [pytest](https://docs.pytest.org/en/7.4.x/) to be installed.

To run tests for the Tezos contracts, execute:
```shell
poetry run pytest tezos/tests
```

#### 2. Etherlink side:
The Etherlink contract tests use the [Foundry](https://book.getfoundry.sh/getting-started/installation) stack and are implemented in Solidity. To run these tests, navigate to the [etherlink](etherlink/) directory and run `forge test`, or execute the following script from the root directory:
```shell
poetry run etherlink_tests
```

### Linting
To perform linting, execute the following commands:

```shell
poetry run mypy .
poetry run ruff .
poetry run black .
```
