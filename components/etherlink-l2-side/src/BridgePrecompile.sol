// SPDX-License-Identifier: MIT
pragma solidity >=0.8.21;

import {ERC20Wrapper} from "./ERC20Wrapper.sol";

contract BridgePrecompile {
    constructor() {
        this;
    }

    function deposit(
        address wrapper,
        address to,
        uint256 amount,
        uint256 tokenHash
    ) public {
        ERC20Wrapper token = ERC20Wrapper(wrapper);
        token.deposit(to, amount, tokenHash);
    }

    function withdraw(bytes20 receiver, uint256 amount, uint256 tokenHash)
        public
    {}
}
