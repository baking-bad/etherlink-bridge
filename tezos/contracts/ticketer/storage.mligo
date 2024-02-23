#import "../common/tokens/index.mligo" "Token"
#import "../common/types/ticket.mligo" "Ticket"
#import "../common/errors.mligo" "Errors"


type t = {
    metadata : (string, bytes) big_map;
    token : Token.t;
    content : Ticket.content_t;
    total_supply : nat;
}

(* The maximum amount of ticket which can be stored on the L2 side is 2^256-1 *)
let two_to_the_256th = 115_792_089_237_316_195_423_570_985_008_687_907_853_269_984_665_640_564_039_457_584_007_913_129_639_936n

let increase_total_supply (amount : nat) (store : t) : t =
    let total_supply = store.total_supply + amount in
    if total_supply >= two_to_the_256th
        then failwith Errors.total_supply_exceed_max
        else { store with total_supply }

let decrease_total_supply (amount : nat) (store : t) : t =
    let total_supply = if amount > store.total_supply
        then failwith Errors.total_supply_exceeded
        else abs (store.total_supply - amount) in
    { store with total_supply }