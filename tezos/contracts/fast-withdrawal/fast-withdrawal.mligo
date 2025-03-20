(* SPDX-CopyrightText 2025 Functori <contact@functori.com> *)
(* SPDX-CopyrightText 2025 Nomadic Labs <contact@nomadic-labs.com> *)
// TODO: add copyright

#import "../common/entrypoints/settle-withdrawal.mligo" "SettleWithdrawalEntry"
#import "../common/entrypoints/exchanger-burn.mligo" "ExchangerBurnEntry"
#import "../common/entrypoints/router-withdraw.mligo" "RouterWithdrawEntry"
#import "../common/types/ticket.mligo" "Ticket"
#import "../common/tokens/tokens.mligo" "Tokens"
#import "../common/types/fast-withdrawal.mligo" "FastWithdrawal"
#import "./storage.mligo" "Storage"


// TODO: add docstring
type payout_withdrawal_params = {
    withdrawal : FastWithdrawal.t;
    service_provider : address;
}

type return = operation list * Storage.t

[@inline]
let assert_sender_is_allowed (smart_rollup : address) : unit =
    if Tezos.get_sender () <> smart_rollup then
        failwith "Sender is not allowed to call this entrypoint"

[@inline]
let unpack_payload (payload : bytes) : nat =
    match Bytes.unpack payload with
    | Some (amount) -> amount
    | None -> failwith "Error during payload unpack"

[@inline]
let get_token (ticketer : address) : Tokens.t =
    match Tezos.Next.View.call "get_token" unit ticketer with
    | Some (token) -> token
    | None -> failwith "Error in get_token view call"

[@entry]
let payout_withdrawal
        (params : payout_withdrawal_params)
        (storage: Storage.t) : return =
    (* TODO: add docstring *)

    let { withdrawal; service_provider } = params in
    let _ = Storage.assert_withdrawal_was_not_paid_before withdrawal storage in
    let discounted_amount = unpack_payload withdrawal.payload in
    // TODO: check if timestamp expired:
    //       - if it is, payout_amount = discounted_amount
    //       - if it is, payout_amount = withdrawal.full_amount
    let payout_amount = discounted_amount in
    let transfer_op = if withdrawal.ticketer = storage.exchanger then
        // TODO: assert ticket content in None
        let entry = Tezos.get_contract withdrawal.base_withdrawer in
        let payout_amount_tez = payout_amount * 1mutez in
        Tezos.Next.Operation.transaction unit payout_amount_tez entry
    else
        // TODO: assert no xtz added to this entrypoint
        let token = get_token withdrawal.ticketer in
        let sender = Tezos.get_sender () in
        // TODO: assert ticket.content the same as withdrawal.ticketer.get_content
        Tokens.send_transfer token payout_amount sender withdrawal.base_withdrawer in

    let updated_storage = Storage.add_withdrawal withdrawal service_provider storage in
    [transfer_op], updated_storage

[@entry]
let default
        (params : SettleWithdrawalEntry.t)
        (storage: Storage.t) : return =
    (* TODO: add docstring *)

    let (ticket, withdrawal) = SettleWithdrawalEntry.to_key_and_ticket params in
    // TODO: disallow xtz payments to this entrypoint (?)
    let _ = assert_sender_is_allowed storage.smart_rollup in

    (* If no advance payment found, send to the withdrawer. *)
    (* If key found, then everything matches, the withdrawal was payed,
       we send the amount to the payer. *)
    let payer_opt, upd_withdrawals = Big_map.get_and_update withdrawal None storage.withdrawals in
    let receiver = match payer_opt with
    | None -> withdrawal.base_withdrawer
    | Some service_provider -> service_provider in

    let (ticketer, (_, _)), ticket = Tezos.Next.Ticket.read ticket in
    let withdraw_op = if ticketer = storage.exchanger then
        // TODO: sync parameter with RouterWithdrawEntry (make record) ?
        ExchangerBurnEntry.send storage.exchanger (receiver, ticket)
    else
        RouterWithdrawEntry.send ticketer { receiver; ticket } in
    [withdraw_op], { storage with withdrawals = upd_withdrawals }
