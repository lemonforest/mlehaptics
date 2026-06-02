# SIDE RESEARCH — can an Azure VM be a compile+test box with AVX-512 (and "whatnot") for the SHA-NI HAL path? (2026-06-02)

> **Method:** research-twin (opus ∥ sonnet, identical prompt, web-search + citation discipline) **adversarially merged** here. This is a **dev-facing infra answer + scaffold**, NOT a settled fact-sheet: the twin DISAGREED on one load-bearing point (Intel Ice Lake-SP SHA-NI — see CONTESTED), and neither tier got a *primary Intel/AMD ARK leaf-7 confirmation*, so several rows are **attested to secondary sources + flagged**. Treat the UNATTESTED RESIDUE as the most valuable part — close it with a 5-minute live `grep sha_ni /proc/cpuinfo` on the actual VM before relying on any Intel row. Scope: build/test INFRASTRUCTURE (in-scope; not CAD; defensive). The dev measures throughput; this answers *can the box exist + how to pin it*.

## ANSWER
**Yes.** The single most defensible choice is an **AMD-Zen4 "Genoa" Azure VM — the `Dasv6` / `Dadsv6` / `Easv6` family** (e.g. `Standard_D8as_v6`): Zen 4 is AMD's first AVX-512 microarchitecture **and** carries SHA-NI (AMD has shipped Intel SHA Extensions since Zen 1), so **both target ISA bits sit on the same single-generation silicon** — which makes the SKU pin clean. Stand it up as a **self-hosted GitHub Actions runner pinned to that exact SKU** (GitHub/Azure *hosted* runners do NOT guarantee AVX-512/SHA-NI), and put it on an **Azure Dedicated Host** to suppress live-migration CPUID masking. On the **Intel** side, only **Sapphire Rapids / Emerald Rapids** are safe; the **Ice Lake-SP SHA-NI question is contested between sources** (below), so do *not* rely on a mixed `Dv5`/`Dsv5` pool that may schedule you onto an Ice Lake host.

## Attested SKU → ISA table
Both tiers concur on the AMD rows (the recommendation). Intel rows carry the contested item.

