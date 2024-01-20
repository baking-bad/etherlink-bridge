#import "../common/tokens/index.mligo" "Token"
#import "../common/types/ticket.mligo" "Ticket"
#import "../common/errors.mligo" "Errors"


type t = {
    metadata : (string, bytes) big_map;
    token : Token.t;
    content : Ticket.content_t;
    total_supply : nat;
}

let increase_total_supply (amount : nat) (store : t) : t =
    let total_supply = store.total_supply + amount in
    { store with total_supply }

let decrease_total_supply (amount : nat) (store : t) : t =
    let total_supply = if amount > store.total_supply
        then failwith Errors.total_supply_exceeded
        else abs (store.total_supply - amount) in
    { store with total_supply }