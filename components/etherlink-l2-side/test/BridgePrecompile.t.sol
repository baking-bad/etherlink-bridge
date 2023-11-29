// SPDX-License-Identifier: MIT
pragma solidity ^0.8.21;

import {BaseTest} from "./Base.t.sol";
import {IDepositEvent} from "../src/IDepositEvent.sol";
import {IWithdrawEvent} from "../src/IWithdrawEvent.sol";

contract BridgePrecompileTest is BaseTest, IDepositEvent, IWithdrawEvent {
    function test_ShouldEmitDepositEventOnDeposit() public {
        // All topics are indexed, so we check all of them and
        // that data the same (last argument is true):
        vm.expectEmit(true, true, true, true);
        bytes32 depositId = keccak256(abi.encodePacked(uint256(0), uint256(0)));
        emit Deposit(depositId, tokenHash, address(token), bob, 100);
        kernel.inboxDeposit(address(token), bob, 100, ticketer, identifier);
    }

    function test_ShouldEmitWithdrawEventOnWithdraw() public {
        kernel.inboxDeposit(address(token), bob, 100, ticketer, identifier);
        vm.prank(bob);
        // All topics are indexed, so we check them all
        // and check that data the same:
        vm.expectEmit(true, true, true, true);
        uint256 messageId = 0;
        uint256 outboxLevel = 0;
        bytes32 withdrawalId =
            keccak256(abi.encodePacked(messageId, outboxLevel));
        emit Withdraw(
            withdrawalId,
            tokenHash,
            address(token),
            messageId,
            outboxLevel,
            bob,
            receiver,
            100
        );
        kernel.withdraw(address(token), receiver, 100, tokenHash);
    }

    function test_RevertWhen_DepositCalledNotFromKernel() public {
        vm.prank(alice);
        bytes32 depositId = keccak256(abi.encodePacked(uint256(0), uint256(0)));
        vm.expectRevert(
            "BridgePrecompile: only kernel allowed to deposit and withdraw tokens"
        );
        bridge.deposit(depositId, address(token), bob, 10000, tokenHash);
    }

    function test_RevertWhen_WithdrawCalledNotByKernel() public {
        kernel.inboxDeposit(address(token), bob, 10, ticketer, identifier);
        vm.prank(bob);
        vm.expectRevert(
            "BridgePrecompile: only kernel allowed to deposit and withdraw tokens"
        );
        bridge.withdraw(address(token), bob, receiver, 1, tokenHash);
    }
}
