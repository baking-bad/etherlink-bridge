// SPDX-License-Identifier: MIT
pragma solidity ^0.8.21;

import {Test} from "forge-std/Test.sol";
import {ERC20Wrapper} from "../src/ERC20Wrapper.sol";
import {BridgePrecompile} from "../src/BridgePrecompile.sol";

contract CounterTest is Test {
    ERC20Wrapper public token;
    BridgePrecompile public bridge;
    address public alice;
    address public bob;

    function setUp() public {
        alice = vm.addr(0x1);
        bob = vm.addr(0x2);
        vm.label(alice, "Alice");
        vm.label(bob, "Bob");
        bridge = new BridgePrecompile();
        token = new ERC20Wrapper("some tickiter", 0, address(bridge));
    }

    function test_BridgeCanMintToken() public {
        assertEq(token.balanceOf(alice), 0);
        bridge.deposit(address(token), alice, 100, "some tickiter", 0);
        assertEq(token.balanceOf(alice), 100);
    }

    function test_RevertWhen_AliceTriesMintToken() public {
        vm.prank(alice);
        vm.expectRevert("ERC20Wrapper: must have minter role to mint");
        token.deposit(alice, 100, "some tickiter", 0);
    }

    function test_RevertWhen_TicketerIsWrong() public {
        vm.expectRevert("ERC20Wrapper: wrong ticketer");
        bridge.deposit(address(token), alice, 100, "some other tickiter", 0);
    }

    function test_RevertWhen_IdentifierIsWrong() public {
        vm.expectRevert("ERC20Wrapper: wrong identifier");
        bridge.deposit(address(token), alice, 100, "some tickiter", 1);
    }
}
