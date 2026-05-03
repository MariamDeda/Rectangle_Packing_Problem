import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np
import time
import random
import math
import json
from collections import Counter

# ══════════════════════════════════════════════════════════════════════════════
# RANDOM BLOCK GENERATION  (15 blocks, seeded for reproducibility)
# ══════════════════════════════════════════════════════════════════════════════
random.seed(2)

def generate_blocks(n=250, max_dim=14, max_val=10):
    """
    Generate n random blocks: (dx, dy, dz, value, id).
    Dimensions are 1–max_dim on each axis; value is 1–max_val.
    """
    blks = []
    for i in range(1, n + 1):
        dx  = random.randint(1, max_dim)
        dy  = random.randint(1, max_dim)
        dz  = random.randint(1, max_dim)
        val = random.randint(1, max_val)
        blks.append((dx, dy, dz, val, i))
    return blks

BLOCKS = generate_blocks(15)

print("Generated 15 random blocks:")
print(f"  {'ID':>3}  {'dx':>3} {'dy':>3} {'dz':>3}  {'val':>4}  {'density':>8}")
print("  " + "-"*38)
for dx, dy, dz, val, bid in BLOCKS:
    print(f"  {bid:>3}  {dx:>3} {dy:>3} {dz:>3}  {val:>4}  {val/(dx*dy*dz):>8.3f}")

# ── Colour palette (16 colours; index 0 unused) ────────────────────────────────
COLOURS = [
    None,
    "#E63946","#2A9D8F","#E9C46A","#457B9D","#F4A261",
    "#A8DADC","#8338EC","#06D6A0","#FF6B6B","#4ECDC4",
    "#FFE66D","#A8E6CF","#FF8B94","#B4A7D6","#83D0C9",
]

# ── Analytics accumulator ─────────────────────────────────────────────────────
ALL_RESULTS = {}   # key: (gx,gy,gz) -> {algo: {value, steps, time_s, ...}}
ANALYTICS_FILE = "grid_sweep_analytics.json"

# ══════════════════════════════════════════════════════════════════════════════
# VISUALISATION HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _hex_to_rgba(hex_colour, alpha=0.75):
    h = hex_colour.lstrip("#")
    r, g, b = (int(h[i:i+2], 16) / 255.0 for i in (0, 2, 4))
    return (r, g, b, alpha)

def _cube_faces(ox, oy, oz, dx, dy, dz):
    x0, x1 = ox, ox+dx;  y0, y1 = oy, oy+dy;  z0, z1 = oz, oz+dz
    return [
        [(x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0)],
        [(x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)],
        [(x0,y0,z0),(x1,y0,z0),(x1,y0,z1),(x0,y0,z1)],
        [(x0,y1,z0),(x1,y1,z0),(x1,y1,z1),(x0,y1,z1)],
        [(x0,y0,z0),(x0,y1,z0),(x0,y1,z1),(x0,y0,z1)],
        [(x1,y0,z0),(x1,y1,z0),(x1,y1,z1),(x1,y0,z1)],
    ]

