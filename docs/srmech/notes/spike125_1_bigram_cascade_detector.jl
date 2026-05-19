#!/usr/bin/env julia
# Spike #125.1 — Julia bigram-cascade detector (follow-up to Spike #125).
#
# Parent Spike #125 (Python/numpy unigram-frequency Laplacian detector) returned
# Cohen's d ≈ 0 across all 4 adversarial classes. Root cause: random_baseline
# (character-shuffled) preserves unigram frequency, so the unigram detector
# is provably blind to it. Cascade-shape signal must live in higher-order n-gram
# structure.
#
# Spike #125.1 refines to BIGRAM co-occurrence: same 5 contrast classes, same
# Cohen's d metric, but build the co-occurrence Laplacian over top-N most-frequent
# observed bigrams (not single characters). The hypothesis: bigram structure
# captures local order and so should discriminate random_baseline (shuffle
# destroys bigram structure) and may discriminate value/vocab/citation mutations
# at the bigram level.
#
# Bit-exact reproducibility: Random.seed!(42) upfront; deterministic FP ops;
# script designed to produce identical output across runs.
#
# Anchors:
#   - parent Spike #125 (docs/srmech/notes/spike125_*)
#   - [[feedback_every_doc_edit_faces_falsification]]
#   - [[feedback_autonomous_research_followup_authorization]]

using Random
using LinearAlgebra
using Printf
using Statistics

# Bit-exact: pin the RNG seed up front.
Random.seed!(42)

# =====================================================================
# 1. Configuration constants (mirrors Spike #125 / parent)
# =====================================================================

const ALPHABET = "abcdefghijklmnopqrstuvwxyz0123456789 .,()[]+-=*/_<>:; \n\t\"'"
# Exactly 64 chars (matches parent unigram alphabet).
@assert length(ALPHABET) >= 64 "Alphabet must have at least 64 chars"
const ALPHA64 = ALPHABET[1:64]
# Char -> [0,63] integer index
const ALPHA_INDEX = Dict{Char,Int}(c => i-1 for (i, c) in enumerate(ALPHA64))

const N_ALPHA = 64
const TOP_N_BIGRAMS = 1000         # Bound state-vector dimensionality
const CHUNK_SIZE = 2000            # Char chunks (matches parent)
const COOC_WINDOW = 1              # Bigram window in bigram-tokens (= adjacent)
const HELD_OUT_FRAC = 0.30         # Last 30% of corpus reserved for evaluation
const RNG_SEED = 42

# =====================================================================
# 2. Corpus load (truth: MFO + srmech notebooks, same as parent)
# =====================================================================

const REPO_ROOT = abspath(joinpath(@__DIR__, "..", "..", ".."))
const MFO_PATH = joinpath(REPO_ROOT, "docs", "antikythera-maths", "mfo_spectral_research_notebook.md")
const SRMECH_PATH = joinpath(REPO_ROOT, "docs", "srmech", "srmech_research_notebook.md")

function load_attested_corpus()
    parts = String[]
    for path in (MFO_PATH, SRMECH_PATH)
        text = read(path, String)
        push!(parts, text)
    end
    return join(parts, "\n")
end

function text_to_indices(text::AbstractString)
    out = Int[]
    for c in lowercase(text)
        if haskey(ALPHA_INDEX, c)
            push!(out, ALPHA_INDEX[c])
        end
    end
    return out
end

# Convert sequence of unigram indices -> sequence of bigram tokens (each in [0, 64²-1]).
function indices_to_bigrams(idxs::Vector{Int})
    n = length(idxs)
    if n < 2
        return Int[]
    end
    out = Vector{Int}(undef, n - 1)
    @inbounds for i in 1:(n-1)
        out[i] = idxs[i] * N_ALPHA + idxs[i+1]
    end
    return out
end

# =====================================================================
# 3. Top-N bigram alphabet selection (built once from full corpus)
# =====================================================================

function topn_bigrams(corpus::AbstractString, topn::Int)
    idxs = text_to_indices(corpus)
    bigrams = indices_to_bigrams(idxs)
    counts = Dict{Int,Int}()
    for b in bigrams
        counts[b] = get(counts, b, 0) + 1
    end
    # Sort by (-count, token-id) to get a deterministic top-N
    pairs = collect(counts)
    sort!(pairs, by = p -> (-p[2], p[1]))
    k = min(topn, length(pairs))
    selected_tokens = [p[1] for p in pairs[1:k]]
    # Map token-id -> compact slot index in [0, k-1]
    token_to_slot = Dict{Int,Int}(t => i-1 for (i, t) in enumerate(selected_tokens))
    return selected_tokens, token_to_slot
