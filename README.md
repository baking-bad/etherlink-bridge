# Etherlink FA Token Bridge

Smart contracts for an FA tokens bridge between Tezos and Etherlink, implementation of [TZIP-029](https://gitlab.com/baking-bad/tzip/-/blob/wip/029-etherlink-token-bridge/drafts/current/draft-etherlink-token-bridge/etherlink-token-bridge.md) standard:

- [**Ticketer**](tezos/contracts/ticketer/ticketer.mligo). Enables wrapping of **FA1.2** and **FA2** tokens into tickets. These tickets can then be sent to Etherlink using a permissionless ticket transport mechanism.
- [**TokenBridgeHelper**](tezos/contracts/token-bridge-helper/token-bridge-helper.mligo). Designed to allow users to transfer tickets even without the support for the **ticket_transfer** operation in the current Tezos infrastructure. The Token Bridge Helper implementation focused on **FA1.2** and **FA2** tokens only.
- [**ERC20Proxy**](etherlink/src/ERC20Proxy.sol). An **ERC20** contract that implements the ERC20 Proxy [deposit interface](https://gitlab.com/baking-bad/tzip/-/blob/wip/029-etherlink-token-bridge/drafts/current/draft-etherlink-token-bridge/etherlink-token-bridge.md#l2-proxy-deposit-interface) and [withdraw interface](https://gitlab.com/baking-bad/tzip/-/blob/wip/029-etherlink-token-bridge/drafts/current/draft-etherlink-token-bridge/etherlink-token-bridge.md#l2-proxy-withdraw-interface).

## Setup
1. Install [Poetry](https://python-poetry.org/) if not already installed:
```shell
curl -sSL https://install.python-poetry.org | python3 -
```

2. Install all dependencies with:
```shell
poetry install
```

3. To rebuild and test contracts it is also required to install Foundry and LIGO, see [compilation and running tests](#compilation-and-running-tests).

> [!TIP]
> There is a `Dockerfile` allowing to run scripts in [docker](#running-in-docker).

> [!TIP]
> To fund you wallets and pay for gas in test networks there are: [Tezos faucet](https://faucet.ghostnet.teztnets.com/) and [Etherlink faucet](https://faucet.etherlink.com/).

## Bridging a new Token
To establish a new bridge between Tezos and Etherlink for existing `FA1.2` and `FA2` tokens there is a `bridge_token` command that would deploy three contracts:
- Ticketer contract on the Tezos side,
- ERC20 Proxy contract on the Etherlink side,
- Token Bridge Helper on the Tezos side.

Here is an example of the command to deploy Token bridge contracts for the test `FA1,2` token:
```shell
poetry run bridge_token \
    --token-address KT19P1nbGzGnumMfRHcLNuyQUdcuwjpBfsCU \
    --token-type FA1.2 \
    --token-decimals 8 \
    --token-symbol "TST" \
    --token-name "Test Token"
```

> [!NOTE]
> To find out the details of how the FA Bridge contracts deployed and communicate with each other, see: [bridge configuration](docs/README.md#bridge-configuration).

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
> The version of `forge` used to build contracts is `forge 0.2.0 (20b3da1 2024-07-02T00:18:52.435480726Z)`.

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

## Running in Docker
There is a `Dockerfile` provided that may simplify the installation of dependencies required to run **bridge_token**, **deposit** and **withdraw** scripts. Here is an example of how to use it:

### Build a docker image by running:
```shell
docker build -t etherlink-bridge .
```

Then it is possible to execute commands within a docker container, just make sure to provide all necessary variables directly to the scripts. It is also possible to set up environment variables for private keys, nodes and other parameters.

### Bridge token example:
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

### Deposit example:
```shell
docker run --rm etherlink-bridge deposit \
    --token-bridge-helper-address KT1KiiUkGKFqNAK2BoAGi2conhGoGwiXcMTR \
    --amount 77 \
    --receiver-address 0x7e6f6CCFe485a087F0F819eaBfDBfb1a49b97677 \
    --smart-rollup-address sr1HpyqJ662dWTY8GWffhHYgN2U26funbT1H \
    --tezos-private-key edsk4XG4QyAj19dr78NNGH6dpXBtTnkmMdAkM9w5tUTCHaUP1pJaD5 \
    --tezos-rpc-url "https://rpc.tzkt.io/parisnet/"
```

### Withdraw example:
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
