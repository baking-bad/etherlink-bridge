// SPDX-License-Identifier: MIT
pragma solidity >=0.8.21;

contract FAWithdrawalPrecompile {
    function withdraw(
        address ticketOwner,
        bytes calldata receiver,
        uint256 amount,
        bytes22 ticketer,
        bytes calldata content
    ) public {}
}

contract NativeWithdrawalPrecompile {
    function withdraw_base58(string memory target) public payable {}
}

contract BulkWithdrawal {
    event LogEvent(uint256 num);

    address fa_precompile;
    address native_precompile;

    constructor(address fa_precompile_, address native_precompile_) {
        fa_precompile = fa_precompile_;
        native_precompile = native_precompile_;
    }

    function withdraw(
        address ticketOwner,
        bytes memory routing_info,
        uint256 amount,
        bytes22 ticketer,
        bytes memory content
    ) public {
        emit LogEvent(0);
        FAWithdrawalPrecompile precompile =
            FAWithdrawalPrecompile(fa_precompile);
        precompile.withdraw(
            ticketOwner, routing_info, amount, ticketer, content
        );
        emit LogEvent(1);
    }

    function withdraw_base58(string memory target) public payable {
        emit LogEvent(0);
        NativeWithdrawalPrecompile precompile =
            NativeWithdrawalPrecompile(native_precompile);
        precompile.withdraw_base58{value: msg.value}(target);
        emit LogEvent(2);
    }

    /*
    function withdraw(
        address ticketOwner,
        bytes memory routing_info,
        uint256 amount,
        bytes22 ticketer,
        bytes memory content
    ) public {
        IWithdrawFA precompile = IWithdrawFA(fa_precompile);
        precompile.withdraw(
            ticketOwner, routing_info, amount, ticketer, content
        );
        (bool success,) = fa_precompile.call(
            abi.encodeWithSignature(
                "withdraw(address,bytes,uint256,bytes22,bytes)",
                ticketOwner,
                routing_info,
                amount,
                ticketer,
                content
            )
        );
        require(success, "Call to target contract failed");
    }

    function withdraw_base58(string memory target) public payable {
        (bool success,) = native_precompile.call{value: msg.value}(
            abi.encodeWithSignature("withdraw_base58(string)", target)
        );
        require(success, "Call to target contract failed");
    }
    */
}
