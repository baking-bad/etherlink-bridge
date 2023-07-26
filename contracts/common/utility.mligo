#import "./types.mligo" "Types"
#import "./errors.mligo" "Errors"


let create_ticket (payload, amount : Types.payload * nat) : Types.ticket_t =
    match Tezos.create_ticket (payload) amount with
    | None -> failwith Errors.ticket_creation_failed
    | Some t -> t

let get_ticket_entrypoint (address : address) : Types.ticket_t contract =
    match Tezos.get_contract_opt address with
    | None -> failwith Errors.failed_to_get_ticket_entrypoint
    | Some c -> c

let assert_address_is_self (address : address) : unit =
    if address <> Tezos.get_self_address ()
    then failwith Errors.unauthorized_ticketer else unit
