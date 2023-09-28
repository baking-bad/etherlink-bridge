// SPDX-License-Identifier: MIT
pragma solidity >=0.8.21;

/**
 * @dev Interface of the contract which can emit Withdraw event.
 */
interface IWithdraw {
    /**
     * @dev Emitted when succesful withdraw is made.
     */
    event Withdraw(
        bytes32 indexed withdrawalId,
        uint256 messageId,
        uint256 outboxLevel,
        address indexed sender,
        bytes20 indexed receiver,
        uint256 amount
    );
}
