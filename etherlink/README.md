## Bridge L2 side contracts

This project features an ERC20 Proxy Contract, essential for the functioning of a bridge between Tezos and Etherlink networks. Additionally, the project includes a rollup logic mock and tests covering token `deposit` and `withdraw` processes. Smart contracts written in solidity, the project leverages the [Foundry framework](https://book.getfoundry.sh/) for contract compilation, test execution, and interactions with contracts within the L2 network.

## Usage
### Test

```shell
forge test
```

### Compile
```shell
forge build
```

### Interact

#### Fund and Initialize Accounts
To fund and initialize accounts, run:
TODO: add example with account initialization

#### Deploy Proxy ERC20 Contract
For deploying the Proxy ERC20 contract, use:
TODO: add example with ERC20 deploy

#### Execute Withdrawal Procedure
> NOTE: For successful execution of the withdrawal process, ensure that the ERC20 Proxy is deployed and received a successful deposit from L1.

To execute the withdrawal procedure, run:
TODO: add example
