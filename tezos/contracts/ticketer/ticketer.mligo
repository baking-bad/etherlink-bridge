#import "../common/tokens/index.mligo" "Token"
#import "../common/types/ticket.mligo" "Ticket"
#import "../common/entrypoints/ticketer-deposit.mligo" "TicketerDepositEntry"
#import "../common/entrypoints/router-withdraw.mligo" "RouterWithdrawEntry"
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
            (amount : TicketerDepositEntry.t)
            (store : Storage.t) : return_t =
        (*
            `deposit` entrypoint is used to convert legacy token to a ticket.
            The legacy token is transferred to the ticketer contract and
            the ticket is minted.
        *)

        let () = Utility.assert_no_xtz_deposit () in
        let self = Tezos.get_self_address () in
        let sender = Tezos.get_sender () in
        let ticket = Ticket.create store.content amount in
        let token_transfer_op = Token.get_transfer_op store.token amount sender self in
        let ticket_transfer_op = Ticket.send ticket sender in
        let store = Storage.increase_total_supply amount store in
        [token_transfer_op; ticket_transfer_op], store

    [@entry] let withdraw
            (params : RouterWithdrawEntry.t)
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
        let store = Storage.decrease_total_supply amount store in
        [transfer_op], store

    [@view] let get_total_supply (() : unit) (store : Storage.t) : nat =
        store.total_supply

    [@view] let get_content (() : unit) (store : Storage.t) : Ticket.content_t =
        store.content

    [@view] let get_token (() : unit) (store : Storage.t) : Token.t =
        store.token
end
