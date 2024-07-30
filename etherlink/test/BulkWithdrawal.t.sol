// SPDX-License-Identifier: MIT
pragma solidity ^0.8.21;

import {BaseTest} from "./Base.t.sol";
import {BulkWithdrawal} from "../src/BulkWithdrawal.sol";
import {ERC20Proxy, hashTicket} from "../src/ERC20Proxy.sol";
import "forge-std/console.sol";

contract BulkWithdrawalTest is BaseTest {
    BulkWithdrawal public bulkWithdrawal;

    function test_WithdrawalFromSmartContractSucceed() public {
        uint256 batchSize = 3;
        bulkWithdrawal =
            new BulkWithdrawal(address(kernel), address(kernel), batchSize);
        kernel.inboxDeposit(
            address(token), address(bulkWithdrawal), 100, ticketer, content
        );
        assertEq(token.totalSupply(), 100);

        bytes memory expectedData = abi.encodeCall(
            kernel.withdraw, (address(token), receiver, 12, ticketer, content)
        );
        vm.expectCall(address(kernel), expectedData);
        vm.prank(bob);
        // bulk withdrawal makes 3 withdrawals in one transaction:
        bulkWithdrawal.withdraw(address(token), receiver, 12, ticketer, content);
        assertEq(token.balanceOf(address(bulkWithdrawal)), 100 - 12 * batchSize);
        assertEq(token.totalSupply(), 100 - 12 * batchSize);
    }

    function test_WithdrawalNativeSucceed() public {
        uint256 batchSize = 5;
        bulkWithdrawal =
            new BulkWithdrawal(address(kernel), address(kernel), batchSize);
        string memory target = "someTarget";
        startHoax(bob, 1000000);
        (bool success,) = address(bulkWithdrawal).call{value: 500}("");
        require(success, "Failed to deposit ether");

        bytes memory expectedData =
            abi.encodeCall(kernel.withdraw_base58, target);
        vm.expectCall(address(kernel), expectedData);
        bulkWithdrawal.withdraw_base58{value: 100}(target);
        assertEq(address(kernel).balance, 500);
        console.logUint(address(bob).balance);
    }
}