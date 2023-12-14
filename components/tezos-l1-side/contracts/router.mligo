#import "./common/entrypoints/router-withdraw.mligo" "WithdrawEntry"
#import "./common/types/ticket.mligo" "Ticket"
#import "./common/errors.mligo" "Errors"
#import "./common/utility.mligo" "Utility"


module Router = struct
    (*
        Router is a contract that processes withdraw transaction from the
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
            (params : WithdrawEntry.t)
            (store: storage_t) : return_t =
        (*
            `withdraw` entrypoint is called by the smart rollup contract
            to process a withdraw transaction. It accepts a pair of receiver
            address and ticket and sends the ticket to the receiver.
        *)

        let () = Utility.assert_no_xtz_deposit () in
        let { receiver; ticket } = params in
        let entry = Ticket.get_ticket_entrypoint receiver in
        let ticket_transfer_op = Tezos.transaction ticket 0mutez entry in
        [ticket_transfer_op], store

    [@entry] let default
            (_p : unit)
            (_s: storage_t) : return_t =
        (*
            `default` entrypoint implemented to prevent entrypoints collapsing
            into single entrypoint
        *)

        failwith Errors.xtz_deposit_disallowed
end