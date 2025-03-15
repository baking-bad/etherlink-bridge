(* SPDX-CopyrightText 2025 Functori <contact@functori.com> *)
(* SPDX-CopyrightText 2025 Nomadic Labs <contact@nomadic-labs.com> *)
// TODO: add copyright

#import "../common/entrypoints/settle-withdrawal.mligo" "SettleWithdrawalEntry"
#import "../common/entrypoints/purchase-withdrawal.mligo" "PurchaseWithdrawalEntry"
#import "../common/entrypoints/exchanger-burn.mligo" "ExchangerBurnEntry"
#import "../common/types/ticket.mligo" "Ticket"
#import "../common/types/fast-withdrawal.mligo" "FastWithdrawal"
#import "./storage.mligo" "Storage"


type return = operation list * Storage.t

[@inline]
let assert_ticket_is_correct
        (ticket : Ticket.t)
        (exchanger : address) : Ticket.t =
    // TODO: consider checking ticket payload as well?
    let (ticketer, (_, _)), ticket = Tezos.Next.Ticket.read ticket in
    if ticketer <> exchanger then failwith "Wrong ticketer" else ticket

[@inline]
let assert_sender_is_allowed (smart_rollup : address) : unit =
    if Tezos.get_sender () <> smart_rollup then
        failwith "Sender is not allowed to call this entrypoint"

[@inline]
let assert_payload_is_valid
        (withdrawal : FastWithdrawal.t)
        (ticket : Ticket.t) : Ticket.t =
    // TODO: consider converting to bytes without packing?
    let (_, (_, discounted_amount)), ticket = Tezos.Next.Ticket.read ticket in
    if Bytes.pack discounted_amount <> withdrawal.payload then
        failwith "Invalid discounted amount or payload."
    else ticket

[@entry]
let purchase_withdrawal
        (params : PurchaseWithdrawalEntry.t)
        (storage: Storage.t) : return =
    (* TODO: add docstring *)

    let { withdrawal; ticket; service_provider } = params in
    // TODO: disallow xtz payments to this entrypoint
    let ticket = assert_ticket_is_correct ticket storage.exchanger in
    // TODO: check if timestamp expired:
    //       - if it is, assert_full_amount_is_paid
    //       - if it is, assert_payload_is_valid
    let ticket = assert_payload_is_valid withdrawal ticket in
    let _ = Storage.assert_withdrawal_was_not_paid_before withdrawal storage in

    let updated_storage = Storage.add_withdrawal withdrawal service_provider storage in
    let burn_op = ExchangerBurnEntry.send storage.exchanger (withdrawal.base_withdrawer, ticket) in
    [burn_op], updated_storage

[@entry]
let default
        (params : SettleWithdrawalEntry.t)
        (storage: Storage.t) : return =
    (* TODO: add docstring *)

    let (ticket, withdrawal) = SettleWithdrawalEntry.to_key_and_ticket params in
    // TODO: disallow xtz payments to this entrypoint (?)
    let _ = assert_sender_is_allowed storage.smart_rollup in
    let ticket = assert_ticket_is_correct ticket storage.exchanger in

    (* If no advance payment found, send to the withdrawer. *)
    (* If key found, then everything matches, the withdrawal was payed,
       we send the amount to the payer. *)
    let payer_opt, upd_withdrawals = Big_map.get_and_update withdrawal None storage.withdrawals in
    let receiver = match payer_opt with
    | None -> withdrawal.base_withdrawer
    | Some service_provider -> service_provider in
    let burn_op = ExchangerBurnEntry.send storage.exchanger (receiver, ticket) in

    [burn_op], { storage with withdrawals = upd_withdrawals }
