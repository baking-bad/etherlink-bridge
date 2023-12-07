// SPDX-License-Identifier: MIT
pragma solidity ^0.8.21;

import {Test} from "forge-std/Test.sol";
import {ERC20Proxy, hashTicket} from "../src/ERC20Proxy.sol";
import {Kernel} from "../src/Kernel.sol";

contract BaseTest is Test {
    ERC20Proxy public token;
    Kernel public kernel;
    address public alice = vm.addr(0x1);
    address public bob = vm.addr(0x2);
    uint256 public ticketHash;
    bytes22 public ticketer = bytes22("some ticketer");
    bytes22 public wrongTicketer = bytes22("some other ticketer");
    bytes public content = abi.encodePacked("forged content");
    bytes public wrongContent = abi.encodePacked("another forged content");
    bytes public receiver = bytes("some receiver % entrypoint");

    function setUp() public {
        vm.label(alice, "Alice");
        vm.label(bob, "Bob");
        kernel = new Kernel();
        token = new ERC20Proxy(
            ticketer,
            content,
            address(kernel),
            "Token",
            "TKN",
            18
        );
        ticketHash = hashTicket(ticketer, content);
    }
}
