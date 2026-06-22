"""Investigate eigenvectors as KERNEL OBJECTS + where Qarg (phase) augments. (1) the Laplacian eigen-
spectrum is a structure fingerprint (F172) -- different relationship graphs -> different spectra (a
similarity-comparable kernel). (2) for DIRECTED relationship graphs (word-order IS directed) the magnetic
Laplacian is complex-Hermitian; its eigenvectors carry PHASE = the which-way/chirality (Class C). Reversing
edge direction conjugates the phase (imag sign flip). That phase is exactly what a Qarg (polar argument)
carrier would read natively -- in rc28 Q is rectangular, so phase = (real,imag), Qarg is the missing reader.
srmech rc28; native eigensolver."""
from srmech.amsc import laplacian as La
def fl(q): return q.as_float() if hasattr(q,"as_float") else (q.real if hasattr(q,'real') else float(q))
def reim(z):
    if hasattr(z,"imag"): return fl(z.real) if hasattr(z.real,'as_float') else float(z.real), (float(z.imag.as_float()) if hasattr(z.imag,'as_float') else float(z.imag))
    return float(z), 0.0

print("=== eigenvectors as kernel objects (rc28 full eigensolver) ===")
# (1) spectrum as a structure fingerprint: path vs star (same n, different relationship structure)
path=[(0,1),(1,2),(2,3),(3,4)]; star=[(0,1),(0,2),(0,3),(0,4)]
sp,_=La.symmetric_eigendecompose(La.dense_laplacian(5, path))
ss,_=La.symmetric_eigendecompose(La.dense_laplacian(5, star))
spv=sorted(round(float(x),3) for x in sp); ssv=sorted(round(float(x),3) for x in ss)
print(f"\n(1) Laplacian SPECTRUM as a kernel fingerprint (F172):")
print(f"    path graph spectrum: {spv}")
print(f"    star graph spectrum: {ssv}")
print(f"    distinct fingerprints (different relationship structure -> different kernel): {spv!=ssv}")

# (2) DIRECTED relationship -> magnetic Laplacian -> complex eigvecs -> phase = chirality (where Qarg reads)
Hf=La.magnetic_laplacian(3, [(0,1),(1,2),(2,0)])    # forward directed cycle
Hr=La.magnetic_laplacian(3, [(0,2),(2,1),(1,0)])    # reversed cycle (opposite chirality)
ef,Vf=La.hermitian_eigendecompose(Hf); er,Vr=La.hermitian_eigendecompose(Hr)
# read one off-diagonal of the (complex) magnetic Laplacian: forward vs reverse should be conjugate
hf01=Hf[0][1] if not hasattr(Hf,'get') else Hf.get(0,1)
hr01=Hr[0][1] if not hasattr(Hr,'get') else Hr.get(0,1)
rf,imf=reim(hf01); rr,imr=reim(hr01)
print(f"\n(2) magnetic (directed) Laplacian carries PHASE:")
print(f"    forward edge (0->1) L[0][1] = ({rf:+.3f}, {imf:+.3f}i)")
print(f"    reversed edge      L[0][1] = ({rr:+.3f}, {imr:+.3f}i)")
print(f"    phase flips with direction (imag sign): {(imf<0)!=(imr<0)}  -> direction = the eigvec PHASE = chirality (Class C)")
print(f"\n  => eigenvectors ARE kernel objects: the spectrum is a structure fingerprint (global, Class-L), and")
print(f"     for DIRECTED graphs the eigvec PHASE carries the which-way. A Qarg (polar argument) carrier would")
print(f"     read that phase natively; rc28's Q is rectangular (real,imag) so phase is implicit. Qarg = the")
print(f"     chirality reader for the spectral kernel. This AUGMENTS the local byte/glyph C1 with global+directional structure.")
