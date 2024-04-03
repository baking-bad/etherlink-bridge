// SPDX-License-Identifier: MIT
pragma solidity >=0.8.21;

/**
 * @notice Interface for emitting Withdrawal events as part of an L2 to L1 token bridge.
 */
interface IWithdrawalEvent {
    /**
     * @notice Indicates a withdrawal from L2 to L1.
     * @param ticketHash Unique identifier for the withdrawal ticket.
     * @param sender Address that initiated the withdrawal request.
     * @param ticketOwner Owner of the ticket on L2, could be the sender or an L2 proxy contract.
     * @param receiver Encoded L1 address designated to receive the withdrawn amount.
     * @param amount Amount of tokens being withdrawn.
     * @param outboxLevel The level at which the withdrawal was processed in the rollup outbox.
     * @param outboxMsgId Unique identifier for the withdrawal message within its level, facilitating tracking.
     */
    event Withdrawal(
        uint256 indexed ticketHash,
        address sender,
        address ticketOwner,
        bytes22 receiver,
        uint256 amount,
        uint256 outboxLevel,
        uint256 outboxMsgId
    );
}
