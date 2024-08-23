# Etherlink FA Token Bridge

The tools in this repository help you bridge tokens between Tezos layer 1 and Etherlink.
You can use them to set up bridging for any Tezos token that is compliant with the FA standard, versions 1.2 or 2.
For more information about the FA standards, see [Token standards](https://docs.tezos.com/architecture/tokens#token-standards) on docs.tezos.com.

The tools also help you submit bridging transactions, both for bridging tokens from Tezos to Etherlink (depositing) and for bridging tokens from Etherlink to Tezos (withdrawing).

For information on how this bridge works, see [Bridging FA tokens between Tezos layer 1 and Etherlink](https://docs.etherlink.com/building-on-etherlink/bridging-fa) in the Etherlink documentation.

You can use the tool to bridge tokens between Tezos Mainnet and Etherlink Mainnet and between Tezos test networks and Etherlink Testnet.

## Prerequisites

To bridge tokens in this way, you need:

- An FA-compliant smart contract deployed to Tezos.
You can use your own contract or the tool can deploy a sample contract for you.

- A Tezos wallet with enough tez to pay for the Tezos transaction fees.
See [Installing and funding a wallet](https://docs.tezos.com/developing/wallet-setup) on docs.tezos.com.
If you are using a test network, you can find faucets that provide free tez at https://teztnets.com, such as the Ghostnet faucet at https://faucet.ghostnet.teztnets.com/.

- An EVM-compatible wallet with enough Etherlink XTZ to pay for the Etherlink transaction fees.
See [Using your wallet](https://docs.etherlink.com/get-started/using-your-wallet) in the Etherlink documentation for a list of compatible wallets and information about connecting your wallet to Etherlink.
If you are using Etherlink Testnet, you can get free XTZ at the [Etherlink faucet](https://faucet.etherlink.com/).

## Contracts

The bridging process relies on smart contracts that convert tokens to [tickets](https://docs.tezos.com/smart-contracts/data-types/complex-data-types#tickets) and transfer the tickets between Tezos and Etherlink.
These contracts are an implementation of the [TZIP-029](https://gitlab.com/baking-bad/tzip/-/blob/wip/029-etherlink-token-bridge/drafts/current/draft-etherlink-token-bridge/etherlink-token-bridge.md) standard for bridging between Tezos and Etherlink.

Each FA token needs its own copy of these contracts for you to bridge that token:

- **Ticketer**: This Tezos contract stores FA1.2 and FA2.0 tokens and issues tickets that represent those tokens, similar to a wrapped token.
The ticket includes the type and number of tokens that it represents and the address of the ticketer contract.
For an example, see the [`ticketer.mligo`](tezos/contracts/ticketer/ticketer.mligo) contract.

- **Token bridge helper**: This Tezos contract accepts requests to bridge tokens, uses the ticketer contract to get tickets for them, and sends the tickets to Etherlink.
For an example, see [`token-bridge-helper.mligo`](tezos/contracts/token-bridge-helper/token-bridge-helper.mligo).

- **ERC-20 proxy**: This Etherlink contract accepts the tickets and mints ERC-20 tokens that are equivalent to the Tezos tokens.
This contract implements the ERC20 Proxy [deposit interface](https://gitlab.com/baking-bad/tzip/-/blob/wip/029-etherlink-token-bridge/drafts/current/draft-etherlink-token-bridge/etherlink-token-bridge.md#l2-proxy-deposit-interface) and [withdraw interface](https://gitlab.com/baking-bad/tzip/-/blob/wip/029-etherlink-token-bridge/drafts/current/draft-etherlink-token-bridge/etherlink-token-bridge.md#l2-proxy-withdraw-interface).
For an example, see [`ERC20Proxy.sol`](etherlink/src/ERC20Proxy.sol).

FA2.1 tokens have built-in ticket capabilities, so they do not require a ticketer or token bridge helper contract.

For information about how these contracts communicate with each other, see [bridge configuration](docs/README.md#bridge-configuration).

## Setup

Follow these steps to set up the tool for local use.
You can run the tool directly or build a Docker container that runs it.

### Local installation

1. Install [Poetry](https://python-poetry.org/) if it is not already installed by running this command:

   ```shell
   curl -sSL https://install.python-poetry.org | python3 -
   ```

2. Clone this repository and go into its directory.

3. Install the tool's dependencies by running this command:

   ```shell
   poetry install
   ```

4. Optional: Rebuild and test the contracts locally as described in [compilation and running tests](#compilation-and-running-tests).

Then you can run commands by running `poetry run` followed by the command name, such as `poetry run bridge_token`.

### Docker installation

1. Clone this repository and go into its directory.

2. Build the Docker image by running this command:

   ```bash
   docker build -t etherlink-bridge .
   ```

Now you can run commands by prefixing them with `docker run --rm etherlink-bridge`, such as `docker run --rm etherlink-bridge bridge_token`.

## Setting up bridging for a token

This tool's `bridge_token` command deploys the bridging contracts for a single token.
If you have multiple token types, as in FA2 multi-asset tokens, you must run this command once for each type of token to bridge.
The tool also has separate commands for deploying the contracts individually if you want to deploy the contracts one at a time.

Here is an example of the command to deploy the bridging contracts for an FA1.2 token:

```shell
poetry run bridge_token \
    --token-address KT1SekNYSaT3sWp55nhmratovWN4Mvfc6cfQ \
    --token-type FA1.2 \
    --token-id=0 \
    --token-decimals 0 \
    --token-symbol "TST12" \
    --token-name "Test FA1.2 Token" \
    --tezos-private-key ${TEZOS_WALLET_PRIVATE_KEY} \
    --tezos-rpc-url "https://rpc.ghostnet.teztnets.com" \
    --etherlink-private-key ${ETHERLINK_WALLET_PRIVATE_KEY} \
    --etherlink-rpc-url "https://node.ghostnet.etherlink.com" \
    --skip-confirm
```

Here is an example of the command to deploy the bridging contracts for an FA2 token:

```shell
poetry run bridge_token \
    --token-address KT19P1nbGzGnumMfRHcLNuyQUdcuwjpBfsCU \
    --token-type FA2 \
    --token-id=0 \
    --token-decimals 8 \
    --token-symbol "TST" \
    --token-name "TST Token" \
    --tezos-private-key ${TEZOS_WALLET_PRIVATE_KEY} \
    --tezos-rpc-url "https://rpc.ghostnet.teztnets.com" \
    --etherlink-private-key ${ETHERLINK_WALLET_PRIVATE_KEY} \
    --etherlink-rpc-url "https://node.ghostnet.etherlink.com" \
    --skip-confirm
```

The `bridge_token` command accepts these arguments:

- `--token-address`: The Tezos address of the token contract, starting with `KT1`
- `--token-type`: The token standard: `FA1.2` or `FA2`
- `--token-id`: The ID of the token to bridge; for FA1.2 contracts, which have only one token, use `0`
- `--token-decimals`: The number of decimal places used in the token quantity
- `--token-symbol`: An alphanumeric symbol for the token
- `--token-name`: A name for the token
- `--tezos-private-key`: The private key for the Tezos account
- `--tezos-rpc-url`: The URL to a Tezos RPC server to send the transactions to; for RPC servers on test networks, see https://teztnets.com
- `--etherlink-private-key`: The private key for the EVM-compatible wallet that is connected to Etherlink
- `--etherlink-rpc-url`: The URL to the Etherlink RPC server to send the transactions to; see [Network information](https://docs.etherlink.com/get-started/network-information) on docs.etherlink.com
- `--skip-confirm`: Skip the confirmation step; required if you are running the command via Docker



## Deposit
To deposit tokens from the Tezos side to the Etherlink side there is a `deposit` command:
```shell
poetry run deposit \
    --token-bridge-helper-address KT1KiiUkGKFqNAK2BoAGi2conhGoGwiXcMTR \
    --amount 77 \
    --receiver-address 0x7e6f6CCFe485a087F0F819eaBfDBfb1a49b97677 \
    --smart-rollup-address sr1HpyqJ662dWTY8GWffhHYgN2U26funbT1H
```

> [!NOTE]
> For details on how the FA Bridge deposit works, see: [Deposit](docs/README.md#deposit).

## Withdrawal
To initiate withdrawal on the Etherlink side there is a `withdraw` command:
```shell
poetry run withdraw \
    --erc20-proxy-address 0x8AaBCd16bA3346649709e4Ff93E5c6Df18D8c2Ed \
    --amount 17 \
    --tezos-side-router-address KT199szFcgpAc46ZwsDykNBCa2t6u32xUyY7 \
    --ticketer-address-bytes 0x0106431674bc137dcfe537765838b1864759d6f79200 \
    --ticket-content-bytes 0x0707000005090a000000a505020000009f07040100000010636f6e74726163745f616464726573730a000000244b54313950316e62477a476e756d4d665248634c4e75795155646375776a70426673435507040100000008646563696d616c730a0000000138070401000000046e616d650a0000000a5465737420546f6b656e0704010000000673796d626f6c0a000000035453540704010000000a746f6b656e5f747970650a000000054641312e32 \
    --receiver-address tz1ekkzEN2LB1cpf7dCaonKt6x9KVd9YVydc
```

> [!NOTE]
> To get `--ticketer-address-bytes` and `--ticket-content-bytes` parameters for the ticketer contract, there is a `get_ticketer_command` command: `poetry run get_ticketer_params --ticketer-address KT199szFcgpAc46ZwsDykNBCa2t6u32xUyY7`.

> [!IMPORTANT]
> Withdrawal required to be finalized on Tezos side after commitment with witdhrawal has been settled. See more here: [Withdrawal process](docs/README.md#withdrawal-process).

## Compilation and Running Tests
1. Install Foundry by following the [installation guide](https://book.getfoundry.sh/getting-started/installation)
> [!NOTE]
> Please note that the version of `forge` used to build contracts is `forge 0.2.0 (ca67d15 2023-08-02T00:16:51.291393754Z)`. Build results for newer versions may differ from the artifacts added to the build directory.

2. Install LIGO with the instructions at https://ligolang.org.

3. Install Solidity dependencies with Forge (part of the Foundry toolchain). Installation should be executed from the `etherlink` directory:
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

> [!NOTE]
> This repository includes built Tezos side contracts which are located in the [tezos/build](tezos/build/) directory.

#### 2. Etherlink side:
To compile contracts on the Etherlink side, Foundry must be installed. To initiate the compilation, navigate to the [etherlink](etherlink/) directory and run `forge build`, or execute the following script from the root directory:
```shell
poetry run build_etherlink_contracts
```

> [!NOTE]
> This repository includes built Etherlink side contracts which are located in the [etherlink/build](etherlink/build/) directory.

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

## Linting
To perform linting, execute the following commands:

```shell
poetry run mypy .
poetry run ruff .
poetry run black .
```

## Example commands

### Deploy bridge contracts for a token

```shell
docker run --rm etherlink-bridge bridge_token \
    --token-address KT19P1nbGzGnumMfRHcLNuyQUdcuwjpBfsCU \
    --token-type FA1.2 \
    --token-decimals 8 \
    --token-symbol "TST" \
    --token-name "Test Token" \
    --tezos-private-key edsk4XG4QyAj19dr78NNGH6dpXBtTnkmMdAkM9w5tUTCHaUP1pJaD5 \
    --tezos-rpc-url "https://rpc.tzkt.io/parisnet/" \
    --etherlink-private-key f463e320ed1bd1cd833e29efc383878f34abe6b596e5d163f51bb8581de6f8b8 \
    --etherlink-rpc-url "https://etherlink.dipdup.net" \
    --skip-confirm
```

### Bridge tokens from Tezos to Etherlink

```shell
docker run --rm etherlink-bridge deposit \
    --token-bridge-helper-address KT1KiiUkGKFqNAK2BoAGi2conhGoGwiXcMTR \
    --amount 77 \
    --receiver-address 0x7e6f6CCFe485a087F0F819eaBfDBfb1a49b97677 \
    --smart-rollup-address sr1HpyqJ662dWTY8GWffhHYgN2U26funbT1H \
    --tezos-private-key edsk4XG4QyAj19dr78NNGH6dpXBtTnkmMdAkM9w5tUTCHaUP1pJaD5 \
    --tezos-rpc-url "https://rpc.tzkt.io/parisnet/"
```

### Bridge tokens from Etherlink to Tezos

```shell
docker run --rm etherlink-bridge withdraw \
    --erc20-proxy-address 0x8AaBCd16bA3346649709e4Ff93E5c6Df18D8c2Ed \
    --amount 17 \
    --tezos-side-router-address KT199szFcgpAc46ZwsDykNBCa2t6u32xUyY7 \
    --ticketer-address-bytes 0x0106431674bc137dcfe537765838b1864759d6f79200 \
    --ticket-content-bytes 0x0707000005090a000000a505020000009f07040100000010636f6e74726163745f616464726573730a000000244b54313950316e62477a476e756d4d665248634c4e75795155646375776a70426673435507040100000008646563696d616c730a0000000138070401000000046e616d650a0000000a5465737420546f6b656e0704010000000673796d626f6c0a000000035453540704010000000a746f6b656e5f747970650a000000054641312e32 \
    --receiver-address tz1ekkzEN2LB1cpf7dCaonKt6x9KVd9YVydc \
    --etherlink-private-key f463e320ed1bd1cd833e29efc383878f34abe6b596e5d163f51bb8581de6f8b8 \
    --etherlink-rpc-url "https://etherlink.dipdup.net"
```