def draw(grid, GX, GY, GZ, ax, title="", stats=None):
    ax.clear()
    ax.set_facecolor("#0D1117")
    try:
        for pane in (ax.xaxis.pane, ax.yaxis.pane, ax.zaxis.pane):
            pane.fill = False
            pane.set_edgecolor("#30363D")
    except AttributeError:
        pass
    ax.grid(False)
    ax.set_xlim(0, GX); ax.set_ylim(0, GY); ax.set_zlim(0, GZ)
    ax.set_xlabel("X", color="#8B949E")
    ax.set_ylabel("Y", color="#8B949E")
    ax.set_zlabel("Z", color="#8B949E")
    ax.tick_params(colors="#8B949E")
    ax.set_title(title, color="#E6EDF3", pad=8, fontsize=9, fontfamily="monospace")

    if stats:
        hud = (f"steps  : {stats.get('steps',0):,}\n"
               f"time   : {stats.get('elapsed',0):.3f}s\n"
               f"best   : {stats.get('best',0)}")
        if "pruned" in stats:
            hud += f"\npruned : {stats['pruned']:,}"
        ax.text2D(0.02, 0.97, hud, transform=ax.transAxes,
                  color="#58A6FF", fontsize=7, fontfamily="monospace",
                  verticalalignment="top",
                  bbox=dict(boxstyle="round,pad=0.3", facecolor="#161B22",
                            edgecolor="#30363D", alpha=0.85))

    for x in range(GX+1):
        ax.plot([x,x],[0,GY],[0,0], color="#21262D", lw=0.4)
        ax.plot([x,x],[0,0],[0,GZ], color="#21262D", lw=0.4)
    for y in range(GY+1):
        ax.plot([0,GX],[y,y],[0,0], color="#21262D", lw=0.4)
        ax.plot([0,0],[y,y],[0,GZ], color="#21262D", lw=0.4)
    for z in range(GZ+1):
        ax.plot([0,GX],[0,0],[z,z], color="#21262D", lw=0.4)
        ax.plot([0,0],[0,GY],[z,z], color="#21262D", lw=0.4)

    placed = {}
    for x in range(GX):
        for y in range(GY):
            for z in range(GZ):
                bid = grid[x][y][z]
                if bid:
                    if bid not in placed:
                        placed[bid] = [x,y,z,x+1,y+1,z+1]
                    else:
                        b = placed[bid]
                        b[0]=min(b[0],x); b[1]=min(b[1],y); b[2]=min(b[2],z)
                        b[3]=max(b[3],x+1); b[4]=max(b[4],y+1); b[5]=max(b[5],z+1)

    for bid,(x0,y0,z0,x1,y1,z1) in placed.items():
        col = COLOURS[bid] if bid < len(COLOURS) else "#FFFFFF"
        poly = Poly3DCollection(_cube_faces(x0,y0,z0,x1-x0,y1-y0,z1-z0),
                                facecolor=_hex_to_rgba(col,0.72),
                                edgecolor=_hex_to_rgba(col,1.00), linewidth=0.5)
        ax.add_collection3d(poly)
    plt.pause(0.001)

# ══════════════════════════════════════════════════════════════════════════════
# GRID HELPERS  (grid size passed explicitly — no globals)
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

def count_free(grid, GX, GY, GZ):
    return sum(1 for x in range(GX) for y in range(GY)
               for z in range(GZ) if grid[x][y][z] == 0)

def get_block_by_id(bid, blocks):
    for b in blocks:
        if b[4] == bid:
            return b
    return None

# ══════════════════════════════════════════════════════════════════════════════
# ALGORITHM 1 — GREEDY
# ══════════════════════════════════════════════════════════════════════════════

def run_greedy(blocks, GX, GY, GZ, ax):
    grid   = make_grid(GX, GY, GZ)
    total, steps = 0, 0
    t0     = time.perf_counter()
    sorted_blocks = sorted(blocks, key=lambda b: b[3]/(b[0]*b[1]*b[2]), reverse=True)

    for dx, dy, dz, val, bid in sorted_blocks:
        placed = False
        for ox in range(GX):
            if placed: break
            for oy in range(GY):
                if placed: break
                for oz in range(GZ):
                    steps += 1
                    if can_place(grid, ox, oy, oz, dx, dy, dz, GX, GY, GZ):
                        place(grid, ox, oy, oz, dx, dy, dz, bid)
                        total += val
                        if ax:
                            elapsed = time.perf_counter() - t0
                            draw(grid, GX, GY, GZ, ax,
                                 f"[Greedy] block {bid} → {total}",
                                 dict(steps=steps, elapsed=elapsed, best=total))
                        placed = True
                        break

    elapsed = time.perf_counter() - t0
    result  = dict(value=total, steps=steps, time_s=round(elapsed,6))
    if ax:
        draw(grid, GX, GY, GZ, ax, f"[Greedy] ✦ FINAL={total}",
             dict(steps=steps, elapsed=elapsed, best=total))
        plt.pause(0.6)
    return grid, result

# ══════════════════════════════════════════════════════════════════════════════
# ALGORITHM 2 — DP  (volume-relaxed 0/1 knapsack)
# ══════════════════════════════════════════════════════════════════════════════

