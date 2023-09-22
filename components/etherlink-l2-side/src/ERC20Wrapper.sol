// SPDX-License-Identifier: MIT
pragma solidity >=0.8.21;

import {ERC20} from "openzeppelin-contracts/token/ERC20/ERC20.sol";
import {AccessControlEnumerable} from
    "openzeppelin-contracts/access/AccessControlEnumerable.sol";
import {Context} from "openzeppelin-contracts/utils/Context.sol";
import {BridgePrecompile} from "./BridgePrecompile.sol";

function hashToken(string memory ticketer, uint256 identifier)
    pure
    returns (uint256)
{
    return uint256(keccak256(abi.encodePacked(ticketer, identifier)));
}

/**
 * ERC20 Wrapper is a ERC20 token contract which represents a L1 token
 * on L2.
 */
contract ERC20Wrapper is Context, AccessControlEnumerable, ERC20 {
    bytes32 public constant MINTER_ROLE = keccak256("MINTER_ROLE");
    uint256 private _tokenHash;
    address private _kernel;

    /**
     * @param ticketer_ whitelisted Tezos L1 address of the ticketer contract
     * @param identifier_ identifier of the L1 token (ticket id)
     * @param kernel_ address of the rollup kernel which is responsible for
     *        minting and burning tokens
     */
    constructor(string memory ticketer_, uint256 identifier_, address kernel_)
        ERC20("TODO: Name", "TODO: Symbol")
    {
        _tokenHash = hashToken(ticketer_, identifier_);
        _kernel = kernel_;
        _setupRole(DEFAULT_ADMIN_ROLE, kernel_);
        _setupRole(MINTER_ROLE, kernel_);
        // TODO: find a way to provide some metadata during deployment
        //       [maybe create some kind of ERC20Factory?]
        this;
    }

    /**
     * @dev Mints `amount` tokens for `to` address if provided `ticketer`
     * address and `identifier` are correct.
     *
     * Requirements:
     *
     * - the caller must have the `MINTER_ROLE`.
     * - `tokenHash` must be equal to the token hash of the ticketer
     * and identifier used during deployment.
     */
    function deposit(address to, uint256 amount, uint256 tokenHash)
        public
        virtual
    {
        require(
            hasRole(MINTER_ROLE, _msgSender()),
            "ERC20Wrapper: must have minter role to mint"
        );
        require(_tokenHash == tokenHash, "ERC20Wrapper: wrong token hash");
        _mint(to, amount);
    }

    /**
     * Burns `amount` tokens from the caller's account and creates
     * transaction to withdraw `amount` tokens from L2 to L1.
     *
     * Requirements:
     *
     * - `amount` must be less or equal to the balance of the caller.
     */
    function withdraw(string memory receiver, uint256 amount) public {
        _burn(_msgSender(), amount);
        BridgePrecompile bridge = BridgePrecompile(_kernel);
        bridge.withdraw(receiver, amount, _tokenHash);
    }

    // TODO: getTicketer, getIdentifier, getRollupKernel
}
