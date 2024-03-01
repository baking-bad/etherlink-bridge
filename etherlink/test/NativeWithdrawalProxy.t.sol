// SPDX-License-Identifier: MIT
pragma solidity ^0.8.21;

import {BaseTest} from "./Base.t.sol";
import {NativeWithdrawalProxy} from "../src/NativeWithdrawalProxy.sol";

contract NativeWithdrawalProxyTest is BaseTest {
    NativeWithdrawalProxy public nativeWithdrawalProxy;

    function test_WithdrawalNativeSucceed() public {
        nativeWithdrawalProxy = new NativeWithdrawalProxy(address(kernel));
        string memory target = "tz1_some_target_as_a_string";
        startHoax(bob, 1000000);
        bytes memory expectedData =
            abi.encodeCall(kernel.withdraw_base58, target);
        vm.expectCall(address(kernel), expectedData);
        nativeWithdrawalProxy.withdraw_base58{value: 100}(target);
        assertEq(address(kernel).balance, 100);
    }
}
