#import "../errors.mligo" "Errors"
#import "../types/ticket.mligo" "Ticket"


// TODO: add docstring
type t = address

let get (exchanger : address) : t contract =
    match Tezos.get_entrypoint_opt "%mint" exchanger with
    | None -> failwith(Errors.invalid_exchanger_contract)
    | Some entry -> entry

let send
        (exchanger : address)
        (amount : tez)
        (receiver : t)
        : operation =
    let entry = get exchanger in
    Tezos.Next.Operation.transaction receiver amount entry