| SKU family | CPU (gen) | AVX-512? | SHA-NI? | attestation status |
|---|---|---|---|---|
| **Dasv6 / Dadsv6 / Easv6** | AMD EPYC 9004 **Genoa (Zen 4)** | **Yes** (Zen 4 = AMD's 1st AVX-512 µarch) | **Yes** (SHA since Zen 1; the QEMU EPYC-Genoa CPUID model lists both `CPUID_7_0_EBX_SHA_NI` and `AVX512F\|DQ`) | **both tiers agree**; AVX-512 in Azure Dasv6 doc; SHA-NI via Zen-lineage + QEMU model (secondary) |
| **Dsv6 / Esv6** | Intel Xeon Platinum 8573C **Emerald Rapids (5th gen)** | **Yes** (Azure doc) | **Yes** (Emerald Rapids ≥ Sapphire Rapids lineage) | sonnet-attested (Azure Dsv6 doc + SHA-lineage); opus did not separately confirm — **medium confidence** |
| **Dv5 / Dsv5 / Ev5 / Esv5** | Intel 8473C **Sapphire Rapids** *or* 8370C **Ice Lake** *or* 8573C **Emerald Rapids** — pool may serve ANY | **Yes** (Azure doc) | **MIXED / NOT guaranteed** | AVX-512 attested; SHA-NI only on the Sapphire/Emerald host — **do not rely on this pool** |
| Sapphire Rapids host (8473C) | Intel SPR (4th gen) | Yes | **Yes** (SPR ISA list includes SHA) | both tiers lean yes (Wikipedia SPR infobox) |
| **Ice Lake-SP host (8370C)** | Intel ICX (3rd gen) | Yes | **CONTESTED** | **see below — the headline residue** |
| Dasv5 (Milan/Zen3), Dav4 (Rome/Zen2) | AMD EPYC | **NO** (AVX-512 first on Zen 4) | Yes | excluded — no AVX-512 |

## CONTESTED — Intel Ice Lake-SP SHA-NI (the twin's disagreement; do not silently resolve)
- **opus tier:** Ice Lake-SP (3rd-gen Xeon, 8370C) **lacks** SHA-NI; Intel *server* SHA-NI first appears in **Sapphire Rapids** (4th gen). Basis: Wikipedia's Intel-SHA-extensions page lists Ice Lake **client/mobile only**, no Ice-Lake-*server* entry. Flagged as **inference-from-absence** (no primary doc says "ICX-SP lacks SHA-NI").
- **sonnet tier:** Ice Lake-SP **has** SHA hardware acceleration (cites WikiChip Ice Lake-server / Sunny Cove + ms.codes SHA-CPU list + HotChips-2020 ICX overview).
- **Merge verdict:** **UNRESOLVED** — neither got a primary Intel ARK leaf-7 datasheet for the 8370C (WikiChip returned 403/ECONNREFUSED for opus). **Action:** do not depend on Ice-Lake-SP SHA-NI; either use the **AMD Genoa** path (both tiers agree) or a **guaranteed Sapphire/Emerald Rapids** Intel SKU, and **confirm with a live `grep sha_ni /proc/cpuinfo`** on the provisioned VM.

## CI recommendation
1. **Don't use hosted runners** (GitHub-hosted / Azure-DevOps Microsoft-hosted) — heterogeneous fleet, ISA not selectable or documented (corroborated by `actions/runner-images` disc. #3390, `actions/runner` #1069).
2. **Provision your own Azure VM at a pinned SKU**, register it as a **self-hosted GitHub Actions runner** (or Azure DevOps self-hosted agent). Pin at create time:
   ```bash
   az vm create -g rg-srmech-ci -n srmech-isa-runner \
     --image Ubuntu2404 --size Standard_D8as_v6 \   # Genoa/Zen4: AVX-512 + SHA-NI (both-tier agreed)
     --admin-username azureuser --generate-ssh-keys
   # install the Actions runner; label it: [self-hosted, linux, x64, avx512, shani]
   ```
   `--size` is the SKU pin; `*asv6` is single-generation (Genoa only) → stable ISA across host moves within the family.
3. **Kill the live-migration masking risk** with an **Azure Dedicated Host** (`az vm dedicated-host create`) — Microsoft docs: *"Azure dedicated hosts do not support live migration."* Eliminates cross-generation CPUID masking entirely.
4. **cibuildwheel** runs on the self-hosted runner (`runs-on: [self-hosted, avx512, shani]`); wheels stay portable (runtime HAL dispatch) — only the *test* step needs the real ISA.
5. **Gate the job on a runtime ISA assertion** (below) so CI **fails loud** if the runner ever lands on a host missing a flag.

## Runtime-detection + compile-flags recipe
```bash
# Linux — confirm BOTH features are really exposed on the box
grep -o -E 'avx512f|sha_ni' /proc/cpuinfo | sort -u   # expect: avx512f AND sha_ni
lscpu | grep -o -E 'avx512f|sha_ni'                    # same flags
```
**SAFE runtime dispatch = CPUID leaf 7, subleaf 0 (both tiers + the conservative choice):**
```c
#include <intrin.h>      /* MSVC; <cpuid.h> on gcc/clang */
int r[4]; __cpuidex(r, 7, 0);
int has_sha     = (r[1] >> 29) & 1;   /* EBX bit 29 = SHA */
int has_avx512f = (r[1] >> 16) & 1;   /* EBX bit 16 = AVX-512F */
```
gcc/clang also offer `__builtin_cpu_supports("avx512f")` (**confirmed valid**) — but **`__builtin_cpu_supports("sha")` was NOT primary-confirmed** (opus residue #1); prefer the leaf-7/EBX-29 path for the SHA gate.
**Compile flags:** gcc/clang `-msha -mavx512f -mavx512bw -mavx512vl` (compile the CPU-detect TU *without* these), or `-march=znver4` (Genoa) / `-march=sapphirerapids`. MSVC `/arch:AVX512` (no `/arch` switch exists for SHA — the `_mm_sha256*` intrinsics in `<immintrin.h>` are available unconditionally; gate their *execution* behind the leaf-7 check).

## UNATTESTED RESIDUE (close before lodging as fact)
1. **Intel Ice-Lake-SP SHA-NI — CONTESTED** (see above). The headline. Don't depend on it.
2. **`__builtin_cpu_supports("sha")` string validity** — unconfirmed to GCC docs; use the CPUID leaf-7 path.
3. **Azure hypervisor CPUID masking of `sha_ni` on v5/v6 families** — undocumented whether the guest sees `sha_ni` despite supporting hardware (Hyper-V compatibility mode *can* mask features for migration). **Highest practical risk.** Mitigate: Dedicated Host + live `grep`.
4. **No live `/proc/cpuinfo` from an actual Azure `D*as_v6`** captured this pass — a 5-min `az vm create … && grep sha_ni /proc/cpuinfo` closes it definitively.
5. **CPUID EBX bit numbers (29=SHA, 16=AVX512F)** standard/widely-used but not re-verified vs Intel SDM Vol.2 this pass.
6. **Regional GA of Dasv6/Dsv6 varies** — check `az vm list-skus --location <region> --size Standard_D8as_v6`.
7. **Zen 4 AVX-512 = 2× 256-bit (double-pumped)** — correctness-identical, throughput-relevant only for the dev's benchmark (secondary source, Agner-Fog-forum-tier).

## SOURCES (URLs the twin fetched/searched — re-verify the flagged ones before lodging as attested)
1. Azure Dasv6 — learn.microsoft.com/.../sizes/general-purpose/dasv6-series (Genoa; Live Migration supported)
2. Azure Dsv6 — learn.microsoft.com/.../sizes/general-purpose/dsv6-series (Emerald Rapids 8573C; AVX-512)
3. Azure Dsv5 / Dv5 — learn.microsoft.com/.../dsv5-series, dv5-series (8473C SPR / 8370C ICX / 8573C EMR; AVX-512)
4. Zen 4 — en.wikipedia.org/wiki/Zen_4 ("first AMD µarch to support AVX-512")
5. Zen 1 — en.wikipedia.org/wiki/Zen_(first_generation) (SHA support)
6. Intel SHA extensions — en.wikipedia.org/wiki/Intel_SHA_extensions (Ice Lake *client* only; AMD Zen 2017+) ⚠ basis of the CONTESTED row
7. Sapphire Rapids — en.wikipedia.org/wiki/Sapphire_Rapids (SHA in ISA list)
8. QEMU EPYC-Genoa CPUID model — mail-archive.com qemu-devel msg1076318 (`CPUID_7_0_EBX_SHA_NI` + `AVX512F|DQ`)
9. MSVC `/arch:x64` — learn.microsoft.com/.../cpp/build/reference/arch-x64 (`/arch:AVX512`; `__cpuidex`)
10. Azure Dedicated Hosts — learn.microsoft.com/.../dedicated-hosts ("do not support live migration")
11. GitHub self-hosted runner on Azure — techcommunity.microsoft.com step-by-step; hosted-runner ISA inconsistency: actions/runner-images disc. #3390, actions/runner #1069
12. ⚠ NOT individually fetched (corroborating only): WikiChip ICX-server/Genoa (403/ECONNREFUSED), ms.codes SHA-CPU list, Phoronix/AMD AVX-512-on-EPYC blog, HotChips-2020 ICX.

*Discipline: research-twin (no privileged model) + MPM citation discipline (`[[feedback_pdf_extraction_citation_discipline]]`, `[[feedback_paywalled_doi_cannot_be_attested]]` analogue for vendor docs); `[[feedback_trauma_informed_defensive_scope]]` (build infra, defensive). Pairs with the C-library discipline (runtime HAL dispatch, no new direct `hashlib.sha256`). Cross-ref: UPSTREAM_NOTES §13 (dev hand-down) + §12.6 (the rc10 `sha256_batch` SIMD graft this box would test).*
