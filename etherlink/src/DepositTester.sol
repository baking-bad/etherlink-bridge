// SPDX-License-Identifier: MIT
pragma solidity >=0.8.21;

// TODO: consider remove or move this logic to another contract

// TODO: describe this is simple contract to test that deposit
// allows to make some work with the target contract or not
contract DepositTester {
    address public xtzPrecompile;
    string public target;

    constructor(address xtzPrecompile_, string memory target_) {
        xtzPrecompile = xtzPrecompile_;
        target = target_;
    }

    receive() external payable {
        bytes memory data =
            abi.encodeWithSignature("withdraw_base58(string)", target);
        (bool success,) = xtzPrecompile.call{value: msg.value}(data);
        require(success, "Call to target contract failed");
    }
}