def run_dp(blocks, GX, GY, GZ, ax):
    grid     = make_grid(GX, GY, GZ)
    capacity = GX * GY * GZ
    steps, t0 = 0, time.perf_counter()

    dp     = [0] * (capacity + 1)
    chosen = [[] for _ in range(capacity + 1)]

    for dx, dy, dz, val, bid in blocks:
        vol = dx * dy * dz
        for v in range(capacity, vol-1, -1):
            steps += 1
            if dp[v-vol] + val > dp[v]:
                dp[v]     = dp[v-vol] + val
                chosen[v] = chosen[v-vol] + [(dx,dy,dz,val,bid)]

    best_v   = max(range(capacity+1), key=lambda v: dp[v])
    selected = chosen[best_v]
    dp_bound = dp[best_v]

    total = 0
    for dx, dy, dz, val, bid in sorted(selected, key=lambda b: b[0]*b[1]*b[2], reverse=True):
        placed = False
        for ox in range(GX):
            if placed: break
            for oy in range(GY):
                if placed: break
                for oz in range(GZ):
                    steps += 1
                    if can_place(grid, ox, oy, oz, dx, dy, dz, GX, GY, GZ):
                        place(grid, ox, oy, oz, dx, dy, dz, bid)
                        total += val
                        if ax:
                            elapsed = time.perf_counter() - t0
                            draw(grid, GX, GY, GZ, ax,
                                 f"[DP] block {bid} → {total} (bound={dp_bound})",
                                 dict(steps=steps, elapsed=elapsed, best=total))
                        placed = True
                        break

    elapsed = time.perf_counter() - t0
    result  = dict(value=total, steps=steps, time_s=round(elapsed,6),
                   dp_upper_bound=dp_bound)
    if ax:
        draw(grid, GX, GY, GZ, ax,
             f"[DP] ✦ FINAL={total} (bound={dp_bound})",
             dict(steps=steps, elapsed=elapsed, best=total))
        plt.pause(0.6)
    return grid, result

# ══════════════════════════════════════════════════════════════════════════════
# ALGORITHM 3 — SIMULATED ANNEALING
# ══════════════════════════════════════════════════════════════════════════════

