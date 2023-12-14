#import "./storage.mligo" "Storage"
#import "../common/types/routing-data.mligo" "RoutingData"
#import "../common/types/entrypoints.mligo" "Entrypoints"
#import "../common/tokens/index.mligo" "Token"
#import "../common/types/ticket.mligo" "Ticket"
#import "../common/errors.mligo" "Errors"
#import "../common/utility.mligo" "Utility"


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

    type deposit_params = [@layout:comb] {
        rollup : address;
        routing_info : RoutingData.l1_to_l2_t;
        amount : nat;
    }

    [@entry] let deposit
            (params : deposit_params)
            (store: Storage.t) : return_t =
        (*
            `deposit` entrypoint called when user wants to deposit tokens
            to the Etherlink Bridge.

            This entrypoint will transfer tokens from the user to the contract
            and then call `Ticketer.deposit` entrypoint, which will mint ticket
            and send it back to the TicketHelper contract triggering `default`
            entrypoint.
        *)

        let { amount; routing_info; rollup } = params in
        let () = Utility.assert_no_xtz_deposit () in
        let token = store.token in
        let ticketer = store.ticketer in
        let entry = Entrypoints.get_ticketer_deposit ticketer in
        let sender = Tezos.get_sender () in
        let self = Tezos.get_self_address () in
        let token_transfer_op = Token.get_transfer_op token amount sender self in
        let start_deposit_op = Tezos.transaction amount 0mutez entry in
        let approve_token_op = Token.get_approve_op token ticketer amount in
        let context = { rollup; routing_info } in
        let updated_store = Storage.set_context context store in
        [token_transfer_op; approve_token_op; start_deposit_op], updated_store

    [@entry] let default
            (ticket : Ticket.t)
            (s: Storage.t) : return_t =
        (*
            `default` entrypoint called when Ticketer minted ticket and
            sent it to the TicketHelper contract.

            This entrypoint will transfer ticket to the Etherlink Bridge
            contract and then call its `deposit` entrypoint, which will
            finish deposit process.
        *)

        let () = Utility.assert_no_xtz_deposit () in
        let () = Utility.assert_sender_is s.ticketer in
        match s.context with
        | Some context ->
            let { rollup; routing_info } = context in
            let entry = Entrypoints.get_rollup_deposit rollup in
            let deposit = { routing_info; ticket } in
            let payload = Entrypoints.wrap_rollup_entrypoint deposit in
            let finish_deposit_op = Tezos.transaction payload 0mutez entry in
            let updated_store = Storage.clear_context s in
            [finish_deposit_op], updated_store
        | None -> failwith Errors.routing_data_is_not_set

    // TODO: withdraw entrypoint which allows to withdraw tokens from the ticketer
end
