#!/usr/bin/env python3
"""LANE 2 SUPPLEMENT — is the SHIPPED CD register's address set XOR-graded?

The main lane showed the HV carrier IS (Z/2)^d under the shipped bind.  This
supplement asks whether the register srmech actually ships EXPLOITS that: are
its minted per-slot addresses ADDR[i] closed under the grading, i.e. does
``bind(ADDR[i], ADDR[j]) == ADDR[i^j]``?

Subject = the shipped CDRegister address mint
(``srmech.amsc.cascade.cd_register.CDRegister._addr`` ->
``mint_vector(f"{namespace}:e{slot}", D=D)``) and the shipped
``srmech.amsc.hdc.bind``.  Exact byte equality; no float, no abs().
"""
import json

from srmech.amsc import hdc
from srmech.amsc.cascade.cd_register import CDRegister
from srmech.amsc.cascade.cayley_dickson import cd_basis_product
from srmech.signal_processing import mint_vector

OUT = []


def rec(**kw):
    OUT.append(kw)


D_BITS = 8192
NBYTES = D_BITS // 8

for dim, ns in ((16, "SEDENION"), (16, None), (8, None), (32, None)):
    reg = CDRegister(dim=dim, D=D_BITS, namespace=ns)
    addr = [reg._addr(k) for k in range(dim)]        # the SHIPPED address mint
    graded = sum(1 for i in range(dim) for j in range(dim)
                 if hdc.bind(addr[i], addr[j]) == addr[i ^ j])
    # even the identity slot: is ADDR[0] the XOR identity (all-zero)?
    rec(kind="S1_shipped_register_addresses_are_not_graded",
        dim=dim, namespace=reg.namespace, D_bits=D_BITS,
        ordered_pairs=dim * dim, graded_pairs=graded,
        addr0_is_xor_identity=(addr[0] == bytes(NBYTES)),
        note="mint_vector(f'{ns}:e{slot}') is an INDEPENDENT SHA-256 draw per "
             "slot, so the address set carries no grading: bind(ADDR_i, ADDR_j) "
             "is a fresh pseudorandom vector, not ADDR_{i^j}")

# The alternative: mint d GENERATORS and bind-fold. Same mint op, same bind op.
for dim in (8, 16, 32, 64):
    d = dim.bit_length() - 1
    gens = [mint_vector(f"CDGRADE{dim}:g{b}", D=D_BITS) for b in range(d)]
    addr = []
    for k in range(dim):
        v = bytes(NBYTES)
        for b in range(d):
            if (k >> b) & 1:
                v = hdc.bind(v, gens[b])
        addr.append(v)
    graded = sum(1 for i in range(dim) for j in range(dim)
                 if hdc.bind(addr[i], addr[j]) == addr[i ^ j])
    # what a graded address set BUYS: navigate(j) becomes ONE bind on the
    # materialised bundle instead of a per-slot symbolic rewrite — but ONLY the
    # index lane moves; the sign still has to ride out of band.
    sign_pairs_needing_out_of_band = sum(
        1 for i in range(dim) for j in range(dim)
        if cd_basis_product(dim, i, j)[1] == -1)
    rec(kind="S2_generator_fold_addresses_are_graded",
        dim=dim, generators_minted=d, addresses=dim,
        ordered_pairs=dim * dim, graded_pairs=graded,
        grading_exact=(graded == dim * dim),
        mint_calls_generator_fold=d, mint_calls_per_slot_scheme=dim,
        mint_call_ratio=f"{d}/{dim}",
        addr0_is_xor_identity=(addr[0] == bytes(NBYTES)),
        sign_pairs_still_out_of_band=sign_pairs_needing_out_of_band,
        note="d minted generators replace dim minted addresses and the grading "
             "becomes exact; the sign is UNCHANGED and still needs its own lane")

for r in OUT:
    print(json.dumps(r, sort_keys=True))