def run_simulated_annealing(blocks, GX, GY, GZ, ax):
    t0 = time.perf_counter()

    # Start from a greedy solution
    cur_grid, gr = run_greedy(blocks, GX, GY, GZ, None)
    cur_val  = gr["value"]
    best_val = cur_val
    best_g   = copy_grid(cur_grid, GX, GY, GZ)

    temp, final_temp, cooling = 500.0, 0.5, 0.92
    iters_per_temp = 150
    steps = gr["steps"]
    iteration = 0

    def neighbour(grid, val):
        ng = copy_grid(grid, GX, GY, GZ)
        nv = val
        placed_ids = {ng[x][y][z]
                      for x in range(GX) for y in range(GY)
                      for z in range(GZ) if ng[x][y][z]}
        avail = [b for b in blocks if b[4] not in placed_ids]
        choices = (['remove','move','add'] if avail else ['remove','move'])
        action  = random.choice(choices)

        if action == 'add' and avail:
            dx,dy,dz,v,bid = random.choice(avail)
            positions = [(ox,oy,oz) for ox in range(GX)
                         for oy in range(GY) for oz in range(GZ)]
            random.shuffle(positions)
            for ox,oy,oz in positions:
                if can_place(ng, ox,oy,oz, dx,dy,dz, GX,GY,GZ):
                    place(ng, ox,oy,oz, dx,dy,dz, bid)
                    nv += v; break

        elif action == 'remove' and placed_ids:
            bid = random.choice(list(placed_ids))
            b   = get_block_by_id(bid, blocks)
            if b:
                dx,dy,dz,v,_ = b
                found = False
                for x in range(GX):
                    if found: break
                    for y in range(GY):
                        if found: break
                        for z in range(GZ):
                            if ng[x][y][z] == bid:
                                remove_block(ng,x,y,z,dx,dy,dz)
                                nv -= v
                                found = True
                                break

        elif action == 'move' and placed_ids:
            bid = random.choice(list(placed_ids))
            b   = get_block_by_id(bid, blocks)
            if b:
                dx,dy,dz,v,_ = b
                pos = None
                for x in range(GX):
                    for y in range(GY):
                        for z in range(GZ):
                            if ng[x][y][z] == bid:
                                pos = (x,y,z)
                                remove_block(ng,x,y,z,dx,dy,dz)
                                nv -= v; break
                    if pos: break
                if pos:
                    positions = [(ox,oy,oz) for ox in range(GX)
                                 for oy in range(GY) for oz in range(GZ)]
                    random.shuffle(positions)
                    ok = False
                    for ox,oy,oz in positions:
                        if can_place(ng,ox,oy,oz,dx,dy,dz,GX,GY,GZ):
                            place(ng,ox,oy,oz,dx,dy,dz,bid)
                            nv += v; ok = True; break
                    if not ok:
                        ox,oy,oz = pos
                        if can_place(ng,ox,oy,oz,dx,dy,dz,GX,GY,GZ):
                            place(ng,ox,oy,oz,dx,dy,dz,bid); nv += v
        return ng, nv

    while temp > final_temp:
        for _ in range(iters_per_temp):
            steps += 1
            ng, nv = neighbour(cur_grid, cur_val)
            delta  = nv - cur_val
            if delta > 0 or random.random() < math.exp(delta / temp):
                cur_grid, cur_val = ng, nv
                if cur_val > best_val:
                    best_val = cur_val
                    best_g   = copy_grid(cur_grid, GX, GY, GZ)
        iteration += 1
        temp *= cooling
        if ax and iteration % 5 == 0:
            elapsed = time.perf_counter() - t0
            draw(cur_grid, GX, GY, GZ, ax,
                 f"[SA] temp={temp:.1f} cur={cur_val} best={best_val}",
                 dict(steps=steps, elapsed=elapsed, best=best_val))

    elapsed = time.perf_counter() - t0
    result  = dict(value=best_val, steps=steps, time_s=round(elapsed,6),
                   iterations=iteration)
    if ax:
        draw(best_g, GX, GY, GZ, ax,
             f"[SA] ✦ FINAL={best_val}",
             dict(steps=steps, elapsed=elapsed, best=best_val))
        plt.pause(0.6)
    return best_g, result

# ══════════════════════════════════════════════════════════════════════════════
# ANALYTICS — save & print
# ══════════════════════════════════════════════════════════════════════════════

def save_analytics():
    serialisable = {str(k): v for k, v in ALL_RESULTS.items()}
    with open(ANALYTICS_FILE, "w") as f:
        json.dump(serialisable, f, indent=2)
    print(f"  [Analytics] Saved → {ANALYTICS_FILE}")

def print_grid_summary(GX, GY, GZ):
    key = f"{GX}x{GY}x{GZ}"
    data = ALL_RESULTS.get((GX,GY,GZ), {})
    algos = ["Greedy", "DP", "Simulated_Annealing"]
    print(f"\n  {'Algorithm':<22} {'Value':>6}  {'Steps':>10}  {'Time(s)':>10}  Extra")
    print(f"  {'-'*22} {'-'*6}  {'-'*10}  {'-'*10}  {'-'*20}")
    for a in algos:
        if a not in data: continue
        d = data[a]
        extra = ""
        if "branches_pruned" in d: extra = f"pruned={d['branches_pruned']:,}"
        if "dp_upper_bound"  in d: extra = f"bound={d['dp_upper_bound']}"
        if "iterations"      in d: extra = f"iters={d['iterations']}"
        print(f"  {a.replace('_',' '):<22} {d['value']:>6}  {d['steps']:>10,}  {d['time_s']:>10.6f}  {extra}")

# ══════════════════════════════════════════════════════════════════════════════
# COMPARISON CHART  — shown once per grid size
# ══════════════════════════════════════════════════════════════════════════════

