#import "../common/entrypoints/purchase-withdrawal.mligo" "PurchaseWithdrawalEntry"
#import "../common/types/ticket.mligo" "Ticket"


// TODO: add docstring
type t = {
    withdrawal_id : nat;
    withdrawal_amount : nat;
    timestamp : timestamp;
    base_withdrawer : address;
    payload : bytes;
    l2_caller : bytes;
    service_provider : address;
    fast_withdrawal_contract: address;
    exchanger : address;
}

let to_purchase_withdrawal
        (ticket : Ticket.t)
        (purchase_withdrawal_proxy_entry : t)
        : PurchaseWithdrawalEntry.t =
    let {
        withdrawal_id;
        withdrawal_amount;
        timestamp;
        base_withdrawer;
        payload;
        l2_caller;
        service_provider;
        fast_withdrawal_contract = _;
        exchanger = _;
    } = purchase_withdrawal_proxy_entry in
    {
        withdrawal_id;
        ticket;
        timestamp;
        base_withdrawer;
        payload;
        l2_caller;
        service_provider;
        withdrawal_amount;
    }

