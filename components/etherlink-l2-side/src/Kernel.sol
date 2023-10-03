// SPDX-License-Identifier: MIT
pragma solidity >=0.8.21;

import {ERC20Wrapper, hashToken} from "./ERC20Wrapper.sol";
import {BridgePrecompile} from "./BridgePrecompile.sol";
import "forge-std/console.sol";

function hashTicketOwner(
    bytes20 ticketer,
    bytes memory identifier,
    address owner
) pure returns (bytes32) {
    return keccak256(abi.encodePacked(ticketer, identifier, owner));
}

struct TokenData {
    bytes20 ticketer;
    bytes identifier;
}

/**
 * The Kernel is mock contract that used to represent the rollup kernel
 * on L2 side, which is resposible for bridging tokens between L1 and L2.
 * Kernel address is the one who should be allowed to mint new tokens in
 * ERC20Wrapper contract.
 * The Kernel is responsible for maintainig the ledger of L2 tickets
 */
contract Kernel {
    address private _bridge;
    uint256 private _inboxLevel;
    uint256 private _inboxMessageId;

    mapping(uint256 => TokenData) private _tokens;
    mapping(bytes32 => uint256) private _tickets;

    constructor() {
        // TODO: does this initialization required, or uint256 already
        //       initializes to the zero value?
        _inboxLevel = 0;
    }

    function setBridge(address bridge) public {
        _bridge = bridge;
    }

    function inboxDeposit(
        address wrapper,
        address receiver,
        uint256 amount,
        bytes20 ticketer,
        bytes memory identifier
    ) public {
        ERC20Wrapper token = ERC20Wrapper(wrapper);
        BridgePrecompile bridge = BridgePrecompile(_bridge);

        uint256 tokenHash = hashToken(ticketer, identifier);
        bytes32 depositId =
            keccak256(abi.encodePacked(_inboxMessageId, _inboxLevel));

        _inboxMessageId += 1;
        _tokens[tokenHash] = TokenData(ticketer, identifier);

        // TODO: is it possible to make try/catch block with deposit
        //       transaction and if it fails move tickets from wrapper
        //       to receiver?

        bytes32 ticketWrapper = hashTicketOwner(ticketer, identifier, wrapper);
        _tickets[ticketWrapper] += amount;
        bridge.deposit(depositId, wrapper, receiver, amount, tokenHash);
        token.deposit(receiver, amount, tokenHash);
    }

    function getBalance(
        bytes20 ticketer,
        bytes memory identifier,
        address owner
    ) public view returns (uint256) {
        bytes32 ticket = hashTicketOwner(ticketer, identifier, owner);
        return _tickets[ticket];
    }

    function getTokenData(uint256 tokenHash)
        public
        view
        returns (TokenData memory)
    {
        TokenData memory tokenData = _tokens[tokenHash];
        return tokenData;
    }

    function finalizeWithdraw(
        uint256 tokenHash,
        address wrapper,
        uint256 amount
    ) public {
        // TODO: assert only bridge precompile ca call this
        bytes20 ticketer = _tokens[tokenHash].ticketer;
        bytes memory identifier = _tokens[tokenHash].identifier;
        bytes32 ticketWrapper = hashTicketOwner(ticketer, identifier, wrapper);
        uint256 ticketBalance = _tickets[ticketWrapper];
        if (ticketBalance < amount) {
            revert("Kernel: ticket balance is not enough");
        }
        _tickets[ticketWrapper] -= amount;
        // NOTE: here the withdraw outbox message should be sent to L1
    }
}
