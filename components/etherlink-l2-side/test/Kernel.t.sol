// SPDX-License-Identifier: MIT
pragma solidity ^0.8.21;

import {BaseTest} from "./Base.t.sol";
import {hashToken} from "../src/ERC20Wrapper.sol";
import {TokenData} from "../src/Kernel.sol";

contract KernelTest is BaseTest {
    function test_ShouldIncreaseTicketBalanceOfTokenIfDepositSucceed() public {
        kernel.inboxDeposit(address(token), alice, 100, ticketer, identifier);
        assertEq(kernel.getBalance(ticketer, identifier, address(token)), 100);
        assertEq(kernel.getBalance(ticketer, identifier, alice), 0);
    }

    // TODO: test_ShouldIncreaseTicketBalanceOfReceiverIfWrongTokenAddress

    function test_ShouldAddTokenDataIfDepositSucceed() public {
        kernel.inboxDeposit(address(token), alice, 100, ticketer, identifier);
        uint256 tokenHash = hashToken(ticketer, identifier);
        TokenData memory tokenData = kernel.getTokenData(tokenHash);
        assertEq(tokenData.ticketer, ticketer);
        assertEq(tokenData.identifier, identifier);
    }

    function test_ShouldDecreaseTicketBalanceOfTokenIfWithdrawSucceed()
        public
    {
        assertEq(kernel.getBalance(ticketer, identifier, address(token)), 0);
        kernel.inboxDeposit(address(token), alice, 100, ticketer, identifier);
        assertEq(kernel.getBalance(ticketer, identifier, address(token)), 100);
        assertEq(kernel.getBalance(ticketer, identifier, alice), 0);
        vm.prank(alice);
        token.withdraw(receiver, 40);
        assertEq(kernel.getBalance(ticketer, identifier, address(token)), 60);
    }

    function test_RevertWhen_WithdrawMoreThanTicketBalance() public {
        kernel.inboxDeposit(address(token), bob, 1, ticketer, identifier);
        assertEq(kernel.getBalance(ticketer, identifier, address(token)), 1);
        vm.prank(address(bridge));
        vm.expectRevert("Kernel: ticket balance is not enough");
        kernel.finalizeWithdraw(tokenHash, address(token), 2);
    }
}
