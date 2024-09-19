// SPDX-License-Identifier: MIT
pragma solidity >=0.8.21;

/**
 * @title DepositTester
 * @notice This contract is used to test the logic triggered when sending
 * (XTZ) to the contract. Specifically, it is used to verify whether the Kernel
 * will trigger the logic inside `receive()` during deposit execution or not.
 */
contract DepositTester {
    address public xtzPrecompile;
    string public target;

    /**
     * @notice Constructs the DepositTester contract.
     * @param xtzPrecompile_ The address of the XTZ precompile contract.
     * @param target_ The recipient address for XTZ on L1.
     */
    constructor(address xtzPrecompile_, string memory target_) {
        xtzPrecompile = xtzPrecompile_;
        target = target_;
    }

    /**
     * @notice Fallback function triggered when the contract receives XTZ.
     * @dev Encodes a call to the withdrawal precompile contract with the
     * specified receiver string, then forwards the received XTZ along with
     * the encoded data.
     */
    receive() external payable {
        bytes memory data =
            abi.encodeWithSignature("withdraw_base58(string)", target);
        (bool success,) = xtzPrecompile.call{value: msg.value}(data);
        require(success, "Call to target contract failed");
    }
}
