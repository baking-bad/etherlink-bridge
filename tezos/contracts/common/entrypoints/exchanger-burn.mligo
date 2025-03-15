#import "../errors.mligo" "Errors"
#import "../types/ticket.mligo" "Ticket"


// TODO: add docstring
type t = address * Ticket.t

let get (exchanger : address) : t contract =
    match Tezos.get_entrypoint_opt "%burn" exchanger with
    | None -> failwith(Errors.invalid_exchanger_contract)
    | Some entry -> entry

let send
        (exchanger : address)
        (receiver_and_ticket : t) : operation =
    let entry = get exchanger in
    Tezos.Next.Operation.transaction receiver_and_ticket 0mutez entry
