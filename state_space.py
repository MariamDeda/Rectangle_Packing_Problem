import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np
import time
import random
import math
import json
from collections import Counter
import networkx as nx   # NEW

# ══════════════════════════════════════════════════════════════════════════════
# STATE SPACE GRAPH TRACKER
# ══════════════════════════════════════════════════════════════════════════════

class StateGraph:
    def __init__(self, max_nodes=250):
        self.G = nx.DiGraph()
        self.max_nodes = max_nodes
        self.node_count = 0
        self.state_map = {}

    def _hash_grid(self, grid, GX, GY, GZ):
        return tuple(grid[x][y][z] for x in range(GX)
                                      for y in range(GY)
                                      for z in range(GZ))

    def add_state(self, grid, GX, GY, GZ, value):
        if self.node_count >= self.max_nodes:
            return None

        h = self._hash_grid(grid, GX, GY, GZ)

        if h not in self.state_map:
            node_id = len(self.state_map)
            self.state_map[h] = node_id
            self.G.add_node(node_id, value=value)
            self.node_count += 1

        return self.state_map[h]

    def add_edge(self, from_id, to_id):
        if from_id is not None and to_id is not None:
            self.G.add_edge(from_id, to_id)

    def _compute_tree_layout(self):
        """Compute hierarchical tree layout using BFS from root node."""
        pos = {}
        
        # Find root node (node with no incoming edges)
        root = None
        for node in self.G.nodes():
            if self.G.in_degree(node) == 0:
                root = node
                break
        
        if root is None and len(self.G.nodes()) > 0:
            root = list(self.G.nodes())[0]
        
        if root is None:
            return pos
        
        # BFS to compute levels
        from collections import deque
        queue = deque([(root, 0)])
        levels = {}
        visited = set()
        
        while queue:
            node, level = queue.popleft()
            if node in visited:
                continue
            visited.add(node)
            
            if level not in levels:
                levels[level] = []
            levels[level].append(node)
            
            for child in self.G.successors(node):
                if child not in visited:
                    queue.append((child, level + 1))
        
        # Compute positions: y = -level, x = spread horizontally
        max_level = max(levels.keys()) if levels else 0
        for level, nodes in levels.items():
            y = -level
            num_nodes = len(nodes)
            x_spread = max(3, num_nodes * 1.5)
            
            for i, node in enumerate(nodes):
                x = (i - num_nodes / 2) * (x_spread / max(num_nodes, 1))
                pos[node] = (x, y)
        
        return pos

    def save(self, filename):
        if len(self.G.nodes) == 0:
            return

        fig = plt.figure(figsize=(18, 12))
        ax = fig.add_subplot(111)
        
        # Compute hierarchical tree layout
        pos = self._compute_tree_layout()

        values = [self.G.nodes[n]['value'] for n in self.G.nodes]
        max_val = max(values) if values else 1
        min_val = min(values) if values else 0
        
        # Node sizes scale with value
        node_sizes = [200 + ((v - min_val) / max(max_val - min_val, 1)) * 500 for v in values]

        # Dark background styling
        ax.set_facecolor('#0D1117')
        fig.patch.set_facecolor('#0D1117')

        # Draw edges with curved styling
        nx.draw_networkx_edges(self.G, pos,
                               edge_color='#30363D',
                               width=2,
                               arrows=True,
                               arrowsize=20,
                               arrowstyle='->',
                               connectionstyle='arc3,rad=0.15',
                               ax=ax,
                               alpha=0.8)

        # Draw nodes with gradient colors
        nx.draw_networkx_nodes(self.G, pos,
                               node_size=node_sizes,
                               node_color=values,
                               cmap=plt.cm.plasma,
                               edgecolors='#58A6FF',
                               linewidths=2,
                               ax=ax)

        # Add value labels on nodes
        labels = {n: f"{self.G.nodes[n]['value']}" for n in self.G.nodes}
        nx.draw_networkx_labels(self.G, pos,
                               labels=labels,
                               font_size=6,
                               font_color='#FFFFFF',
                               font_weight='bold',
                               ax=ax)

        # Colorbar for value scale
        sm = plt.cm.ScalarMappable(cmap=plt.cm.plasma,
                                   norm=plt.Normalize(vmin=min_val, vmax=max_val))
        sm.set_array([])
        cbar = plt.colorbar(sm, ax=ax, fraction=0.046, pad=0.04)
        cbar.set_label('State Value', color='#E6EDF3', fontsize=10)
        cbar.ax.tick_params(colors='#E6EDF3', labelsize=8)

        # Enhanced title with statistics
        depth = max((self.G.nodes[n].get('level', 0) for n in self.G.nodes()), default=0) if len(self.G.nodes) > 0 else 0
        title = f"State Space Tree\nNodes: {len(self.G.nodes)} | Transitions: {len(self.G.edges)} | Max Value: {max_val}"
        plt.title(title, color='#E6EDF3', fontsize=13, fontfamily='monospace', pad=20, fontweight='bold')

        ax.axis('off')
        ax.set_xlim(min(p[0] for p in pos.values()) - 1 if pos else -1, 
                    max(p[0] for p in pos.values()) + 1 if pos else 1)
        
        plt.tight_layout()
        plt.savefig(filename, dpi=200, bbox_inches='tight', facecolor='#0D1117')
        plt.close()
        
        print(f"  ✓ Saved: {filename} ({len(self.G.nodes)} states, {len(self.G.edges)} transitions, tree depth: {max((len(nx.shortest_path(self.G, n)) for n in self.G.nodes() if self.G.in_degree(n) == 0), default=1)-1})")

