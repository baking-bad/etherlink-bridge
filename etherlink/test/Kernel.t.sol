// SPDX-License-Identifier: MIT
pragma solidity ^0.8.21;

import {BaseTest} from "./Base.t.sol";
import {hashTicket} from "../src/ERC20Proxy.sol";
import {IWithdrawalEvent} from "../src/IWithdrawalEvent.sol";
import {IDepositEvent} from "../src/IDepositEvent.sol";

contract KernelTest is BaseTest, IWithdrawalEvent, IDepositEvent {
    function test_ShouldIncreaseTicketBalanceOfTokenIfDepositSucceed() public {
        kernel.inboxDeposit(address(token), alice, 100, ticketer, content);
        assertEq(kernel.getBalance(ticketer, content, address(token)), 100);
        assertEq(kernel.getBalance(ticketer, content, alice), 0);
    }

    function test_ShouldDecreaseTicketBalanceOfTokenIfWithdrawSucceed()
        public
    {
        assertEq(kernel.getBalance(ticketer, content, address(token)), 0);
        kernel.inboxDeposit(address(token), alice, 100, ticketer, content);
        assertEq(kernel.getBalance(ticketer, content, address(token)), 100);
        assertEq(kernel.getBalance(ticketer, content, alice), 0);
        vm.prank(alice);
        kernel.withdraw(address(token), receiver, 40, ticketer, content);
        assertEq(kernel.getBalance(ticketer, content, address(token)), 60);
    }

    function test_RevertWhen_WithdrawMoreThanTicketBalance() public {
        kernel.inboxDeposit(address(token), bob, 1, ticketer, content);
        assertEq(kernel.getBalance(ticketer, content, address(token)), 1);
        vm.prank(address(alice));
        vm.expectRevert("Kernel: ticket balance is not enough");
        kernel.withdraw(address(token), receiver, 2, ticketer, content);
    }

    function test_WithdrawCallsTokenBurn() public {
        kernel.inboxDeposit(address(token), alice, 100, ticketer, content);
        assertEq(token.balanceOf(alice), 100);
        bytes memory expectedData =
            abi.encodeCall(token.withdraw, (alice, 50, ticketHash));
        vm.expectCall(address(token), expectedData);
        vm.prank(alice);
        kernel.withdraw(address(token), receiver, 50, ticketer, content);
        assertEq(token.balanceOf(alice), 50);
    }

    function test_InboxDepositCallsTokenMint() public {
        bytes memory expectedData =
            abi.encodeCall(token.deposit, (alice, 71, ticketHash));
        vm.expectCall(address(token), expectedData);
        kernel.inboxDeposit(address(token), alice, 71, ticketer, content);
    }

    function test_ShouldEmitDepositEventOnDeposit() public {
        // Checking that emited indexed data is the same in all topics:
        vm.expectEmit(true, true, true, true);
        uint256 inboxLevel = 0;
        uint256 inboxMsgId = 0;
        emit Deposit(
            ticketHash, address(token), bob, 100, inboxLevel, inboxMsgId
        );
        kernel.inboxDeposit(address(token), bob, 100, ticketer, content);
    }

    function test_ShouldEmitWithdrawEventOnWithdraw() public {
        kernel.inboxDeposit(address(token), bob, 100, ticketer, content);
        vm.prank(bob);
        // Checking that emited indexed data is the same in all topics:
        vm.expectEmit(true, true, true, true);
        uint256 outboxLevel = 0;
        uint256 outboxMsgId = 0;
        emit Withdrawal(
            ticketHash,
            bob,
            address(token),
            receiver22,
            100,
            outboxLevel,
            outboxMsgId
        );
        kernel.withdraw(address(token), receiver, 100, ticketer, content);
    }

    // TODO: test_ShouldIncreaseTicketBalanceOfReceiverIfWrongTokenAddress
    //       -- however this logic is not implemented in kernel
}
