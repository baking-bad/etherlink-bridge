// SPDX-License-Identifier: MIT
pragma solidity >=0.8.21;

import {IWithdrawalEvent} from "./IWithdrawalEvent.sol";
import {IDepositEvent} from "./IDepositEvent.sol";
import {ERC20Proxy, hashTicket} from "./ERC20Proxy.sol";

/**
 * @notice Calculates the hash of the ticket including the owner's address to
 * uniquely identify the L2 ticket owner pair.
 * @param ticketer The L1 ticketer address in its forged form.
 * @param content The ticket content as a micheline expression in its forged form.
 * @param owner The address of the L2 ticket owner.
 * @return The calculated ticket hash including the owner as a bytes32.
 */
function hashTicketOwner(bytes22 ticketer, bytes memory content, address owner)
    pure
    returns (bytes32)
{
    return keccak256(abi.encodePacked(ticketer, content, owner));
}

/**
 * @title Kernel Mock
 * @notice Represents the rollup kernel on L2, responsible for bridging
 * tokens between L1 and L2.
 * This mock kernel allows for the minting of new tokens in ERC20Proxy
 * contracts and manages L2 tickets, emitting `Deposit` and `Withdraw` events.
 */
contract KernelMock is IWithdrawalEvent, IDepositEvent {
    uint256 private _rollupId;
    uint256 private _inboxLevel;
    uint256 private _inboxMsgId;
    uint256 private _withdrawalId;

    mapping(bytes32 => uint256) private _tickets;

    /**
     * @notice Increases the L2 ticket balance for a given owner.
     * @param ticketer The L1 ticketer address in its forged form.
     * @param content The ticket content in its forged form.
     * @param owner The address of the ticket owner.
     * @param amount The amount by which to increase the ticket balance.
     */
    function _increaseTicketsBalance(
        bytes22 ticketer,
        bytes memory content,
        address owner,
        uint256 amount
    ) internal {
        bytes32 ticketOwner = hashTicketOwner(ticketer, content, owner);
        _tickets[ticketOwner] += amount;
    }

    /**
     * @notice Decreases the L2 ticket balance for a given owner.
     * @param ticketer The L1 ticketer address in its forged form.
     * @param content The ticket content in its forged form.
     * @param owner The address of the ticket owner.
     * @param amount The amount by which to decrease the ticket balance.
     */
    function _decreaseTicketsBalance(
        bytes22 ticketer,
        bytes memory content,
        address owner,
        uint256 amount
    ) internal {
        bytes32 ticketOwner = hashTicketOwner(ticketer, content, owner);
        uint256 ticketBalance = _tickets[ticketOwner];
        if (ticketBalance < amount) {
            revert("KernelMock: ticket balance is not enough");
        }
        _tickets[ticketOwner] -= amount;
    }

    /**
     * @notice Gets the balance of L2 tickets for a specified owner.
     * @param ticketer The L1 ticketer address in its forged form.
     * @param content The ticket content in its forged form.
     * @param owner The address of the ticket owner.
     * @return The balance of tickets for the specified owner.
     */
    function getBalance(bytes22 ticketer, bytes memory content, address owner)
        public
        view
        returns (uint256)
    {
        bytes32 ticket = hashTicketOwner(ticketer, content, owner);
        return _tickets[ticket];
    }

    /**
     * @notice Emulates the deposit operation processed during inbox dispatch in the Kernel.
     * @param ticketReceiver The ERC20Proxy contract address.
     * @param receiver The address to receive the minted tokens.
     * @param amount The amount of tokens to mint.
     * @param ticketer The L1 ticketer address in its forged form.
     * @param identifier The ticket content in its forged form.
     */
    function inboxDeposit(
        address ticketReceiver,
        address receiver,
        uint256 amount,
        bytes22 ticketer,
        bytes memory identifier
    ) public {
        ERC20Proxy proxyToken = ERC20Proxy(ticketReceiver);
        uint256 ticketHash = hashTicket(ticketer, identifier);

        // NOTE: in the Kernel implementation if proxyToken.deposit fails, then
        // ticket added to the receiver instead of the ticketReceiver:
        _increaseTicketsBalance(ticketer, identifier, ticketReceiver, amount);

        emit Deposit(
            ticketHash,
            ticketReceiver,
            receiver,
            amount,
            _inboxLevel,
            _inboxMsgId
        );

        _inboxMsgId += 1;
        proxyToken.deposit(receiver, amount, ticketHash);
    }

    /**
     * @notice Emulates the withdraw operation processed during outbox dispatch in the Kernel.
     * @param ticketOwner The ERC20Proxy contract address.
     * @param routingInfo The encoded routing info with L1 receiver and router address.
     * @param amount The amount of tokens to withdraw.
     * @param ticketer The L1 ticketer address in forged form.
     * @param content The ticket content in forged form.
     */
    function withdraw(
        address ticketOwner,
        bytes memory routingInfo,
        uint256 amount,
        bytes22 ticketer,
        bytes memory content
    ) public {
        ERC20Proxy proxyToken = ERC20Proxy(ticketOwner);
        address sender = msg.sender;
        uint256 ticketHash = hashTicket(ticketer, content);
        _decreaseTicketsBalance(ticketer, content, ticketOwner, amount);

        require(routingInfo.length >= 22, "Routing info is too short");
        bytes22 receiver22 = bytes22(routingInfo);

        // NOTE: proxy22 is not parsed from routingInfo and hardcoded:
        bytes22 proxy22 = bytes22("0000000000000000000000");

        emit Withdrawal(
            ticketHash,
            sender,
            ticketOwner,
            receiver22,
            proxy22,
            amount,
            _withdrawalId
        );

        _withdrawalId += 1;
        proxyToken.withdraw(sender, amount, ticketHash);
        // NOTE: here the withdraw outbox message should be sent to L1
    }

    function withdraw_base58(string memory target) public payable {}
}
