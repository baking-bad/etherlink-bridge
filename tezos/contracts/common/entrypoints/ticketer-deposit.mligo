#import "../errors.mligo" "Errors"


(* `ticketer-deposit` is deposit interface for the Ticketer contract: *)
type t = nat

let get (router : address) : t contract =
    match Tezos.get_entrypoint_opt "%deposit" router with
    | None -> failwith(Errors.router_entrypoint_not_found)
    | Some entry -> entry
