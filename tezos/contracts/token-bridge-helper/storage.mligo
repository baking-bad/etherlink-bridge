#import "../common/tokens/tokens.mligo" "Token"


(*
    Context is used to store the receiver and rollup address
    during the ticket-minting process. It is set during the deposit
    entrypoint execution and cleared after the ticket is received
    from the ticketer and redirected back to the user.
    - receiver: an address that will receive tokens in Etherlink
    - rollup: an address of the Etherlink smart rollup contract
*)
type context_t = [@layout:comb] {
    receiver : bytes;
    rollup : address;
}

(*
    The token bridge helper storage type:
    - token: a token which Ticketer accepts for minting tickets, immutable
    - ticketer: an address of the Ticketer contract, immutable
    - erc_proxy: an address of the ERC20 proxy contract in the
        raw form (H160 format), immutable
    - context: a context of the current ticket-minting process
    - metadata: a big_map containing the metadata of the contract (TZIP-016), immutable
*)
type t = [@layout:comb] {
    token : Token.t;
    ticketer : address;
    erc_proxy : bytes;
    context : context_t option;
    metadata : (string, bytes) big_map;
}

let set_context
        (context : context_t)
        (store : t)
        : t =
    { store with context = (Some context) }

let clear_context (store : t) : t = { store with context = None }
