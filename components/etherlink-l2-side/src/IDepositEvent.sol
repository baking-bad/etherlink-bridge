// SPDX-License-Identifier: MIT
pragma solidity >=0.8.21;

/**
 * @dev Interface of the contract which can emit Deposit event.
 */
interface IDepositEvent {
    /**
     * @dev Emitted when succesful deposit is made.
     */
    // TODO: add address of ERC contract?
    // TODO: add tokenHash
    event Deposit(
        bytes32 indexed depositId, address indexed to, uint256 amount
    );
}
