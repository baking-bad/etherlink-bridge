#import "../types/ticket.mligo" "Ticket"
#import "../errors.mligo" "Errors"


(*
    `router-withdraw` is router interface that used for redirecting
    tickets during withdrawal from the Etherlink rollup:
 *)
type t = [@layout:comb] {
    receiver: address;
    ticket: Ticket.t;
}

let get (router : address) : t contract =
    match Tezos.get_entrypoint_opt "%withdraw" router with
    | None -> failwith(Errors.router_entrypoint_not_found)
    | Some entry -> entry

