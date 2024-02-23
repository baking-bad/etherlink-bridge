#import "./storage.mligo" "Storage"
#import "../common/entrypoints/rollup-deposit.mligo" "RollupDepositEntry"
#import "../common/entrypoints/ticketer-deposit.mligo" "TicketerDepositEntry"
#import "../common/entrypoints/router-withdraw.mligo" "RouterWithdrawEntry"
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
        receiver : bytes;
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

        let { amount; receiver; rollup } = params in
        let () = Utility.assert_no_xtz_deposit () in
        let token = store.token in
        let ticketer = store.ticketer in
        let sender = Tezos.get_sender () in
        let self = Tezos.get_self_address () in
        let token_transfer_op = Token.get_transfer_op token amount sender self in
        let start_deposit_op = TicketerDepositEntry.make ticketer amount in
        let approve_token_op = Token.get_approve_op token ticketer amount in
        let context = { rollup; receiver } in
        let updated_store = Storage.set_context context store in
        [token_transfer_op; approve_token_op; start_deposit_op], updated_store

    [@entry] let default
            (ticket : Ticket.t)
            (s: Storage.t) : return_t =
        (*
            `default` entrypoint called when Ticketer minted ticket and
            sent it to the TicketHelper contract.

            This entrypoint will transfer ticket to the Etherlink Bridge
            contract stored in context during `deposit` entrypoint call.
        *)

        let () = Utility.assert_no_xtz_deposit () in
        let () = Utility.assert_sender_is s.ticketer in
        match s.context with
        | Some context ->
            let { rollup; receiver } = context in
            let routing_info = Bytes.concat receiver s.erc_proxy in
            (* TODO: assert routing_info length equal to 40 bytes *)
            let deposit = { routing_info; ticket } in
            let finish_deposit_op = RollupDepositEntry.make rollup deposit in
            let updated_store = Storage.clear_context s in
            [finish_deposit_op], updated_store
        | None -> failwith Errors.routing_data_is_not_set

    [@entry] let unwrap
            (ticket : Ticket.t)
            (s: Storage.t) : return_t =
        (*
            `withdraw` entrypoint called when user wants to convert tickets
            back to tokens for implicit account that not supported to send
            tickets within additional data structure.

            Any ticket that sent to this entrypoint will be redirected to
            the Ticketer contract set in the storage, to the standard
            `withdraw` entrypoint that implements `RouterWithdraw` interface.

            It is the Ticketer responsibility to check that ticket is valid.
        *)

        let () = Utility.assert_no_xtz_deposit () in
        let receiver = Tezos.get_sender () in
        let withdraw = { receiver; ticket } in
        let withdraw_op = RouterWithdrawEntry.make s.ticketer withdraw in
        [withdraw_op], s
end
