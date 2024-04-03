// SPDX-License-Identifier: MIT
pragma solidity >=0.8.21;

import {ERC20} from "openzeppelin-contracts/token/ERC20/ERC20.sol";

/**
 * @notice Calculates the hash of the ticket.
 * @param ticketer The L1 ticketer address in its forged form.
 * @param content The ticket content as a micheline expression in its forged form.
 * @return ticketHash The calculated ticket hash as a uint256.
 */
function hashTicket(bytes22 ticketer, bytes memory content)
    pure
    returns (uint256 ticketHash)
{
    ticketHash = uint256(keccak256(abi.encodePacked(ticketer, content)));
}

/**
 * @title ERC20 Proxy
 * @notice A ERC20 token contract representing a L1 token on L2.
 */
contract ERC20Proxy is ERC20 {
    uint256 private immutable _ticketHash;
    address private immutable _kernel;
    uint8 private immutable _decimals;

    /**
     * @notice Constructs the ERC20Proxy.
     * @param ticketer_ Address of the L1 ticketer contract which tickets are
     * allowed to be minted by this ERC20Proxy.
     * @param content_ Content of the L1 ticket allowed to be minted by
     * this ERC20Proxy.
     * @param kernel_ Address of the rollup kernel which has rights for
     * the minting and burning tokens.
     * @param name_ Name of the token.
     * @param symbol_ Symbol of the token.
     * @param decimals_ Number of decimals of the token.
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
     * @notice Ensures the caller is the kernel address.
     */
    modifier onlyKernel() {
        require(
            _kernel == _msgSender(),
            "ERC20Proxy: only kernel allowed to deposit / withdraw tokens"
        );
        _;
    }

    /**
     * @notice Ensures the ticket hash equal to the one that was calculated
     * during deployment.
     * @param ticketHash The ticket hash to validate.
     */
    modifier onlyAllowedTicketHash(uint256 ticketHash) {
        require(_ticketHash == ticketHash, "ERC20Proxy: wrong ticket hash");
        _;
    }

    /**
     * @notice Mints tokens to a receiver.
     * @notice Only callable by the kernel and fails if ticketHash is incorrect.
     * @param receiver The address to receive the minted tokens.
     * @param amount The amount of tokens to mint.
     * @param ticketHash The ticket hash to check against.
     */
    function deposit(address receiver, uint256 amount, uint256 ticketHash)
        public
        onlyKernel
        onlyAllowedTicketHash(ticketHash)
    {
        _mint(receiver, amount);
    }

    /**
     * @notice Burns tokens from a sender address.
     * @notice Only callable by the kernel and fails if ticketHash is incorrect.
     * @param sender The address from which tokens will be burned.
     * @param amount The amount of tokens to burn.
     * @param ticketHash The ticket hash to check against.
     */
    function withdraw(address sender, uint256 amount, uint256 ticketHash)
        public
        onlyKernel
        onlyAllowedTicketHash(ticketHash)
    {
        _burn(sender, amount);
    }

    /**
     * @notice Returns the number of decimals the token uses.
     * @return The number of decimals for the token.
     */
    function decimals() public view override returns (uint8) {
        return _decimals;
    }

    /**
     * @notice Returns the ticket hash.
     * @return The ticket hash as a uint256.
     */
    function getTicketHash() public view returns (uint256) {
        return _ticketHash;
    }
}
