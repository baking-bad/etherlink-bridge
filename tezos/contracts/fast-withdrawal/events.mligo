#import "../common/types/fast-withdrawal.mligo" "FastWithdrawal"


type settle_withdrawal_event = {
    withdrawal : FastWithdrawal.t;
    receiver : address;
}

[@inline]
let settle_withdrawal (event : settle_withdrawal_event) : operation =
    Tezos.Next.Operation.emit "%settle_withdrawal" event
