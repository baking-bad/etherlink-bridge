#import "./common/types/entrypoints.mligo" "Entrypoints"
#import "./common/types/ticket.mligo" "Ticket"
#import "./common/errors.mligo" "Errors"
#import "./common/utility.mligo" "Utility"


module Router = struct

    (*
        Router is a contract that processes withdraw transactiom from the
        smart rollup. It accepts a pair of receiver address and ticket and
        sends the ticket to the receiver.
    *)

    type storage_t = [@layout:comb] {
        // NOTE: unit is used to prevent storage collapsing into single metadata:
        unit : unit;
        metadata : (string, bytes) big_map;
    }
    type return_t = operation list * storage_t

    [@entry] let withdraw
            (params : Entrypoints.router_withdraw_params)
            (store: storage_t) : return_t =
        let () = Utility.assert_no_xtz_deposit () in
        let { receiver; ticket } = params in
        let entry = Ticket.get_ticket_entrypoint receiver in
        let ticket_transfer_op = Tezos.transaction ticket 0mutez entry in
        [ticket_transfer_op], store

    [@entry] let default
            (_p : unit)
            (_s: storage_t) : return_t =
        failwith Errors.xtz_deposit_disallowed
end