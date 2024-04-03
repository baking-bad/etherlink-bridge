// SPDX-License-Identifier: MIT
pragma solidity >=0.8.21;

import {ERC20} from "openzeppelin-contracts/token/ERC20/ERC20.sol";

function hashTicket(bytes22 ticketer, bytes memory content)
    pure
    returns (uint256 ticketHash)
{
    ticketHash = uint256(keccak256(abi.encodePacked(ticketer, content)));
}

/**
 * ERC20 Proxy is a ERC20 token contract which represents a L1 token
 * on L2.
 */
contract ERC20Proxy is ERC20 {
    uint256 private immutable _ticketHash;
    address private immutable _kernel;
    uint8 private immutable _decimals;

    /**
     * @param ticketer_ address of the L1 ticketer contract which tickets are
     *        allowed to be minted by this ERC20Proxy
     * @param content_ content of the L1 ticket allowed to be minted by
     *        this ERC20Proxy
     * @param kernel_ address of the rollup kernel which has rights for
     *        the minting and burning tokens
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
    modifier onlyKernel() {
        require(
            _kernel == _msgSender(),
            "ERC20Proxy: only kernel allowed to deposit / withdraw tokens"
        );
        _;
    }

    /**
     * Checks if the provided `ticketHash` is equal to the ticket hash
     * of the ticketer and content set during token deployment.
     */
    modifier onlyAllowedTicketHash(uint256 ticketHash) {
        require(_ticketHash == ticketHash, "ERC20Proxy: wrong ticket hash");
        _;
    }

    /**
     * Mints given `amount` of tokens for `receiver` address if provided
     * `ticketHash` is correct.
     *
     * Requirements:
     *
     * - only kernel address allowed to mint tokens.
     * - `ticketHash` must be equal to the ticket hash of the ticketer
     * and identifier used during deployment.
     */
    function deposit(address receiver, uint256 amount, uint256 ticketHash)
        public
        onlyKernel
        onlyAllowedTicketHash(ticketHash)
    {
        _mint(receiver, amount);
    }

    /**
     * Burns `amount` of tokens amount from the `sender` address if provided
     * `ticketHash` is correct.
     *
     * Requirements:
     *
     * - only kernel address allowed to burn tokens.
     * - `ticketHash` must be equal to the token hash of the ticketer
     *    and content set during deployment.
     * - `amount` must be less or equal to the balance of the caller.
     */
    function withdraw(address sender, uint256 amount, uint256 ticketHash)
        public
        onlyKernel
        onlyAllowedTicketHash(ticketHash)
    {
        _burn(sender, amount);
    }

    function decimals() public view override returns (uint8) {
        return _decimals;
    }

    function getTicketHash() public view returns (uint256) {
        return _ticketHash;
    }
}