end

# =====================================================================
# 4. Bigram co-occurrence Laplacian (Hermitian PSD)
# =====================================================================

# Build Laplacian over bigram-tokens. Nodes = compact slot indices.
# Edge weight A[a,b] = co-occurrence count when bigram-tokens a and b
# appear within COOC_WINDOW positions in the bigram-sequence.
function bigram_cooc_laplacian(corpus::AbstractString,
                               token_to_slot::Dict{Int,Int},
                               n_nodes::Int;
                               window::Int = COOC_WINDOW)
    idxs = text_to_indices(corpus)
    bigrams = indices_to_bigrams(idxs)
    A = zeros(Float64, n_nodes, n_nodes)
    nb = length(bigrams)
    @inbounds for i in 1:nb
        a = bigrams[i]
        sa = get(token_to_slot, a, -1)
        if sa < 0
            continue
        end
        upper = min(i + window, nb)
        for j in (i+1):upper
            b = bigrams[j]
            sb = get(token_to_slot, b, -1)
            if sb < 0 || sa == sb
                continue
            end
            A[sa+1, sb+1] += 1.0
            A[sb+1, sa+1] += 1.0
        end
    end
    deg = vec(sum(A, dims=2))
    L = -A
    @inbounds for i in 1:n_nodes
        L[i, i] = deg[i]
    end
    # Symmetrise just in case of FP drift.
    L = (L + L') / 2.0
    return L
end

# =====================================================================
# 5. Per-chunk bigram-frequency state vector (L¹-normalised)
# =====================================================================

function chunk_bigram_state(chunk::AbstractString,
                            token_to_slot::Dict{Int,Int},
                            n_nodes::Int)
    state = zeros(Float64, n_nodes)
    idxs = text_to_indices(chunk)
    bigrams = indices_to_bigrams(idxs)
    @inbounds for b in bigrams
        s = get(token_to_slot, b, -1)
        if s >= 0
            state[s+1] += 1.0
        end
    end
    total = sum(state)
    if total > 0.0
        state ./= total
    end
    return state
end

# =====================================================================
# 6. Spectral decomposition + cosine-on-real-coefficients similarity
# =====================================================================

# Project a state vector onto the Laplacian's eigenbasis: coeffs = V' * state.
function spectral_project(state::Vector{Float64}, eigvecs::Matrix{Float64})
    return eigvecs' * state
end

function cosine_real(a::Vector{Float64}, b::Vector{Float64})
    na = norm(a)
    nb = norm(b)
    if na == 0.0 || nb == 0.0
        return 0.0
    end
    return dot(a, b) / (na * nb)
end

# =====================================================================
# 7. Adversarial contrast generators (4 classes + held-out)
# =====================================================================

# These mirror parent's regex set. Julia regex follows PCRE2; the patterns are
# simple enough that semantics match Python's `re` module for our inputs.

const ARXIV_RE = r"arXiv:\s*(?:\d{4}\.\d{4,5}|[a-z\-]+/\d{7})"

const VALUE_PATTERNS = [
    (r"1/4", "7/3"),
    (r"0\.34439", "0.91234"),
    (r"0\.0104109", "0.7654321"),
    (r"d_geom", "q_phug"),
    (r"A/4", "B/9"),
    (r"7\.69%?", "31.42%"),
    (r"1\.78", "9.99"),
]

const VOCAB_PATTERNS = [
    (r"\bClass L\b", "Class Z"),
    (r"\bClass M\b", "Class Q"),
    (r"\bClass K\b", "Class W"),
    (r"\bClass C\b", "Class Y"),
    (r"\bClass I\b", "Class X"),
    (r"\bsrmech\b", "frobnication"),
    (r"\bspectral\b", "telegnostic"),
    (r"\bcascade\b", "phrenology"),
    (r"\bsubstrate\b", "ectoplasm"),
]

function adv_citation_swap(text::AbstractString, rng::AbstractRNG)
    return replace(text, ARXIV_RE => function(_m)
        yr = rand(rng, 1990:2098)
        nm = rand(rng, 0:99999)
        return @sprintf("arXiv:%d.%05d", yr, nm)
    end)
end

function adv_value_mutation(text::AbstractString)
    out = text
    for (pat, repl) in VALUE_PATTERNS
        out = replace(out, pat => repl)
    end
    return out
end

function adv_vocab_swap(text::AbstractString)
    out = text
    for (pat, repl) in VOCAB_PATTERNS
        out = replace(out, pat => repl)
    end
    return out
end

function adv_random_baseline(text::AbstractString, rng::AbstractRNG)
    chars = collect(text)
    shuffle!(rng, chars)
    return String(chars)
end

# =====================================================================
# 8. Chunking + Cohen's d
# =====================================================================

function chunk_text(text::AbstractString, chunk_size::Int = CHUNK_SIZE)
    out = String[]
    n = length(text)
    # Iterate by character (lowercase still keeps Unicode-safe in Julia String)
    chars = collect(text)
    nc = length(chars)
    i = 1
    while i <= nc
        upper = min(i + chunk_size - 1, nc)
        c = String(chars[i:upper])
        # Match parent's "keep chunks at least chunk_size//2 long"
        if length(c) >= div(chunk_size, 2)
            push!(out, c)
        end
        i += chunk_size
    end
    return out
end

function cohens_d(a::Vector{Float64}, b::Vector{Float64})
    va = var(a, corrected=true)
    vb = var(b, corrected=true)
    pooled = sqrt((va + vb) / 2.0)
    if pooled == 0.0
        return Inf
    end
    return (mean(a) - mean(b)) / pooled
end

# =====================================================================
# 9. Main experiment
# =====================================================================

function main()
    # Bit-exact: reseed for deterministic adversarial generation.
    Random.seed!(RNG_SEED)
    rng = MersenneTwister(RNG_SEED)

    println("=" ^ 72)
    println("Spike #125.1 — Julia bigram-cascade detector (Spike #125 follow-up)")
    println("=" ^ 72)

    corpus = load_attested_corpus()
    @printf("\nAttested corpus: %d chars from MFO + srmech notebooks\n", length(corpus))

    # ---- Build top-N bigram alphabet from full corpus ----
    selected_tokens, token_to_slot = topn_bigrams(corpus, TOP_N_BIGRAMS)
    n_nodes = length(selected_tokens)
    @printf("Top-N bigrams selected: %d (cap = %d)\n", n_nodes, TOP_N_BIGRAMS)

    # ---- Build bigram Laplacian once over full corpus ----
    L = bigram_cooc_laplacian(corpus, token_to_slot, n_nodes; window=COOC_WINDOW)
    @printf("Bigram Laplacian: %d x %d ; symmetric: %s\n",
            size(L, 1), size(L, 2), string(isapprox(L, L'; atol=1e-10)))

    # Eigendecomposition (symmetric -> use real eigen).
    # NOTE: This is O(n³); for n=1000 this is ~1e9 FLOPs — takes a moment.
    println("Eigendecomposing Laplacian (this is the slow step) ...")
    t0 = time()
    ef = eigen(Symmetric(L))
    t_eig = time() - t0
    @printf("  eigendecomposition time: %.2f s\n", t_eig)
    eigvecs = ef.vectors  # columns are eigenvectors

    # ---- Chunk full corpus, decompose attested chunks ----
    truth_chunks = chunk_text(corpus, CHUNK_SIZE)
    @printf("\nAttested chunks: %d of %d-char each\n", length(truth_chunks), CHUNK_SIZE)

    t0 = time()
    truth_coeffs = Vector{Vector{Float64}}(undef, length(truth_chunks))
    @inbounds for (i, c) in enumerate(truth_chunks)
        state = chunk_bigram_state(c, token_to_slot, n_nodes)
        truth_coeffs[i] = spectral_project(state, eigvecs)
    end
    t_decompose = time() - t0
    n_chars_truth = sum(length(c) for c in truth_chunks)
    @printf("Truth-fingerprint build: %d chunks; %.3f s; per-char %.2f us\n",
            length(truth_chunks), t_decompose,
            1e6 * t_decompose / n_chars_truth)

    # Reference fingerprint = centroid (mean) of attested coefficient vectors.
    ref = zeros(Float64, n_nodes)
    @inbounds for v in truth_coeffs
        ref .+= v
    end
    ref ./= length(truth_coeffs)

    # ---- Held-out 30% seed for adversarial generation ----
    nc = length(corpus)
    seed_start = floor(Int, HELD_OUT_FRAC == 0.30 ? 0.7 * nc : (1.0 - HELD_OUT_FRAC) * nc) + 1
    seed_text = corpus[seed_start:end]
    seed_chunks = chunk_text(seed_text, CHUNK_SIZE)
    @printf("\nAdversarial seed: %d chunks from held-out 30%%\n", length(seed_chunks))

    # Build the 5 contrast classes.
    adv_classes = [
        ("attested_held_out", seed_chunks),
        ("citation_swap",     [adv_citation_swap(c, rng) for c in seed_chunks]),
        ("value_mutation",    [adv_value_mutation(c) for c in seed_chunks]),
        ("vocab_swap",        [adv_vocab_swap(c) for c in seed_chunks]),
        ("random_baseline",   [adv_random_baseline(c, rng) for c in seed_chunks]),
    ]

    # ---- Per-class similarity to reference fingerprint ----
    println("\n--- Per-class spectral fingerprint similarity ---")
    @printf("%-22s %12s %14s %14s\n", "Class", "real_sim_mean", "real_sim_std", "n_chunks")

    class_sims = Dict{String,Vector{Float64}}()
    for (cname, chunks) in adv_classes
        sims = Float64[]
        for c in chunks
            state = chunk_bigram_state(c, token_to_slot, n_nodes)
            coeffs = spectral_project(state, eigvecs)
            push!(sims, cosine_real(ref, coeffs))
        end
        class_sims[cname] = sims
        @printf("%-22s %12.6f %14.6f %14d\n",
                cname, mean(sims), std(sims, corrected=true), length(sims))
    end

    # ---- Cohen's d: attested_held_out vs each adversarial ----
    println("\n--- Cohen's d (attested_held_out vs adversarial) ---")
    attested = class_sims["attested_held_out"]
    d_results = Dict{String,Float64}()
    for cname in ("citation_swap", "value_mutation", "vocab_swap", "random_baseline")
        d = cohens_d(attested, class_sims[cname])
        d_results[cname] = d
        verdict = if abs(d) >= 2.0; "DISCRIMINATES"
                  elseif abs(d) >= 0.5; "WEAK"
                  else; "NULL"; end
        @printf("  attested vs %-22s d = %+.4f   [%s]\n", cname, d, verdict)
    end

    # ---- Per-class verdict ----
    println("\n--- Per-class verdict ---")
    any_discriminates = false
    all_null = true
    for (cname, d) in d_results
        if abs(d) >= 0.5
            all_null = false
        end
        if abs(d) >= 0.5
            any_discriminates = true
        end
    end
    composite = if all_null
        "BIGRAM-NULLS-TOO"
    elseif any_discriminates && !all_null
        # If any class is NULL and any discriminates: PARTIAL
        any_null = any(abs(d) < 0.5 for d in values(d_results))
        any_null ? "BIGRAM-PARTIAL" : "BIGRAM-DISCRIMINATES"
    else
        "BIGRAM-UNKNOWN"
    end
    @printf("\n>>> Composite verdict: %s\n", composite)

    println()
    println("=" ^ 72)
    println("Spike #125.1: bigram-cascade detector COMPLETE")
    println("=" ^ 72)

    return Dict(
        "verdict" => composite,
        "cohens_d" => d_results,
        "class_sim_means" => Dict(k => mean(v) for (k, v) in class_sims),
        "class_sim_stds" => Dict(k => std(v, corrected=true) for (k, v) in class_sims),
        "n_nodes" => n_nodes,
        "n_truth_chunks" => length(truth_chunks),
        "n_seed_chunks" => length(seed_chunks),
        "eigendecompose_s" => t_eig,
    )
end

# Run twice and print whether outputs match exactly (bit-exact reproducibility).
function reproducibility_check()
    println("\n--- Bit-exact reproducibility check (running twice) ---")
    r1 = main()
    println("\n... second run ...\n")
    r2 = main()
    # Compare Cohen's d values byte-exact.
    same = all(r1["cohens_d"][k] === r2["cohens_d"][k] for k in keys(r1["cohens_d"]))
    @printf("\nCohen's d identical across runs: %s\n", string(same))
    return r1
end

if abspath(PROGRAM_FILE) == @__FILE__
    main()
end