def show_comparison_chart(GX, GY, GZ):
    data    = ALL_RESULTS.get((GX,GY,GZ), {})
    algos   = [a for a in ["Greedy","DP","Simulated_Annealing"] if a in data]
    labels  = [a.replace("_"," ") for a in algos]
    values  = [data[a]["value"]  for a in algos]
    steps   = [data[a]["steps"]  for a in algos]
    times   = [data[a]["time_s"] for a in algos]
    cols    = ["#2A9D8F","#E9C46A","#F4A261"]

    fig2, axes = plt.subplots(1, 3, figsize=(14, 4))
    fig2.patch.set_facecolor("#0D1117")
    fig2.suptitle(f"Grid {GX}×{GY}×{GZ} — Algorithm Comparison",
                  color="#E6EDF3", fontsize=12, fontfamily="monospace")

    for ax2, data_arr, ylabel in [
        (axes[0], values, "Value"),
        (axes[1], steps,  "Steps"),
        (axes[2], times,  "Time (s)"),
    ]:
        ax2.set_facecolor("#161B22")
        bars = ax2.bar(labels, data_arr, color=cols[:len(algos)],
                       edgecolor="#30363D", width=0.5)
        ax2.set_title(ylabel, color="#E6EDF3", fontsize=9, fontfamily="monospace")
        ax2.tick_params(colors="#E6EDF3", labelsize=7)
        ax2.tick_params(axis="x", rotation=15)
        for spine in ax2.spines.values(): spine.set_edgecolor("#30363D")
        for bar, v in zip(bars, data_arr):
            lbl = f"{v:.5f}" if isinstance(v, float) else f"{v:,}"
            ax2.text(bar.get_x()+bar.get_width()/2, bar.get_height()*1.02,
                     lbl, ha="center", va="bottom",
                     color="#E6EDF3", fontsize=6.5, fontfamily="monospace")

    plt.tight_layout()
    fname = f"analytics_chart_{GX}x{GY}x{GZ}.png"
    plt.savefig(fname, dpi=130, bbox_inches="tight", facecolor="#0D1117")
    print(f"  [Analytics] Chart saved → {fname}")
    plt.show(block=False)
    plt.pause(1.5)
    plt.close(fig2)

# ══════════════════════════════════════════════════════════════════════════════
# CROSS-GRID SUMMARY CHART  — shown at the very end
# ══════════════════════════════════════════════════════════════════════════════

def show_cross_grid_chart():
    grid_keys = sorted(ALL_RESULTS.keys())
    labels    = [f"{g[0]}×{g[1]}×{g[2]}" for g in grid_keys]
    algos     = ["Greedy","DP","Simulated_Annealing"]
    algo_cols = {"Greedy":"#2A9D8F","DP":"#E9C46A",
                 "Simulated_Annealing":"#F4A261"}

    fig3, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig3.patch.set_facecolor("#0D1117")
    fig3.suptitle("Grid Sweep — Value & Time Across All Grid Sizes",
                  color="#E6EDF3", fontsize=12, fontfamily="monospace")

    x = np.arange(len(grid_keys))
    w = 0.18

    for i, algo in enumerate(algos):
        vals  = [ALL_RESULTS[g].get(algo, {}).get("value", 0)   for g in grid_keys]
        times = [ALL_RESULTS[g].get(algo, {}).get("time_s", 0)  for g in grid_keys]
        offset = (i - 1.5) * w
        lbl    = algo.replace("_"," ")

        for ax2, arr, ylabel in [(axes[0], vals, "Value"), (axes[1], times, "Time (s)")]:
            ax2.bar(x + offset, arr, w, label=lbl,
                    color=algo_cols[algo], edgecolor="#30363D", alpha=0.85)

    for ax2, ylabel in [(axes[0],"Value Achieved"),(axes[1],"Time (seconds)")]:
        ax2.set_facecolor("#161B22")
        ax2.set_xticks(x); ax2.set_xticklabels(labels, color="#E6EDF3", fontsize=9)
        ax2.set_ylabel(ylabel, color="#E6EDF3")
        ax2.tick_params(colors="#E6EDF3")
        ax2.legend(fontsize=8, facecolor="#161B22", labelcolor="#E6EDF3")
        for spine in ax2.spines.values(): spine.set_edgecolor("#30363D")

    plt.tight_layout()
    plt.savefig("analytics_cross_grid.png", dpi=130, bbox_inches="tight",
                facecolor="#0D1117")
    print("\n  [Analytics] Cross-grid chart saved → analytics_cross_grid.png")
    plt.show(block=False)
    plt.pause(2)

