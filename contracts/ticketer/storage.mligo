#import "../common/errors.mligo" "Errors"
#import "../common/tokens/index.mligo" "Token"


type t = {
    extra_metadata : (Token.t, Token.token_info_t) map;
    metadata : (string, bytes) big_map;
    token_ids : (Token.t, nat) big_map;
    tokens : (nat, Token.t) big_map;
    next_token_id : nat;
}

let add_token
        (token : Token.t)
        (store : t)
        : t =
    {
        store with
        token_ids = Big_map.add token store.next_token_id store.token_ids;
        tokens = Big_map.add store.next_token_id token store.tokens;
        next_token_id = store.next_token_id + 1n;
    }

let get_or_create_token_id
        (token : Token.t)
        (store : t)
        : t * nat =
    match Big_map.find_opt token store.token_ids with
    | None -> add_token token store, store.next_token_id
    | Some id -> store, id


let get_token
        (token_id : nat)
        (store : t)
        : Token.t =
    match Big_map.find_opt token_id store.tokens with
    | None -> failwith Errors.token_not_found
    | Some t -> t
