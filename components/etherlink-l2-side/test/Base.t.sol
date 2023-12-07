// SPDX-License-Identifier: MIT
pragma solidity ^0.8.21;

import {Test} from "forge-std/Test.sol";
import {ERC20Wrapper, hashToken} from "../src/ERC20Wrapper.sol";
import {Kernel} from "../src/Kernel.sol";

contract BaseTest is Test {
    ERC20Wrapper public token;
    Kernel public kernel;
    address public alice = vm.addr(0x1);
    address public bob = vm.addr(0x2);
    uint256 public tokenHash;
    bytes22 public ticketer = bytes22("some ticketer");
    bytes22 public wrongTicketer = bytes22("some other ticketer");
    bytes public identifier = abi.encodePacked("forged identifier");
    bytes public wrongIdentifier = abi.encodePacked("another forged identifier");
    bytes public receiver = bytes("some receiver % entrypoint");

    function setUp() public {
        vm.label(alice, "Alice");
        vm.label(bob, "Bob");
        kernel = new Kernel();
        token = new ERC20Wrapper(
            ticketer,
            identifier,
            address(kernel),
            "Token",
            "TKN",
            18
        );
        tokenHash = hashToken(ticketer, identifier);
    }
}
