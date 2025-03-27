#import "../common/types/fast-withdrawal.mligo" "FastWithdrawal"


type status =
    | Claimed of address
    | Finished
type withdrawals = (FastWithdrawal.t, status) big_map

(*
    Fast Withdrawal contract configuration:
    - xtz_ticketer: address of the native XTZ ticketer (exchanger)
    - smart_rollup: address of the Etherlink smart rollup
    - expiration_seconds: number of seconds during which a withdrawal can be purchased at a discount
*)
type config = {
    xtz_ticketer : address;
    smart_rollup : address;
    expiration_seconds : int;
}

(*
    Fast Withdrawal contract storage:
    - withdrawals: maps each withdrawal key to a service provider
    - config: fast withdrawal contract configuration
    - metadata: a big_map containing the metadata of the contract (TZIP-016), immutable
*)
type t = {
    withdrawals : withdrawals;
    config : config;
    metadata : (string, bytes) big_map;
}

[@inline]
let add_withdrawal
        (withdrawal : FastWithdrawal.t)
        (service_provider : address)
        (storage : t) : t =
    let status = Claimed service_provider in
    let updated_withdrawals = Big_map.add withdrawal status storage.withdrawals in
    { storage with withdrawals = updated_withdrawals }

[@inline]
let finalize_withdrawal
        (withdrawal : FastWithdrawal.t)
        (provider_opt : address option)
        (storage : t) : t =
    (* Update the ledger only if it was claimed by the provider, otherwise, ignore it: *)
    let status = if Option.is_some provider_opt then Some Finished else None in
    let updated_withdrawals = Big_map.update withdrawal status storage.withdrawals in
    { storage with withdrawals = updated_withdrawals }

[@inline]
let assert_withdrawal_was_not_paid_before
        (withdrawal : FastWithdrawal.t)
        (storage : t) : unit =
    if Option.is_some (Big_map.find_opt withdrawal storage.withdrawals) then
        failwith "The fast withdrawal was already payed"

[@inline]
let unwrap_provider_opt (status : status) : address option =
    match status with
    | Claimed service_provider -> Some service_provider
    | Finished -> None

[@inline]
let get_provider_opt
        (withdrawal : FastWithdrawal.t)
        (storage : t) : address option =
    let status_opt = Big_map.find_opt withdrawal storage.withdrawals in
    match status_opt with
    | Some status -> unwrap_provider_opt status
    | None -> None

[@inline]
let is_xtz_ticketer
        (withdrawal : FastWithdrawal.t)
        (storage : t) : bool =
    withdrawal.ticketer = storage.config.xtz_ticketer
