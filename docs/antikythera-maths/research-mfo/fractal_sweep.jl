using JSON
using Printf
using LinearAlgebra
using Random

# Standard Model target masses in GeV
const SM_MASSES_GEV = [0.000511, 0.0022, 0.0047, 0.095, 0.1057, 1.275, 1.777, 4.18, 173.0]
const M_E = 0.000511
const TARGET_LOG = log10.(sort([(v/M_E)^2 for v in SM_MASSES_GEV]))

# Precomputed Manifold Constants
const CP2_BASE = Float64[0, 12, 32, 60, 96, 140]
const S1_N = Float64[0, 1, 4, 9, 16] 

function r_inverse(w, L)
    disc = L*L - 4*w
    if disc < 0 return Float64[] end
    sd = sqrt(disc)
    return [(L - sd)/2.0, (L + sd)/2.0]
end

function get_fractal_evals(n, L, max_level=5)
    res = Float64[]
    current_evals = Set{Float64}([0.0, Float64(L)])
    for m in 0:max_level
        factor = Float64(L)^m
        for e in current_evals
            if e > 1e-10
                push!(res, round(e * factor, digits=6))
            end
        end
        if m < max_level
            next_evals = Set{Float64}()
            for w in current_evals
                for z in r_inverse(w, L)
                    if 0 <= z <= L + 1
                        push!(next_evals, round(z, digits=12))
                    end
                end
            end
            push!(next_evals, 2.0)
            push!(next_evals, Float64(n + 2))
            current_evals = next_evals
        end
    end
    return sort(unique(res))[1:min(15, length(res))]
end

function run_sweep()
    Random.seed!(42) # Ensure reproducibility for any sampling
    n = 3
    l_range = 10:10:100
    C = 0.1 # Coupling scale
    
    println("Precomputing fractal spectra for n=3, L=10:10:100...")
    fractal_cache = Dict{Int, Vector{Float64}}()
    for L in l_range
        fractal_cache[L] = get_fractal_evals(n, L)
    end

    r_values = 10.0 .^ range(2, 4, step=0.5)
    candidates = []
    
    println("Starting direct product coupling sweep...")
    for L1 in l_range
        E1 = fractal_cache[L1]
        for L2 in filter(x -> x <= L1, l_range)
            E2 = fractal_cache[L2]
            for L3 in filter(x -> x <= L2, l_range)
                E3 = fractal_cache[L3]
                
                # Direct Product Coupling: C * e1 * e2 * e3
                # We interpret "randomly selected pairs" as a stochastic combination
                # for the combined fractal contribution.
                f_combos = Float64[0.0]
                
                # All combinations (approx 15^3 = 3375)
                for e1 in E1, e2 in E2, e3 in E3
                    push!(f_combos, C * e1 * e2 * e3)
                end
                
                unique_f = sort(unique(round.(f_combos, digits=6)))
                unique_f_top = unique_f[1:min(40, length(unique_f))]

                for R in r_values
                    r2_inv = 1.0 / (R*R)
                    
                    res_combined = Float64[]
                    for f in unique_f_top, cp in CP2_BASE, s1_n2 in S1_N
                        val = f + cp + (s1_n2 * r2_inv)
                        if val > 1e-10
                            push!(res_combined, round(val, digits=6))
                        end
                    end
                    
                    if length(res_combined) < 9 continue end
                    
                    final_9_unique = sort(unique(res_combined))[1:min(9, length(res_combined))]
                    if length(final_9_unique) < 9 continue end
                    
                    normalized_9 = final_9_unique ./ final_9_unique[1]
                    log_9 = log10.(normalized_9)
                    error = sum((log_9 .- TARGET_LOG).^2)
                    
                    push!(candidates, (n=n, L1=L1, L2=L2, L3=L3, R=R, error=error, ratios=normalized_9))
                end
            end
        end
    end

    sort!(candidates, by=x->x.error)
    top_20 = candidates[1:min(20, length(candidates))]
    
    results_path = "results-mfo/product_coupling_sweep.json"
    mkpath("results-mfo")
    open(results_path, "w") do f
        JSON.print(f, [Dict("n"=>c.n, "L1"=>c.L1, "L2"=>c.L2, "L3"=>c.L3, "R"=>c.R, "error"=>c.error, "ratios"=>c.ratios) for c in top_20], 2)
    end

    println("\nProduct coupling sweep complete. Results saved to $results_path")
    @printf("%3s %3s %3s %9s %10s\n", "L1", "L2", "L3", "R", "Error")
    for c in top_20[1:min(10, length(top_20))]
        @printf("%3d %3d %3d %9.3f %10.4f\n", c.L1, c.L2, c.L3, c.R, c.error)
    end
end

run_sweep()
