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
 * on L2.
 */
contract ERC20Proxy is ERC20 {
    uint256 private _ticketHash;
    address private _kernel;
    uint8 private _decimals;

    /**
     * @param ticketer_ address of the L1 ticketer contract which tickets are
     *        allowed to be minted by this ERC20Proxy
     * @param content_ content of the L1 ticket allowed to be minted by
     *        this ERC20Proxy
     * @param kernel_ address of the rollup kernel which is responsible for
     *        minting and burning tokens
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
     * Checks if the sender is the kernel address.
     */
    function _requireSenderIsKernel() internal view {
        require(
            _kernel == _msgSender(),
            "ERC20Proxy: only kernel allowed to deposit / withdraw tokens"
        );
    }

    /**
     * Checks if the provided `ticketHash` is equal to the ticket hash
     * of the ticketer and content set during token deployment.
     */
    function _requireTicketHash(uint256 ticketHash) internal view {
        require(_ticketHash == ticketHash, "ERC20Proxy: wrong ticket hash");
    }

    /**
     * Mints `value` tokens amount for `account` address if provided
     * `ticketHash` is correct.
     *
     * Requirements:
     *
     * - only kernel address allowed to mint tokens.
     * - `ticketHash` must be equal to the ticket hash of the ticketer
     * and identifier used during deployment.
     */
    function deposit(address account, uint256 value, uint256 ticketHash)
        public
    {
        _requireSenderIsKernel();
        _requireTicketHash(ticketHash);
        _mint(account, value);
    }

    /**
     * Burns `value` tokens amount from the `account` address if provided
     * `ticketHash` is correct.
     *
     * Requirements:
     *
     * - only kernel address allowed to burn tokens.
     * - `ticketHash` must be equal to the token hash of the ticketer
     *    and content set during deployment.
     * - `amount` must be less or equal to the balance of the caller.
     */
    function withdraw(address account, uint256 value, uint256 ticketHash)
        public
    {
        _requireSenderIsKernel();
        _requireTicketHash(ticketHash);
        _burn(account, value);
    }

    function decimals() public view override returns (uint8) {
        return _decimals;
    }

    function getTicketHash() public view returns (uint256) {
        return _ticketHash;
    }
}