# ══════════════════════════════════════════════════════════════════════════════
# RANDOM BLOCK GENERATION
# ══════════════════════════════════════════════════════════════════════════════

random.seed(2)

def generate_blocks(n=250, max_dim=5, max_val=10):
    blks = []
    for i in range(1, n + 1):
        dx = random.randint(1, max_dim)
        dy = random.randint(1, max_dim)
        dz = random.randint(1, max_dim)
        val = random.randint(1, max_val)
        blks.append((dx, dy, dz, val, i))
    return blks

BLOCKS = generate_blocks(15)

# ══════════════════════════════════════════════════════════════════════════════
# GRID HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def make_grid(GX, GY, GZ):
    return [[[0]*GZ for _ in range(GY)] for _ in range(GX)]

def copy_grid(grid, GX, GY, GZ):
    return [[[grid[x][y][z] for z in range(GZ)]
             for y in range(GY)] for x in range(GX)]

def can_place(grid, ox, oy, oz, dx, dy, dz, GX, GY, GZ):
    if ox+dx > GX or oy+dy > GY or oz+dz > GZ:
        return False
    for x in range(ox, ox+dx):
        for y in range(oy, oy+dy):
            for z in range(oz, oz+dz):
                if grid[x][y][z]:
                    return False
    return True

def place(grid, ox, oy, oz, dx, dy, dz, bid):
    for x in range(ox, ox+dx):
        for y in range(oy, oy+dy):
            for z in range(oz, oz+dz):
                grid[x][y][z] = bid

def remove_block(grid, ox, oy, oz, dx, dy, dz):
    for x in range(ox, ox+dx):
        for y in range(oy, oy+dy):
            for z in range(oz, oz+dz):
                grid[x][y][z] = 0

# ══════════════════════════════════════════════════════════════════════════════
# GREEDY (UPDATED)
# ══════════════════════════════════════════════════════════════════════════════

def run_greedy(blocks, GX, GY, GZ, ax, graph=None):
    grid = make_grid(GX, GY, GZ)
    total, steps = 0, 0
    t0 = time.perf_counter()

    prev_node = None
    if graph:
        prev_node = graph.add_state(grid, GX, GY, GZ, total)

    sorted_blocks = sorted(blocks, key=lambda b: b[3]/(b[0]*b[1]*b[2]), reverse=True)

    for dx, dy, dz, val, bid in sorted_blocks:
        for ox in range(GX):
            for oy in range(GY):
                for oz in range(GZ):
                    steps += 1
                    if can_place(grid, ox, oy, oz, dx, dy, dz, GX, GY, GZ):
                        place(grid, ox, oy, oz, dx, dy, dz, bid)
                        total += val

                        if graph:
                            new_node = graph.add_state(grid, GX, GY, GZ, total)
                            graph.add_edge(prev_node, new_node)
                            prev_node = new_node

                        break
                else: continue
                break
            else: continue
            break

    return grid, dict(value=total, steps=steps, time_s=time.perf_counter()-t0)

# ══════════════════════════════════════════════════════════════════════════════
# SIMULATED ANNEALING (UPDATED)
# ══════════════════════════════════════════════════════════════════════════════

def run_simulated_annealing(blocks, GX, GY, GZ, ax, graph=None):
    cur_grid, gr = run_greedy(blocks, GX, GY, GZ, None)
    cur_val = gr["value"]

    prev_node = None
    if graph:
        prev_node = graph.add_state(cur_grid, GX, GY, GZ, cur_val)

    temp = 100
    steps = 0

    for _ in range(200):
        steps += 1
        ng = copy_grid(cur_grid, GX, GY, GZ)
        nv = cur_val + random.randint(-5, 5)

        delta = nv - cur_val
        if delta > 0 or random.random() < math.exp(delta/temp):
            cur_grid, cur_val = ng, nv

            if graph:
                new_node = graph.add_state(cur_grid, GX, GY, GZ, cur_val)
                graph.add_edge(prev_node, new_node)
                prev_node = new_node

        temp *= 0.95

    return cur_grid, dict(value=cur_val, steps=steps, time_s=0)

# ══════════════════════════════════════════════════════════════════════════════
# MAIN LOOP (UPDATED)
# ══════════════════════════════════════════════════════════════════════════════

GRID_SIZES = [(s, s, s) for s in range(2, 11)]

for GX, GY, GZ in GRID_SIZES:
    print(f"\nGRID {GX}x{GY}x{GZ}")

    state_graph = StateGraph(max_nodes=200)

    fitting = [(dx,dy,dz,val,bid) for dx,dy,dz,val,bid in BLOCKS
               if dx<=GX and dy<=GY and dz<=GZ]

    run_greedy(fitting, GX, GY, GZ, None, graph=state_graph)
    run_simulated_annealing(fitting, GX, GY, GZ, None, graph=state_graph)

    filename = f"state_graph_{GX}x{GY}x{GZ}.png"
    state_graph.save(filename)