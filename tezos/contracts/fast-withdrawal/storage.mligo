#import "../common/types/fast-withdrawal.mligo" "FastWithdrawal"


type withdrawals = (FastWithdrawal.t, address) big_map

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
*)
type t = {
    withdrawals : withdrawals;
    config : config;
}

let add_withdrawal
        (withdrawal : FastWithdrawal.t)
        (service_provider : address)
        (storage : t) : t =
    let updated_withdrawals = Big_map.add withdrawal service_provider storage.withdrawals in
    { storage with withdrawals = updated_withdrawals }

[@inline]
let assert_withdrawal_was_not_paid_before
        (withdrawal : FastWithdrawal.t)
        (storage : t) : unit =
    if Option.is_some (Big_map.find_opt withdrawal storage.withdrawals) then
        failwith "The fast withdrawal was already payed"
