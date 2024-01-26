// SPDX-License-Identifier: MIT
pragma solidity >=0.8.21;

contract BatchCallHelper {
    function _makeCallMultipleTimes(
        address callee,
        bytes memory data,
        uint256 value,
        uint256 times
    ) internal {
        uint256 counter = 1;
        while (counter <= times) {
            (bool success,) = callee.call{value: value}(data);
            require(success, "Call to target contract failed");
            counter += 1;
        }
    }
}
