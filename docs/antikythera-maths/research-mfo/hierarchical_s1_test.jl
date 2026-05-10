using JSON
using Printf
using LinearAlgebra
using Random

# Guarantee byte-deterministic output
BLAS.set_num_threads(1)
Random.seed!(12345)

# Standard Model target mass-squared ratios relative to electron
const SM_MASSES_GEV = Dict(
    "electron" => 0.000511,
    "up" => 0.0022,
    "down" => 0.0047,
    "strange" => 0.095,
    "muon" => 0.1057,
    "charm" => 1.275,
    "tau" => 1.777,
    "bottom" => 4.18,
    "top" => 173.0,
)

const M_E = 0.000511
const SM_NAMES = ["electron", "up", "down", "strange", "muon", "charm", "tau", "bottom", "top"]
const TARGET_LOG = [log10((SM_MASSES_GEV[name]/M_E)^2) for name in SM_NAMES]

# Fixed parameters from the best previous model
const S = 0.297479
const R = 1000.0
const S1_UNIT = 1.0 / (R^2)

# Fixed fractal anchors (L=5, Level 5)
const ANCHORS = [
    0.0000,   # electron
    0.4384,   # up
    0.4384,   # down
    1.3557,   # strange
    1.3767,   # muon
    2.0000,   # charm
    2.0000,   # tau
    2.0000,   # bottom
    3.6180    # top
]

function run_hierarchical_s1_jl()
    total_error = 0.0
    assignments = []
    
    println("Hierarchical S1 Assignment Sweep (Julia, Deterministic)")
    @printf("%10s %12s %10s %6s %12s %10s\n", "Particle", "Target Log", "Base λ", "Best n", "Final Log", "Error")
    
    for i in 1:9
        target = TARGET_LOG[i]
        base_lam = ANCHORS[i]
        
        best_n = 0
        min_err = Inf
        best_log_pred = 0.0
        
        for n in 0:5
            log_pred = (base_lam + (n^2 * S1_UNIT)) / S
            err = (log_pred - target)^2
            if err < min_err
                min_err = err
                best_n = n
                best_log_pred = log_pred
            end
        end
        
        total_error += min_err
        push!(assignments, (name=SM_NAMES[i], n=best_n, log_pred=best_log_pred, err=min_err))
        
        @printf("%10s %12.4f %10.4f %6d %12.4f %10.4f\n", SM_NAMES[i], target, base_lam, best_n, best_log_pred, min_err)
    end
    
    results = Dict(
        "total_error" => total_error,
        "assignments" => assignments
    )
    
    mkpath("results-mfo")
    open("results-mfo/hierarchical_s1_assignment_jl.json", "w") do f
        JSON.print(f, results, 2)
    end
    
    @printf("\nFinal Total Error: %.6f\n", total_error)
end

run_hierarchical_s1_jl()
