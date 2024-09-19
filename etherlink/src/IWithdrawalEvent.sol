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
     * @param proxy Encoded L1 proxy address assigned to route the withdrawal.
     * @param amount Amount of tokens being withdrawn.
     * @param withdrawalId Unique identifier for the withdrawal message, facilitating tracking.
     */
    event Withdrawal(
        uint256 indexed ticketHash,
        address sender,
        address ticketOwner,
        bytes22 receiver,
        bytes22 proxy,
        uint256 amount,
        uint256 withdrawalId
    );
}
