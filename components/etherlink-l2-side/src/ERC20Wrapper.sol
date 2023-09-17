// SPDX-License-Identifier: MIT
pragma solidity >=0.8.21;

import {ERC20} from "openzeppelin-contracts/token/ERC20/ERC20.sol";

contract ERC20Wrapper is ERC20 {
    // TODO: find a way to provide some metadata during deployment
    //       [maybe create some kind of ERC20Factory?]
    constructor() ERC20("Name", "TODO: Symbol") {
        // TODO: configure Ticketer
        // TODO: configure Rollup Kernel address (zero address?)
        this;
    }

    // TODO: this mint function is only for testing purposes
    //       need to find a way to mint tokens without public mint function
    function mint(address to, uint256 amount) public virtual {
        _mint(to, amount);
    }

    // TODO: implement Deposit function similar to mint
    //       params:
    //           ticketer: Tezos L1 address of the ticketer contract
    //           identifier: identifier of the L1 token (ticket payload bytes)
    //           to: L2 address which should receive token
    //           amount: amount which should be minted for `to` address
    //       Only rollup kernel address must be able to call this function

    // TODO: implement Withdraw function similar to burn
    //       params:
    //           ticketer: Tezos L1 address of the ticketer contract
    //           identifier: identifier of the L1 token (ticket payload bytes)
    //           amount: amount which should be burned from sender
    //           receiver: Tezos L1 address which should receive ticket
    //       Should burn token and call bridge precompile (rollup kernel)
}
