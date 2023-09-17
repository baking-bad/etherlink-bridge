// SPDX-License-Identifier: MIT
pragma solidity ^0.8.21;

import {Test} from "forge-std/Test.sol";
import {ERC20Wrapper} from "../src/ERC20Wrapper.sol";

contract CounterTest is Test {
    ERC20Wrapper public token;
    address public alice;
    address public bob;

    function setUp() public {
        alice = vm.addr(0x1);
        vm.label(alice, "Alice");
        bob = vm.addr(0x2);
        vm.label(bob, "Bob");
        token = new ERC20Wrapper();
        token.mint(alice, 100);
    }

    function test_Transfer() public {
        assertEq(token.balanceOf(alice), 100);
        vm.prank(alice);
        token.transfer(bob, 50);
        assertEq(token.balanceOf(alice), 50);
        assertEq(token.balanceOf(bob), 50);
    }
}
