// SPDX-License-Identifier: MIT
pragma solidity >=0.8.21;

contract BridgePrecompile {
    constructor() {
        this;
    }

    function withdraw(string memory receiver, uint256 amount, string memory ticketer, uint256 identifier) public {}
}
