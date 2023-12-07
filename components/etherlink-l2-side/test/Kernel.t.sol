// SPDX-License-Identifier: MIT
pragma solidity ^0.8.21;

import {BaseTest} from "./Base.t.sol";
import {hashToken} from "../src/ERC20Wrapper.sol";
import {IWithdrawEvent} from "../src/IWithdrawEvent.sol";
import {IDepositEvent} from "../src/IDepositEvent.sol";

contract KernelTest is BaseTest, IWithdrawEvent, IDepositEvent {
    function test_ShouldIncreaseTicketBalanceOfTokenIfDepositSucceed() public {
        kernel.inboxDeposit(address(token), alice, 100, ticketer, identifier);
        assertEq(kernel.getBalance(ticketer, identifier, address(token)), 100);
        assertEq(kernel.getBalance(ticketer, identifier, alice), 0);
    }

    function test_ShouldDecreaseTicketBalanceOfTokenIfWithdrawSucceed()
        public
    {
        assertEq(kernel.getBalance(ticketer, identifier, address(token)), 0);
        kernel.inboxDeposit(address(token), alice, 100, ticketer, identifier);
        assertEq(kernel.getBalance(ticketer, identifier, address(token)), 100);
        assertEq(kernel.getBalance(ticketer, identifier, alice), 0);
        vm.prank(alice);
        kernel.withdraw(address(token), receiver, 40, ticketer, identifier);
        assertEq(kernel.getBalance(ticketer, identifier, address(token)), 60);
    }

    function test_RevertWhen_WithdrawMoreThanTicketBalance() public {
        kernel.inboxDeposit(address(token), bob, 1, ticketer, identifier);
        assertEq(kernel.getBalance(ticketer, identifier, address(token)), 1);
        vm.prank(address(alice));
        vm.expectRevert("Kernel: ticket balance is not enough");
        kernel.withdraw(address(token), receiver, 2, ticketer, identifier);
    }

    function test_WithdrawCallsTokenBurn() public {
        kernel.inboxDeposit(address(token), alice, 100, ticketer, identifier);
        assertEq(token.balanceOf(alice), 100);
        bytes memory expectedData =
            abi.encodeCall(token.burn, (alice, 50, tokenHash));
        vm.expectCall(address(token), expectedData);
        vm.prank(alice);
        kernel.withdraw(address(token), receiver, 50, ticketer, identifier);
        assertEq(token.balanceOf(alice), 50);
    }

    function test_InboxDepositCallsTokenMint() public {
        bytes memory expectedData =
            abi.encodeCall(token.mint, (alice, 71, tokenHash));
        vm.expectCall(address(token), expectedData);
        kernel.inboxDeposit(address(token), alice, 71, ticketer, identifier);
    }

    function test_ShouldEmitDepositEventOnDeposit() public {
        // Checking that emited indexed data is the same in all topics:
        vm.expectEmit(true, true, true, true);
        uint256 inboxLevel = 0;
        uint256 depositIdx = 0;
        emit Deposit(
            tokenHash, address(token), bob, 100, inboxLevel, depositIdx
        );
        kernel.inboxDeposit(address(token), bob, 100, ticketer, identifier);
    }

    function test_ShouldEmitWithdrawEventOnWithdraw() public {
        kernel.inboxDeposit(address(token), bob, 100, ticketer, identifier);
        vm.prank(bob);
        // Checking that emited indexed data is the same in all topics:
        vm.expectEmit(true, true, true, true);
        uint256 withdrawalIdx = 0;
        uint256 outboxLevel = 0;
        emit Withdraw(
            tokenHash,
            bob,
            address(token),
            receiver,
            100,
            outboxLevel,
            withdrawalIdx
        );
        kernel.withdraw(address(token), receiver, 100, ticketer, identifier);
    }

    // TODO: test_ShouldIncreaseTicketBalanceOfReceiverIfWrongTokenAddress
    //       -- however this logic is not implemented in kernel
}
