## Bridge L2 side contracts

This project features an ERC20 Proxy Contract, essential for the functioning of a bridge between Tezos and Etherlink networks. Additionally, the project includes a rollup logic mock and tests covering token `deposit` and `withdraw` processes. Smart contracts written in solidity, the project leverages the [Foundry framework](https://book.getfoundry.sh/) for contract compilation, test execution, and interactions with contracts within the L2 network.

## Usage
### Test

```shell
$ forge test
```

### Interact
Before running any commands, ensure that the following environment variables are set in your `.env` file:
- `L2_MANAGER_PUBLIC_KEY`
- `L2_MANAGER_PRIVATE_KEY`
- `L2_ALICE_PUBLIC_KEY`
- `L2_ALICE_PRIVATE_KEY`
- `L2_BORIS_PUBLIC_KEY`
- `L2_BORIS_PRIVATE_KEY`

#### Fund and Initialize Accounts
To fund and initialize accounts, run:
```shell
$ make fund_accounts
```

#### Deploy Proxy ERC20 Contract
For deploying the Proxy ERC20 contract, use:
```shell
$ make deploy_proxy_erc20
```

#### Execute Withdrawal Procedure
> NOTE: For successful execution of the withdrawal process, ensure that the ERC20 Proxy is deployed and received a successful deposit from L1.

To execute the withdrawal procedure, run:
```shell
$ make play_withdraw
```

