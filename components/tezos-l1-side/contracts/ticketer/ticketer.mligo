#import "../common/tokens/index.mligo" "Token"
#import "../common/types/ticket.mligo" "Ticket"
#import "../common/types/entrypoints.mligo" "Entrypoints"
#import "../common/errors.mligo" "Errors"
#import "../common/utility.mligo" "Utility"
#import "./storage.mligo" "Storage"


module Ticketer = struct
    (*
        Ticketer is a contract that allows to convert any legacy FA1.2 or
        FA2 token to a ticket. The legacy token can be later released by the
        ticket holder.

        Only one token supported per ticketer contract.

        Information about the token added to the ticket as FA2.1 compatible
        payload `(pair nat (option bytes))` where bytes is a packed
        `token_info` record provided during the ticketer origination.
    *)

    type return_t = operation list * Storage.t

    let assert_content_is_expected
        (content : Ticket.content_t)
        (expected : Ticket.content_t) : unit =
            assert_with_error
                (content = expected)
                Errors.unexpected_content


    [@entry] let deposit
            (amount : Entrypoints.deposit_params)
            (store : Storage.t) : return_t =
        (*
            `deposit` entrypoint is used to convert legacy token to a ticket.
            The legacy token is transferred to the ticketer contract and
            the ticket is minted.
        *)

        let () = Utility.assert_no_xtz_deposit () in
        let ticket = Ticket.create store.content amount in
        let sender = Tezos.get_sender () in
        let sender_contract = Ticket.get_ticket_entrypoint sender in
        let self = Tezos.get_self_address () in
        let token_transfer_op = Token.get_transfer_op store.token amount sender self in
        let ticket_transfer_op = Tezos.transaction ticket 0mutez sender_contract in
        [token_transfer_op; ticket_transfer_op], store

    [@entry] let withdraw
            (params : Entrypoints.withdraw_params)
            (store : Storage.t)
            : return_t =
        (*
            `withdraw` entrypoint is used to release the legacy token from the
            ticket. The ticket is burned and the legacy token is transferred
            to the ticket holder.
        *)

        let { ticket; receiver } = params in
        let (ticketer, (content, amount)), _ = Tezos.read_ticket ticket in
        let () = Utility.assert_address_is_self ticketer in
        let () = Utility.assert_no_xtz_deposit () in
        let () = assert_content_is_expected content store.content in
        let self = Tezos.get_self_address () in
        let transfer_op = Token.get_transfer_op store.token amount self receiver in
        [transfer_op], store
end
