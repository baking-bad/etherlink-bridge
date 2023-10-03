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

    struct TokenData {
        bytes20 ticketer;
        bytes identifier;
    }

    mapping(uint256 => TokenData) private _tokens;
    mapping(bytes32 => uint256) private _tickets;

    constructor(address bridge) {
        _bridge = bridge;
        _inboxLevel = 0;
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

    function getTicketerAndIdentifier(uint256 tokenHash)
        public
        view
        returns (bytes20, bytes memory)
    {
        TokenData memory tokenData = _tokens[tokenHash];
        return (tokenData.ticketer, tokenData.identifier);
    }

    // TODO: implement finalizeWithdraw which should be called by the
    //       BridgePrecompile contract and which should update the L2
    //       tickets ledger.
}
