#import "../errors.mligo" "Errors"
#import "../tokens/index.mligo" "Token"


type payload_t = [@layout:comb] {
    token_id : nat;
    metadata : bytes option;
}

type t = payload_t ticket


let create
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

// TODO: consider removing these L2 functions, since they are not used:
(*
let create_l2_payload
        (payload : payload_t)
        (ticketer : address)
        (l2_id : nat)
        : payload_t =
    let token_info_map = Token.unopt_token_info payload.metadata in
    // TODO: assert that these keys don't already exist
    let l1_token_info = Map.literal [
        ("l1_token_id", Bytes.pack payload.token_id);
        ("l1_ticketer", Bytes.pack ticketer);
    ] in
    let token_info_map = Token.merge_token_info l1_token_info token_info_map in
    let token_info_opt = Some (Bytes.pack (token_info_map)) in
    {
        token_id = l2_id;
        metadata = token_info_opt;
    }
*)

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
