module MetadataTracker = struct
    (*
        MetadataTracker is an empty contract that has no storage and provides
        one default entrypoint accepting bytes as an argument. It is used to
        add metadata for smart rollup outbox messages, to be able to track the
        L2 origin of the message on the L1 side.

        NOTE: Metadata is not stored in the contract storage, it is used only
        for the offchain outbox message tracking.
    *)

    type storage_t = unit
    type return_t = operation list * storage_t

    [@entry] let default
            (_metadata : bytes)
            (store : storage_t)
            : return_t =
        (*
            `default` entrypoint accepts metadata bytes and does nothing.

            @param metadata: bytes of metadata
        *)
        [], store
end
