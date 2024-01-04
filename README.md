# Etherlink Bridge

This repository presents an implementation of a bridge between Tezos and Etherlink.

For the Tezos side, it features smart contracts written in CameLIGO, including  `Ticketer` for wrapping legacy `FA` tokens into tickets, and `TicketHelper` enabling users to transfer tickets without the need for the currently unsupported `ticket_transfer` operation in Tezos infrastructure. Tezos testing and build stack: `poetry` + `pytezos` + `pytest`.

On the Etherlink side, the repository contains `solidity` contracts, including `ERC20Proxy` which used to be deployed on L2 to bridge tokens. Tests for Etherlink contracts are written in `solidity`, leveraging the `foundry` stack for both testing and contract compilation.

The implementation adheres to the [TZIP-029](https://gitlab.com/baking-bad/tzip/-/blob/wip/029-etherlink-token-bridge/drafts/current/draft-etherlink-token-bridge/etherlink-token-bridge.md) standard.

## Project structure:
    * tezos, LIGO, pytezos, tests, build contracts directory
    * etherlink, solidity, foundry, tests, build contracts directory
    * scripts to interact on python, poetry

## Interact with bridge
- TODO: add link to colab
- TODO: replay all commands here and add description to each of them

### Configuring bridge

#### Deploy token

#### Deploy ticketer

#### Deploy ticket helper

### Deposit

### Withdraw

## Compilation and run tests
### Install dependencies
```console
poetry install
```

### Linting
```console
poetry run mypy .
poetry run ruff .
poetry run black .
```

### Tests
```console
poetry run pytest
poetry run etherlink_tests
```

### Compilation
```console
poetry run build_tezos_contracts
poetry run build_etherlink_contracts
```
