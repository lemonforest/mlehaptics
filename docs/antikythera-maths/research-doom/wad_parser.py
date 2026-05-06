import struct
import numpy as np

class WadParser:
    def __init__(self, wad_path):
        self.wad_path = wad_path
        with open(wad_path, 'rb') as f:
            self.data = f.read()
        
        self.magic = self.data[:4].decode('ascii')
        self.num_lumps = struct.unpack('<I', self.data[4:8])[0]
        self.dir_offset = struct.unpack('<I', self.data[8:12])[0]
        
        self.directory = {}
        self.lump_list = []
        for i in range(self.num_lumps):
            off = self.dir_offset + i * 16
            l_off = struct.unpack('<I', self.data[off:off+4])[0]
            l_size = struct.unpack('<I', self.data[off+4:off+8])[0]
            l_name = self.data[off+8:off+16].split(b'\x00')[0].decode('ascii')
            self.directory[l_name] = (l_off, l_size)
            self.lump_list.append({'name': l_name, 'offset': l_off, 'size': l_size})

    def get_lump(self, name):
        if name in self.directory:
            off, size = self.directory[name]
            return self.data[off:off+size]
        return None

    def get_level_lumps(self, level_name):
        """Returns a dict of lumps for a specific level (e.g. E1M1)"""
        level_idx = -1
        for i, lump in enumerate(self.lump_list):
            if lump['name'] == level_name:
                level_idx = i
                break
        
        if level_idx == -1:
            return None
        
        lumps = {}
        # Level lumps follow the level name lump
        level_lump_names = ['THINGS', 'LINEDEFS', 'SIDEDEFS', 'VERTEXES', 'SEGS', 'SSECTORS', 'NODES', 'SECTORS', 'REJECT', 'BLOCKMAP']
        for i in range(1, 11):
            lump = self.lump_list[level_idx + i]
            if lump['name'] in level_lump_names:
                lumps[lump['name']] = self.data[lump['offset'] : lump['offset'] + lump['size']]
        return lumps

    def parse_sectors(self, sector_data):
        sectors = []
        for i in range(0, len(sector_data), 26):
            s = sector_data[i:i+26]
            floor = struct.unpack('<h', s[0:2])[0]
            ceil = struct.unpack('<h', s[2:4])[0]
            sectors.append({'id': i // 26, 'floor': floor, 'ceiling': ceil})
        return sectors

    def parse_sidedefs(self, side_data):
        sides = []
        for i in range(0, len(side_data), 30):
            s = side_data[i:i+30]
            sec_idx = struct.unpack('<h', s[28:30])[0]
            sides.append({'sector': sec_idx})
        return sides

    def parse_linedefs(self, line_data):
        lines = []
        for i in range(0, len(line_data), 14):
            l = line_data[i:i+14]
            v1 = struct.unpack('<h', l[0:2])[0]
            v2 = struct.unpack('<h', l[2:4])[0]
            s1 = struct.unpack('<H', l[10:12])[0]
            s2 = struct.unpack('<H', l[12:14])[0]
            lines.append({'v1': v1, 'v2': v2, 'side_f': s1, 'side_b': s2})
        return lines

    def build_sector_graph(self, level_name):
        lumps = self.get_level_lumps(level_name)
        sectors = self.parse_sectors(lumps['SECTORS'])
        sides = self.parse_sidedefs(lumps['SIDEDEFS'])
        lines = self.parse_linedefs(lumps['LINEDEFS'])
        
        num_sectors = len(sectors)
        adj = np.zeros((num_sectors, num_sectors))
        
        for line in lines:
            if line['side_f'] != 0xFFFF and line['side_b'] != 0xFFFF:
                s1 = sides[line['side_f']]['sector']
                s2 = sides[line['side_b']]['sector']
                if s1 < num_sectors and s2 < num_sectors:
                    adj[s1, s2] = 1
                    adj[s2, s1] = 1
        
        return sectors, adj

if __name__ == "__main__":
    wad = WadParser("docs/antikythera-maths/research-doom/DOOM1.WAD")
    print(f"WAD Magic: {wad.magic}, Lumps: {wad.num_lumps}")
    
    sectors, adj = wad.build_sector_graph("E1M1")
    print(f"E1M1 Sectors: {len(sectors)}")
    print(f"Adjacency Matrix Shape: {adj.shape}")
    print(f"Connections: {int(np.sum(adj) / 2)}")
