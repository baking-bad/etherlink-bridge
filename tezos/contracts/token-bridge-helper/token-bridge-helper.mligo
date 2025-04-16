#import "./storage.mligo" "Storage"
#import "../common/entrypoints/rollup-deposit.mligo" "RollupDepositEntry"
#import "../common/entrypoints/ticketer-deposit.mligo" "TicketerDepositEntry"
#import "../common/entrypoints/router-withdraw.mligo" "RouterWithdrawEntry"
#import "../common/tokens/tokens.mligo" "Token"
#import "../common/types/ticket.mligo" "Ticket"
#import "../common/errors.mligo" "Errors"
#import "../common/assertions.mligo" "Assertions"


module TokenBridgeHelper = struct
    (*
        TokenBridgeHelper is a helper contract which helps user to communicate with
        Etherlink Bridge components that requires tickets to be packed into
        external data structure.

        The TokenBridgeHelper implementation focused on FA1.2 and FA2 tokens only.

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

    let assert_routing_info_len_is_equal_to_40n
            (routing_info : bytes) : unit =
        let length = Bytes.length routing_info in
        if length <> 40n then
            failwith Errors.wrong_routing_info_length


    [@entry] let deposit
            (params : deposit_params)
            (store: Storage.t) : return_t =
        (*
            `deposit` entrypoint called when the user wants to deposit tokens
            to the Etherlink Bridge.

            This entrypoint will transfer tokens from the user to the contract
            and then call `Ticketer.deposit` entrypoint, which will mint a ticket
            and send it back to the TokenBridgeHelper contract triggering `default`
            entrypoint.

            @param rollup: an address of the Etherlink smart rollup contract
            @param receiver: an address in the Etherlink that will receive tokens
            @param amount: an amount of tokens to be bridged
        *)

        let { amount; receiver; rollup } = params in
        let () = Assertions.no_xtz_deposit () in
        let token = store.token in
        let ticketer = store.ticketer in
        let sender = Tezos.get_sender () in
        let self = Tezos.get_self_address () in
        let token_transfer_op = Token.send_transfer token amount sender self in
        let start_deposit_op = TicketerDepositEntry.send ticketer amount in
        let approve_token_op = Token.send_approve token ticketer amount in
        let context = { rollup; receiver } in
        let updated_store = Storage.set_context context store in
        [token_transfer_op; approve_token_op; start_deposit_op], updated_store

    [@entry] let default
            (ticket : Ticket.t)
            (s: Storage.t) : return_t =
        (*
            `default` entrypoint called when Ticketer minted ticket and
            sent it to the TokenBridgeHelper contract.

            This entrypoint will transfer a ticket to the Etherlink Bridge
            contract stored in context during `deposit` entrypoint call.

            @param ticket: a ticket from the Ticketer contract
        *)

        let () = Assertions.no_xtz_deposit () in
        let () = Assertions.sender_is s.ticketer in
        match s.context with
        | Some context ->
            let { rollup; receiver } = context in
            let routing_info = Bytes.concat receiver s.erc_proxy in
            let () = assert_routing_info_len_is_equal_to_40n routing_info in
            let deposit = { routing_info; ticket } in
            let finish_deposit_op = RollupDepositEntry.send rollup deposit in
            let updated_store = Storage.clear_context s in
            [finish_deposit_op], updated_store
        | None -> failwith Errors.routing_data_is_not_set

    [@entry] let unwrap
            (ticket : Ticket.t)
            (s: Storage.t) : return_t =
        (*
            `unwrap` entrypoint is called when the user wants to convert
            tickets back to tokens. This allows implicit account to wrap
            tickets within an additional data structure and send it to
            the Ticketer.

            Any ticket sent to this entrypoint will be redirected to
            the Ticketer contract set in the storage, to the `withdraw`
            entrypoint that implements `RouterWithdraw` interface.

            It is Ticketer's responsibility to check that the ticket is valid.

            @param ticket: ticket from the user to be unwrapped
        *)

        let () = Assertions.no_xtz_deposit () in
        let receiver = Tezos.get_sender () in
        let withdraw = { receiver; ticket } in
        let withdraw_op = RouterWithdrawEntry.send s.ticketer withdraw in
        [withdraw_op], s

    [@entry] let withdraw
            (params : RouterWithdrawEntry.t)
            (s : Storage.t)
            : return_t =
        (*
            `withdraw` entrypoint is added in case the user specifies this
            Helper contract as the ticket recipient, instead of a Ticketer.
            This entriponite reads the ticket and redirects it to the Ticketer
            contract keeping the same routing information.

            @param receiver: an address that will receive the unlocked token.
            @param ticket: provided ticket to be burned.
        *)
        let { ticket; receiver } = params in
        let (ticketer, (_, _)), ticket = Tezos.Next.Ticket.read ticket in
        let withdraw = { receiver; ticket } in
        let withdraw_op = RouterWithdrawEntry.send ticketer withdraw in
        [withdraw_op], s
end