# ══════════════════════════════════════════════════════════════════════════════
# MAIN GRID SWEEP  — 2×2×2 → 4×4×4, step +1 on each axis simultaneously
# ══════════════════════════════════════════════════════════════════════════════

GRID_SIZES = [(s, s, s) for s in range(2, 21)]   # (2,2,2) (3,3,3) (4,4,4)

plt.ion()

for GX, GY, GZ in GRID_SIZES:
    print("\n" + "="*65)
    print(f"  GRID  {GX} × {GY} × {GZ}   (capacity = {GX*GY*GZ} cells)")
    print("="*65)

    ALL_RESULTS[(GX, GY, GZ)] = {}

    # Only blocks that can physically fit in this grid
    fitting = [(dx,dy,dz,val,bid) for dx,dy,dz,val,bid in BLOCKS
               if dx<=GX and dy<=GY and dz<=GZ]
    print(f"  Blocks that fit: {len(fitting)} / {len(BLOCKS)}")

    # ── Shared figure: 1×3 subplot layout ────────────────────────────────────
    fig, axes = plt.subplots(1, 3, figsize=(18, 6),
                             subplot_kw={"projection": "3d"})
    fig.patch.set_facecolor("#0D1117")
    fig.suptitle(f"Grid {GX}×{GY}×{GZ}  —  3D Bin Packing",
                 color="#E6EDF3", fontsize=13, fontfamily="monospace")
    ax_g, ax_dp, ax_sa = axes[0], axes[1], axes[2]

    # Label each subplot
    for ax_, lbl in [(ax_g,"Greedy"),(ax_dp,"DP"),
                     (ax_sa,"Simulated Annealing")]:
        ax_.set_title(lbl, color="#8B949E", fontsize=9, fontfamily="monospace")

    plt.pause(0.1)

    # ── GREEDY ────────────────────────────────────────────────────────────────
    print(f"\n  [Greedy]  grid={GX}×{GY}×{GZ}")
    _, res = run_greedy(fitting, GX, GY, GZ, ax_g)
    ALL_RESULTS[(GX,GY,GZ)]["Greedy"] = res
    print(f"           value={res['value']}  steps={res['steps']:,}  time={res['time_s']:.4f}s")

    # ── DP ────────────────────────────────────────────────────────────────────
    print(f"\n  [DP]      grid={GX}×{GY}×{GZ}")
    _, res = run_dp(fitting, GX, GY, GZ, ax_dp)
    ALL_RESULTS[(GX,GY,GZ)]["DP"] = res
    print(f"           value={res['value']}  steps={res['steps']:,}  time={res['time_s']:.4f}s  bound={res['dp_upper_bound']}")

    # ── SIMULATED ANNEALING ───────────────────────────────────────────────────
    print(f"\n  [SA]      grid={GX}×{GY}×{GZ}")
    _, res = run_simulated_annealing(fitting, GX, GY, GZ, ax_sa)
    ALL_RESULTS[(GX,GY,GZ)]["Simulated_Annealing"] = res
    print(f"           value={res['value']}  steps={res['steps']:,}  time={res['time_s']:.4f}s")

    # ── Per-grid summary ──────────────────────────────────────────────────────
    print_grid_summary(GX, GY, GZ)

    # Save analytics after every grid size
    save_analytics()

    # Per-grid bar chart
    show_comparison_chart(GX, GY, GZ)

    plt.tight_layout()
    plt.pause(1.5)
    plt.close(fig)

# ══════════════════════════════════════════════════════════════════════════════
# FINAL CROSS-GRID SUMMARY
# ══════════════════════════════════════════════════════════════════════════════

print("\n" + "="*65)
print("  FINAL CROSS-GRID SUMMARY")
print("="*65)
for GX, GY, GZ in GRID_SIZES:
    print(f"\n  Grid {GX}×{GY}×{GZ}:")
    print_grid_summary(GX, GY, GZ)

show_cross_grid_chart()

plt.ioff()
plt.show()