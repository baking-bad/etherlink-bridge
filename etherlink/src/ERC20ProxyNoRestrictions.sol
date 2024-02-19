// SPDX-License-Identifier: MIT
pragma solidity >=0.8.21;

import {ERC20} from "openzeppelin-contracts/token/ERC20/ERC20.sol";

function hashTicket(bytes22 ticketer, bytes memory content)
    pure
    returns (uint256)
{
    return uint256(keccak256(abi.encodePacked(ticketer, content)));
}

/**
 * ERC20 Proxy is a ERC20 token contract which represents a L1 token
 * on L2. This is the version of ERC20Proxy without any restrictions on
 * minting and burning tokens.
 */
contract ERC20ProxyNoRestrictions is ERC20 {
    uint256 private _ticketHash;
    address private _kernel;
    uint8 private _decimals;

    /**
     * Params ticketer_, content_ and kernel_ not used in this version
     * of the contract.
     * @param ticketer_ address of the L1 ticketer contract
     * @param content_ content of the L1 ticket
     * @param kernel_ address of the rollup kernel
     * @param name_ name of the token
     * @param symbol_ symbol of the token
     * @param decimals_ number of decimals of the token
     */
    constructor(
        bytes22 ticketer_,
        bytes memory content_,
        address kernel_,
        string memory name_,
        string memory symbol_,
        uint8 decimals_
    ) ERC20(name_, symbol_) {
        _ticketHash = hashTicket(ticketer_, content_);
        _kernel = kernel_;
        _decimals = decimals_;
        this;
    }

    /**
     * Mints `value` tokens amount for `account` address.
     * No restrictions.
     */
    function deposit(address account, uint256 value, uint256) public {
        _mint(account, value);
    }

    /**
     * Burns `value` tokens amount from the `account` address.
     * No restrictions.
     */
    function withdraw(address account, uint256 value, uint256) public {
        _burn(account, value);
    }

    function decimals() public view override returns (uint8) {
        return _decimals;
    }

    function getTicketHash() public view returns (uint256) {
        return _ticketHash;
    }
}
