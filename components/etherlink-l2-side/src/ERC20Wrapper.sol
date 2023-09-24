// SPDX-License-Identifier: MIT
pragma solidity >=0.8.21;

import {ERC20} from "openzeppelin-contracts/token/ERC20/ERC20.sol";
import {BridgePrecompile} from "./BridgePrecompile.sol";

function hashToken(bytes20 ticketer, bytes memory identifier)
    pure
    returns (uint256)
{
    return uint256(keccak256(abi.encodePacked(ticketer, identifier)));
}

/**
 * @dev Interface of the ERC20Wrapper.
 * TODO: need to understand whether other methods need to be added here
 *       such as withdraw, deposit, etc.
 * TODO: need to understand should it be derived from IERC20 or not.
 */
interface IERC20Wrapper {
    /**
     * @dev Emitted when succesful deposit is made.
     */
    event Deposit(address indexed to, uint256 amount);

    /**
     * @dev Emitted when succesful withdraw is made.
     */
    event Withdraw(
        address indexed from, bytes32 indexed receiver, uint256 amount
    );
}

/**
 * ERC20 Wrapper is a ERC20 token contract which represents a L1 token
 * on L2.
 */
contract ERC20Wrapper is ERC20, IERC20Wrapper {
    uint256 private _tokenHash;
    address private _kernel;
    uint8 private _decimals;

    /**
     * @param ticketer_ whitelisted Tezos L1 address of the ticketer contract
     * @param identifier_ identifier of the L1 token (ticket id)
     * @param kernel_ address of the rollup kernel which is responsible for
     *        minting and burning tokens
     * @param name_ name of the token
     * @param symbol_ symbol of the token
     * @param decimals_ number of decimals of the token
     */
    constructor(
        bytes20 ticketer_,
        bytes memory identifier_,
        address kernel_,
        string memory name_,
        string memory symbol_,
        uint8 decimals_
    ) ERC20(name_, symbol_) {
        _tokenHash = hashToken(ticketer_, identifier_);
        _kernel = kernel_;
        _decimals = decimals_;
        this;
    }

    /**
     * Mints `amount` tokens for `to` address if provided `ticketer`
     * address and `identifier` are correct.
     *
     * Requirements:
     *
     * - only kernel address allowed to mint tokens.
     * - `tokenHash` must be equal to the token hash of the ticketer
     * and identifier used during deployment.
     */
    function deposit(address to, uint256 amount, uint256 tokenHash)
        public
        virtual
    {
        require(
            _kernel == _msgSender(),
            "ERC20Wrapper: only kernel allowed to mint tokens"
        );
        require(_tokenHash == tokenHash, "ERC20Wrapper: wrong token hash");
        _mint(to, amount);
        emit Deposit(to, amount);
    }

    /**
     * Burns `amount` tokens from the caller's account and creates
     * transaction to withdraw `amount` tokens from L2 to L1.
     *
     * Requirements:
     *
     * - `amount` must be less or equal to the balance of the caller.
     */
    function withdraw(bytes32 receiver, uint256 amount) public {
        address from = _msgSender();
        _burn(from, amount);
        BridgePrecompile bridge = BridgePrecompile(_kernel);
        bridge.withdraw(receiver, amount, _tokenHash);
        emit Withdraw(from, receiver, amount);
    }

    function decimals() public view virtual override returns (uint8) {
        return _decimals;
    }

    // TODO: getTicketer, getIdentifier, getRollupKernel
}
