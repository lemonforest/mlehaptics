import numpy as np

class BAMKinematics:
    """
    Implements ALU-native kinematics using 16.16 fixed-point and 32-bit BAM angles.
    """
    FRACBITS = 16
    FRACUNIT = 1 << FRACBITS
    MAX_INT = 0xFFFFFFFF

    def __init__(self, x=0, y=0, angle=0):
        # Position in 16.16 fixed point
        self.x = int(x * self.FRACUNIT) & self.MAX_INT
        self.y = int(y * self.FRACUNIT) & self.MAX_INT
        # Angle in 32-bit BAM (0 to 2^32-1)
        self.angle = int(angle) & self.MAX_INT

    def move(self, velocity_fixed, angle_bam):
        """
        Move the entity using fixed-point trig lookups (simulated here).
        """
        # In DOOM, cos/sin are precomputed LUTs.
        # We simulate this with float math then convert back to fixed.
        angle_rad = (angle_bam / self.MAX_INT) * 2 * np.pi
        dx = int(velocity_fixed * np.cos(angle_rad))
        dy = int(velocity_fixed * np.sin(angle_rad))
        
        self.x = (self.x + dx) & self.MAX_INT
        self.y = (self.y + dy) & self.MAX_INT

    def slide_move(self, velocity_fixed, angle_bam, wall_normal_bam):
        """
        Wall sliding: project velocity onto the wall's tangent.
        """
        # Velocity vector
        angle_rad = (angle_bam / self.MAX_INT) * 2 * np.pi
        vx = velocity_fixed * np.cos(angle_rad)
        vy = velocity_fixed * np.sin(angle_rad)
        
        # Wall normal vector
        norm_rad = (wall_normal_bam / self.MAX_INT) * 2 * np.pi
        nx = np.cos(norm_rad)
        ny = np.sin(norm_rad)
        
        # Dot product
        dot = vx * nx + vy * ny
        
        # Sliding velocity = V - (V . N) * N
        svx = int(vx - dot * nx)
        svy = int(vy - dot * ny)
        
        self.x = (self.x + svx) & self.MAX_INT
        self.y = (self.y + svy) & self.MAX_INT

    def get_pos(self):
        return self.x / self.FRACUNIT, self.y / self.FRACUNIT

if __name__ == "__main__":
    kin = BAMKinematics(x=10, y=10)
    
    # Move forward at 45 degrees
    # 45 deg = 2^32 / 8 = 0x20000000
    angle_45 = 0x20000000
    vel = 5 * BAMKinematics.FRACUNIT
    
    kin.move(vel, angle_45)
    print("Pos after move:", kin.get_pos())
    
    # Hit a vertical wall (Normal is 180 degrees = 0x80000000)
    # Trying to move at 45 degrees into it
    wall_norm = 0x80000000
    kin.slide_move(vel, angle_45, wall_norm)
    print("Pos after slide move:", kin.get_pos())
