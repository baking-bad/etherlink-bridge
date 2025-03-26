(* SPDX-CopyrightText 2025 Functori <contact@functori.com> *)
(* SPDX-CopyrightText 2025 Nomadic Labs <contact@nomadic-labs.com> *)
(* SPDX-CopyrightText 2025 Baking Bad <hello@baking-bad.org> *)

#import "../common/entrypoints/settle-withdrawal.mligo" "SettleWithdrawalEntry"
#import "../common/entrypoints/xtz-ticketer-burn.mligo" "XtzTicketerBurnEntry"
#import "../common/entrypoints/router-withdraw.mligo" "RouterWithdrawEntry"
#import "../common/types/ticket.mligo" "Ticket"
#import "../common/tokens/tokens.mligo" "Tokens"
#import "../common/types/fast-withdrawal.mligo" "FastWithdrawal"
#import "../common/errors.mligo" "Errors"
#import "./storage.mligo" "Storage"
#import "./events.mligo" "Events"


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

[@inline]
let is_withdrawal_expired (withdrawal : FastWithdrawal.t) (expiration_seconds : int) : bool =
    Tezos.get_now() > withdrawal.timestamp + expiration_seconds

[@inline]
let assert_withdrawal_not_in_future (withdrawal : FastWithdrawal.t) : unit =
    if Tezos.get_now() < withdrawal.timestamp then
        failwith "Withdrawal must not have a future timestamp"
    else
        unit

[@inline]
let resolve_payout_amount (withdrawal : FastWithdrawal.t) (expiration_seconds : int) : nat =
    if not is_withdrawal_expired withdrawal expiration_seconds then
        let discounted_amount = unpack_payload withdrawal.payload in
        discounted_amount
    else
        withdrawal.full_amount

[@inline]
let assert_attached_amount_is_valid (valid_amount : tez) : unit =
    if Tezos.get_amount () <> valid_amount then
        failwith "Tezos amount is not valid"
    else
        unit

[@inline]
let assert_content_is_valid_for_xtz (content : Ticket.content_t) : unit =
    let valid_xtz_content : Ticket.content_t = (0n, None) in
    if content <> valid_xtz_content then
        failwith "Wrong ticket content for xtz ticketer"
    else
        unit

// TODO: consider reusing Assertions.no_xtz_deposit (but it is not inlined)
[@inline]
let assert_no_xtz_deposit
        (unit : unit)
        : unit =
    if Tezos.get_amount () > 0mutez
    then failwith Errors.xtz_deposit_disallowed else unit

[@inline]
let get_service_provider (status : Storage.status) : address =
    match status with
    | Claimed service_provider -> service_provider
    // NOTE: This case with a `Finished` withdrawal should be impossible,
    // as each withdrawal has a unique ID:
    | Finished -> failwith "Wrong state: withdrawal already finished"

[@entry]
let payout_withdrawal
        (params : payout_withdrawal_params)
        (storage: Storage.t) : return =
    (* TODO: add docstring *)

    let { withdrawal; service_provider } = params in
    let _ = Storage.assert_withdrawal_was_not_paid_before withdrawal storage in
    let _ = assert_withdrawal_not_in_future withdrawal in
    let payout_amount = resolve_payout_amount withdrawal storage.config.expiration_seconds in
    let transfer_op = if withdrawal.ticketer = storage.config.xtz_ticketer then
        (* This is the case when the service provider pays out an XTZ withdrawal *)
        let _ = assert_content_is_valid_for_xtz withdrawal.content in
        let entry = Tezos.get_contract withdrawal.base_withdrawer in
        let payout_amount_tez = payout_amount * 1mutez in
        let _ = assert_attached_amount_is_valid payout_amount_tez in
        Tezos.Next.Operation.transaction unit payout_amount_tez entry
    else
        (* This is the case when the service provider pays out an FA withdrawal *)
        let _ = assert_no_xtz_deposit () in
        let token = get_token withdrawal.ticketer in
        let sender = Tezos.get_sender () in
        // TODO: assert ticket.content the same as withdrawal.ticketer.get_content
        Tokens.send_transfer token payout_amount sender withdrawal.base_withdrawer in

    let updated_storage = Storage.add_withdrawal withdrawal service_provider storage in
    let payout_event = Events.payout_withdrawal { withdrawal; service_provider; payout_amount } in
    [transfer_op; payout_event], updated_storage

[@entry]
let default
        (params : SettleWithdrawalEntry.t)
        (storage: Storage.t) : return =
    (* TODO: add docstring *)

    let (ticket, withdrawal) = SettleWithdrawalEntry.to_key_and_ticket params in
    let _ = assert_no_xtz_deposit () in
    let _ = assert_sender_is_allowed storage.config.smart_rollup in

    (* If no advance payment found, send to the withdrawer. *)
    (* If key found, then everything matches, the withdrawal was payed,
       we send the amount to the payer. *)
    let status_opt = Big_map.find_opt withdrawal storage.withdrawals in
    let receiver = match status_opt with
    | None -> withdrawal.base_withdrawer
    | Some status -> get_service_provider status in
    let upd_withdrawals = if Option.is_some status_opt then
        Big_map.update withdrawal (Some Finished) storage.withdrawals
    else
        storage.withdrawals in

    let (ticketer, (_, _)), ticket = Tezos.Next.Ticket.read ticket in
    let withdraw_op = if ticketer = storage.config.xtz_ticketer then
        // TODO: sync parameter with RouterWithdrawEntry (make record) ?
        XtzTicketerBurnEntry.send storage.config.xtz_ticketer (receiver, ticket)
    else
        RouterWithdrawEntry.send ticketer { receiver; ticket } in
    let finalize_event = Events.settle_withdrawal { withdrawal; receiver } in
    [withdraw_op; finalize_event], { storage with withdrawals = upd_withdrawals }

[@view]
let get_service_provider
        (withdrawal : FastWithdrawal.t)
        (storage : Storage.t) : Storage.status option =
    Big_map.find_opt withdrawal storage.withdrawals

[@view]
let get_config (() : unit) (storage : Storage.t) : Storage.config =
    storage.config
