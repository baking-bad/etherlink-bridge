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


(*
    Fast Withdrawal is a contract allowing service providers to promptly
    finalize user withdrawals and later receive funds from Etherlink after
    outbox message settlement.

    Supported withdrawal types:
    - XTZ withdrawals (requires exchanger to implement the `burn` entrypoint)
    - FA bridge withdrawals (requires ticketer to implement the `withdraw`
      entrypoint and `get_token` and `get_content` views)

    Workflow:
    1. Providers initiate withdrawal claims by calling `payout_withdrawal`.
    2. For native withdrawals, providers must attach the required XTZ amount.
       For FA withdrawals, providers must approve the required tokens.
    3. The payout amount is determined based on withdrawal expiration:
        - If the withdrawal has not expired, a discounted amount (encoded in
          the payload as Michelson nat) applies.
        - If the withdrawal has expired, the full amount must be paid.
    4. After successful validation, funds are transferred to the user, and the
        provider's address is recorded in the `withdrawals` ledger as a claim.
    5. Withdrawal settlement occurs via the `default` entrypoint triggered by
        an outbox message from the smart rollup:
        - If claimed, the provider receives the unwrapped ticket as payout.
        - Otherwise, the ticket is unwrapped for the `base_withdrawer`.
*)

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
    | Some amount -> amount
    | None -> failwith "Error during payload unpack"

[@inline]
let get_token (ticketer : address) : Tokens.t =
    match Tezos.Next.View.call "get_token" unit ticketer with
    | Some token -> token
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
    (*
        Checks if the withdrawal has expired: if so, it should be paid in full,
        otherwise, it should be paid at a discounted amount, which is encoded in the payload.
    *)
    if not is_withdrawal_expired withdrawal expiration_seconds then
        let discounted_amount = unpack_payload withdrawal.payload in
        discounted_amount
    else
        withdrawal.full_amount

[@inline]
let assert_attached_amount_is_valid (valid_amount : nat) : unit =
    if Tezos.get_amount () <> valid_amount * 1mutez then
        failwith "Tezos amount is not valid"
    else
        unit

[@inline]
let assert_ticket_content_is_valid_for_xtz (content : Ticket.content_t) : unit =
    let valid_xtz_content : Ticket.content_t = (0n, None) in
    if content <> valid_xtz_content then
        failwith "Wrong ticket content for xtz ticketer"
    else
        unit

// TODO: consider reusing Assertions.no_xtz_deposit (but it is not inlined)
[@inline]
let assert_no_xtz_deposit (unit : unit) : unit =
    if Tezos.get_amount () > 0mutez
    then failwith Errors.xtz_deposit_disallowed else unit

[@inline]
let send_ticket
        (withdrawal : FastWithdrawal.t)
        (storage : Storage.t) : XtzTicketerBurnEntry.t -> operation =
    (*
        Determines the ticketer type and sends it to the contract.
        Both FA (RouterWithdrawEntry) and XTZ ticketers share the same type
        but have different entrypoint names.
    *)
    if Storage.is_xtz_ticketer withdrawal storage then
        XtzTicketerBurnEntry.send withdrawal.ticketer
    else
        RouterWithdrawEntry.send withdrawal.ticketer

[@inline]
let send_xtz_op (amount : nat) (receiver : address) : operation =
    let entry = Tezos.get_contract receiver in
    Tezos.Next.Operation.transaction unit (amount * 1mutez) entry

[@inline]
let send_tokens_op (token: Tokens.t) (amount : nat) (receiver : address) : operation =
    let sender = Tezos.get_sender () in
    Tokens.send_transfer token amount sender receiver

[@entry]
let payout_withdrawal
        (params : payout_withdrawal_params)
        (storage: Storage.t) : return =
    (*
        `payout_withdrawal` allows a service provider to finalize a user's
        withdrawal early, creating a claim for future settlement.

        Parameters:
        @param withdrawal: details of the user's requested withdrawal.
        @param service_provider: address eligible to receive reimbursement.

        Effects:
        - records the withdrawal claim in the `withdrawals` ledger.
        - transfers funds immediately to the withdrawer.
        - emits the `payout_withdrawal` event.
    *)

    let { withdrawal; service_provider } = params in
    let expiration_seconds = storage.config.expiration_seconds in
    let receiver = withdrawal.base_withdrawer in
    let _ = Storage.assert_withdrawal_was_not_paid_before withdrawal storage in
    let _ = assert_withdrawal_not_in_future withdrawal in

    let payout_amount = resolve_payout_amount withdrawal expiration_seconds in
    let payout_operation = if Storage.is_xtz_ticketer withdrawal storage then
        (* This is the case when the service provider pays out an XTZ withdrawal *)
        let _ = assert_ticket_content_is_valid_for_xtz withdrawal.content in
        let _ = assert_attached_amount_is_valid payout_amount in
        send_xtz_op payout_amount receiver
    else
        (* This is the case when the service provider pays out an FA withdrawal *)
        // TODO: assert ticket.content the same as withdrawal.ticketer.get_content
        let _ = assert_no_xtz_deposit () in
        let token = get_token withdrawal.ticketer in
        send_tokens_op token payout_amount receiver in

    let updated_storage = Storage.add_withdrawal withdrawal service_provider storage in
    let payout_event = Events.payout_withdrawal { withdrawal; service_provider; payout_amount } in
    [payout_operation; payout_event], updated_storage

[@entry]
let default
        (params : SettleWithdrawalEntry.t)
        (storage: Storage.t) : return =
    (*
        `default` is an entrypoint that receives tickets from the Etherlink
        smart rollup after the corresponding outbox withdrawal message has been
        executed. It finalizes previously claimed withdrawal or, if no claim
        was recorded, unwraps the ticket directly to the withdrawer.

        Parameters:
        @param withdrawal_id: unique identifier of the withdrawal.
        @param ticket: ticket provided with withdrawal (XTZ or FA).
        @param timestamp: time when the withdrawal was applied on Etherlink.
        @param base_withdrawer: original withdrawal receiver address.
        @param payload: fast withdrawal conditions packed into bytes.
        @param l2_caller: original sender address from the Etherlink side.

        Effects:
        - updates the `withdrawals` ledger state from `Claimed` to `Finished`
          if a claim existed.
        - unwraps the provided ticket to either the service provider (if advance
          payment found) or to the original withdrawer.
        - emits the `settle_withdrawal` event.
    *)

    let (ticket, withdrawal) = SettleWithdrawalEntry.to_key_and_ticket params in
    let _ = assert_no_xtz_deposit () in
    let _ = assert_sender_is_allowed storage.config.smart_rollup in

    let provider_opt = Storage.get_provider_opt withdrawal storage in
    let receiver = match provider_opt with
    | None -> withdrawal.base_withdrawer
    | Some provider -> provider in
    let finalize_operation = send_ticket withdrawal storage { receiver; ticket } in
    let finalize_event = Events.settle_withdrawal { withdrawal; receiver } in
    let updated_storage = Storage.finalize_withdrawal withdrawal provider_opt storage in
    [finalize_operation; finalize_event], updated_storage

[@view]
let get_status
        (withdrawal : FastWithdrawal.t)
        (storage : Storage.t) : Storage.status option =
    Big_map.find_opt withdrawal storage.withdrawals

[@view]
let get_config (() : unit) (storage : Storage.t) : Storage.config =
    storage.config
