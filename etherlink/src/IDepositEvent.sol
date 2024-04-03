// SPDX-License-Identifier: MIT
pragma solidity >=0.8.21;

/**
 * @notice Interface for emitting Deposit events in an L1 to L2 token bridge.
 */
interface IDepositEvent {
    /**
     * @notice Indicates a deposit from L1 to L2.
     * @param ticketHash Unique identifier for the deposited ticket.
     * @param ticketOwner L2 owner who receiving the ticket.
     * @param receiver L2 address receiving the tokens.
     * @param amount Amount of tokens deposited.
     * @param inboxLevel The level at which the deposit was included in the rollup inbox.
     * @param inboxMsgId Inbox message identifier in the rollup inbox at the given level.
     */
    event Deposit(
        uint256 indexed ticketHash,
        address ticketOwner,
        address receiver,
        uint256 amount,
        uint256 inboxLevel,
        uint256 inboxMsgId
    );
}
