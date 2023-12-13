// TODO: remove redundant imports:
#import "./storage.mligo" "Storage"
#import "../common/types/routing-data.mligo" "RoutingData"
#import "../common/types/entrypoints.mligo" "Entrypoints"
#import "../common/tokens/index.mligo" "Token"
#import "../common/types/ticket.mligo" "Ticket"
#import "../common/errors.mligo" "Errors"
#import "../common/utility.mligo" "Utility"


type deposit_params = [@layout:comb] {
    // TODO: add here rollup address?
    routing_data : RoutingData.l1_to_l2_t;
    amount : nat;
}

module TicketHelper = struct
    (*
        TicketHelper is a helper contract which helps user to communicate with
        Etherlink Bridge components that requires tickets to be packed into
        external data structure.

        This contract expected to be temporal solution until Tezos will support
        ability to transfer tickets within additional data structure from
        implicit accounts.
    *)

    type return_t = operation list * Storage.t

    [@entry] let deposit
            (params : deposit_params)
            (store: Storage.t) : return_t =
        let () = Utility.assert_no_xtz_deposit () in
        let token = store.token in
        let ticketer = store.ticketer in
        let { amount; routing_data } = params in
        let entry = Entrypoints.get_ticketer_deposit ticketer in
        let sender = Tezos.get_sender () in
        let self = Tezos.get_self_address () in
        let token_transfer_op = Token.get_transfer_op token amount sender self in
        let start_deposit_op = Tezos.transaction amount 0mutez entry in
        let updated_store = Storage.set_routing_data routing_data store in
        [token_transfer_op; start_deposit_op], updated_store

    [@entry] let approve
            (_unit : unit)
            (store: Storage.t) : return_t =
        // TODO: make approves during deposit instead
        let () = Utility.assert_no_xtz_deposit () in
        Token.get_approve_ops store.token store.ticketer store.approve_amount, store

    [@entry] let default
            (ticket : Ticket.t)
            (s: Storage.t) : return_t =
        // NOTE: default entrypoint called when Ticketer minted ticket and
        //       sends it to the TicketHelper contract.

        // NOTE: we trust Ticketer and assume that amount and payload are correct

        // NOTE: it is assumed that routing data was set before deposit
        //       is there any case when this might be a problem?
        //       as far as only Ticketer can call this entrypoint, looks like
        //       it is safe to assume that routing data was set before deposit

        let () = Utility.assert_no_xtz_deposit () in
        let () = Utility.assert_sender_is s.ticketer in
        match s.routing_data with
        | Some routing_info ->
            let entry = Entrypoints.get_rollup_deposit s.rollup in
            let deposit : Entrypoints.deposit = {
                routing_info = routing_info;
                ticket = ticket;
            } in
            let deposit_or_bytes : Entrypoints.deposit_or_bytes = (M_left deposit) in
            let payload : Entrypoints.rollup_entry = (M_left deposit_or_bytes) in
            let finish_deposit_op = Tezos.transaction payload 0mutez entry in
            let updated_store = Storage.clear_routing_data s in
            [finish_deposit_op], updated_store
        | None -> failwith Errors.routing_data_is_not_set

    // TODO: withdraw entrypoint which allows to withdraw tokens from the ticketer
end
