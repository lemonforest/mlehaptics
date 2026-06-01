"""mass_spec_fft.py — F280: FFT confirms the user's guess about the flattened mass chart.

User guess (2026-06-02): "if we can create a fully projected view of every mass item,
then we can FFT what looks like a flattened chart with known elements and compounds."

Two reasons it's right, both shown here:
  A) The neutral-loss DIFFERENCE-GRAPH (the F279 fiber) IS the autocorrelation of the
     spectrum. Wiener-Khinchin: autocorr = IFFT(|FFT(spectrum)|^2). So FFT of the flat
     chart directly surfaces the recurring Δm/z (the neutral losses) -- the fiber falls
     out of the chart's own power spectrum.
  B) ISOTOPE envelopes are CONVOLUTIONS (a molecule's pattern = convolution of each
     atom's isotope distribution). FFT turns convolution into MULTIPLICATION, so a
     fully-projected library of elements composes multiplicatively in FFT-domain:
     any compound's envelope = product of its elements' FFTs. (= Rockwood's FFT
     isotope method; field's, not ours -- we read WHY it works.)

Together: a fully-projected FFT-domain library + a flat chart -> matching/deconvolution
is multiplication/correlation in FFT-domain, and the difference-fiber is the autocorr.

SCOPE: framework-reading; benign textbook examples (ethanol; abstract C/Cl isotope
math); NO unknown-ID/detection/synthesis -- only the math structure. No-lineage. FFT
is numpy signal-processing (not a bypassed srmech primitive; the eigen/Laplacian side
stays srmech). Class-K clean (|F|^2 = F*conj(F), no abs()).
"""
import numpy as np

NEUTRALS = {1: "H", 2: "H2", 4: "(2H2)", 14: "CH2", 15: "CH3", 16: "O/CH4",
            17: "OH", 18: "H2O", 19: "(F/H3O)", 28: "CO", 29: "CHO"}


def main():
    # ---- A) FFT autocorrelation recovers the neutral-loss difference-fiber ----
    print("=== A) FFT of the flat chart recovers the difference-graph fiber (Wiener-Khinchin) ===")
    mz_max = 64
    spec = np.zeros(mz_max)
    for p in [46, 45, 31, 29, 27]:          # the FLAT chart, as a sparse peak vector
        spec[p] = 1.0
    F = np.fft.fft(spec)
    autocorr = np.real(np.fft.ifft(F * np.conj(F)))   # |F|^2 = F*conj(F) (no abs); IFFT = autocorr
    print(f"  autocorr[0] = {autocorr[0]:.0f}  (= number of peaks)")
    print("  recurring Δm/z (autocorr lags > 0) = the neutral losses the flat chart drops:")
    for d in range(1, 31):
        if autocorr[d] > 0.5:
            tag = NEUTRALS.get(d, "?")
            print(f"    Δ{d:<3} count={autocorr[d]:.0f}  lose {tag}")
    print("  -> the FFT power spectrum recovers F279's hand-built difference-graph, natively.\n")

    # ---- B) isotope envelopes are convolutions -> FFT makes the library composable ----
    print("=== B) isotope envelope = convolution -> FFT = multiplication (composable library) ===")
    pC = np.array([0.9893, 0.0107])          # 12C / 13C (attested-B, IUPAC)
    pCl = np.array([0.7577, 0.0, 0.2423])    # 35Cl / -- / 37Cl (attested-B)

    def conv_n(p, n):
        out = np.array([1.0])
        for _ in range(n):
            out = np.convolve(out, p)
        return out

    env3 = conv_n(pC, 3)                      # 3-carbon envelope (binomial)
    L = len(env3)
    pCp = np.zeros(L); pCp[:2] = pC
    via_fft = np.real(np.fft.ifft(np.fft.fft(pCp) ** 3))[:L]   # FFT^3 == 3-fold convolution
    print(f"  3-carbon envelope via convolution: {np.round(env3, 5)}")
    print(f"  same via FFT(p)^3:                  {np.round(via_fft, 5)}   match={np.allclose(env3, via_fft)}")

    # library composition: a 1-C + 1-Cl compound's envelope = product of element FFTs (= convolution)
    env = np.convolve(pC, pCl)
    print(f"\n  (1 C + 1 Cl) compound envelope [M, M+1, M+2, M+3] = {np.round(env, 4)}")
    print(f"    M+1/M = {env[1]/env[0]*100:.2f}%  -> decodes {round(env[1]/env[0]/0.0107)} carbon")
    print(f"    M+2/M = {env[2]/env[0]*100:.1f}%  -> the ~3:1 (M:M+2) chlorine signature ({env[0]/env[2]:.2f}:1)")
    print("  -> a fully-projected element library composes by FFT-product into any compound's")
    print("     envelope, and the envelope DECODES composition. The flat chart shows these peaks")
    print("     but not the decode; the FFT-domain library is the un-flattened, no-data-lost form.\n")

    print("--- verdict: the guess holds ---")
    print("  Fully-projected library + FFT: (A) the difference-fiber IS the chart's autocorrelation,")
    print("  (B) the library composes multiplicatively (convolution->product). So matching/")
    print("  deconvolving a flat chart against knowns is multiplication/correlation in FFT-domain,")
    print("  and nothing is flattened away -- the fiber is recoverable from the transform itself.")


if __name__ == "__main__":
    main()
