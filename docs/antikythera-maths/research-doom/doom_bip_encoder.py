import numpy as np

class Phase9BIP:
    """
    Phase-9 BIP (Bit-Interleaved Phases) Encoder.
    Translates DOOM spatial motion into resonant HDC states.
    Uses coprime rolls (67, 7 mod D) for spatial uniqueness.
    """
    def __init__(self, D=512):
        self.D = D
        # Coprime shift constants
        self.SHIFT_X = 67
        self.SHIFT_Y = 7
        
        # Base phases for X and Y axes
        # Initialized as random bipolar vectors {-1, 1}^D
        rng = np.random.default_rng(42)
        self.phi_x = rng.choice([-1, 1], size=D)
        self.phi_y = rng.choice([-1, 1], size=D)

    def encode_position(self, x, y):
        """
        Encodes a (fixed-point) coordinate into a hypervector.
        H = (phi_x roll (x * SHIFT_X)) * (phi_y roll (y * SHIFT_Y))
        """
        # We treat x, y as integer indices (BAM/Fixed-point units)
        # and use them to drive the cyclic shifts.
        ix = int(x) % self.D
        iy = int(y) % self.D
        
        hx = np.roll(self.phi_x, ix * self.SHIFT_X)
        hy = np.roll(self.phi_y, iy * self.SHIFT_Y)
        
        return hx * hy # Element-wise binding (XOR in bipolar)

    def get_velocity_operator(self, vx, vy):
        """
        Creates a transition operator that advances the state by velocity.
        """
        # In BIP, velocity is a state-space rotation
        pass

if __name__ == "__main__":
    bip = Phase9BIP(D=512)
    
    # Position A
    pos_a = (100, 200)
    ha = bip.encode_position(*pos_a)
    
    # Position B (Nearby)
    pos_b = (101, 200)
    hb = bip.encode_position(*pos_b)
    
    # Position C (Far away)
    pos_c = (500, 800)
    hc = bip.encode_position(*pos_c)
    
    # Similarity (Dot product)
    sim_ab = np.dot(ha, hb) / bip.D
    sim_ac = np.dot(ha, hc) / bip.D
    
    print(f"BIP Encoding (D={bip.D}):")
    print(f"  Similarity A-B (Adjacent): {sim_ab:.4f}")
    print(f"  Similarity A-C (Distant):  {sim_ac:.4f}")
    
    # Save a representation to results-doom
    np.save("docs/antikythera-maths/results-doom/e1m1_bip_sample.npy", ha)
    print("\nSaved sample BIP state to results-doom/e1m1_bip_sample.npy")
