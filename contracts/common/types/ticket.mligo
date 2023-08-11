#import "../errors.mligo" "Errors"


type payload_t = [@layout:comb] {
    token_id : nat;
    token_info : bytes option;
}

type t = payload_t ticket


let create_ticket
        (payload : payload_t)
        (amount : nat)
        : t =
    match Tezos.create_ticket (payload) amount with
    | None -> failwith Errors.ticket_creation_failed
    | Some t -> t

let get_ticket_entrypoint
        (address : address)
        : t contract =
    match Tezos.get_contract_opt address with
    | None -> failwith Errors.failed_to_get_ticket_entrypoint
    | Some c -> c

let create_l2_payload
        (payload : payload_t)
        (_ticketer : address)
        (l2_id : nat)
        : payload_t =
    // TODO: patch payload.token_info and add ticketer and L1 ticketer id to it
    //       reuse common/tokens/index.mligo as Token with Token.token_info
    let token_info = payload.token_info in {
        token_id = l2_id;
        token_info = token_info;
    }

let split_ticket
        (ticket : t)
        (split_amount : nat)
        : t * t =
    (* Splits ticket into two tickets with given amounts *)
    let (_, (_, amount)), ticket = Tezos.read_ticket ticket in
    let keep_amount =
        if amount >= split_amount then abs(amount - split_amount)
        else failwith Errors.insufficient_amount in
    let ticket_a, ticket_b =
        match Tezos.split_ticket ticket (split_amount, keep_amount) with
        | Some split_tickets -> split_tickets
        | None -> failwith Errors.irreducible_amount in
    ticket_a, ticket_b
