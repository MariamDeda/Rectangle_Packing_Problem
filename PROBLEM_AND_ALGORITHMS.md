# 3D Bin Packing Problem: Formal Analysis

## Table of Contents
1. [Problem Definition](#problem-definition)
2. [Formal Mathematical Formulation](#formal-mathematical-formulation)
3. [Algorithm Analysis](#algorithm-analysis)
4. [State Space Analysis](#state-space-analysis)
5. [Tree Structure Visualization](#tree-structure-visualization)

---

## Problem Definition

### Problem Statement
The **3D Bin Packing Problem** (3D-BP) is an optimization problem where we aim to maximize the total **value** of rectangular blocks that can be packed into a fixed 3D rectangular container (grid) without overlapping, subject to spatial constraints.

### Practical Context
Given:
- A 3D grid of dimensions $G_X \times G_Y \times G_Z$ (the container/bin)
- A set of $n$ rectangular blocks, each with:
  - Dimensions: $(d_x, d_y, d_z)$ in terms of grid cells
  - Value: $v_i$ (profit/importance)
  - Unique ID: $b_i$

**Objective**: Maximize the total value of blocks placed in the grid without any overlapping.

---

## Formal Mathematical Formulation

### Problem Definition
Let $B = \{b_1, b_2, \ldots, b_n\}$ be a set of blocks where each block $b_i$ is characterized by:
$$b_i = (d_{x,i}, d_{y,i}, d_{z,i}, v_i, \text{id}_i)$$

A **state** $S$ is a valid configuration of the grid where:
$$S: [0, G_X) \times [0, G_Y) \times [0, G_Z) \rightarrow B \cup \{\emptyset\}$$

Each cell $(x, y, z)$ is either occupied by a block ID or empty ($\emptyset$).

### Feasibility Constraint
A placement of block $b_i$ at position $(x_0, y_0, z_0)$ is **feasible** if:
$$\forall (x, y, z) \in [x_0, x_0+d_{x,i}) \times [y_0, y_0+d_{y,i}) \times [z_0, z_0+d_{z,i}):$$
$$S(x,y,z) = \emptyset$$

And boundary constraint:
$$x_0 + d_{x,i} \leq G_X \land y_0 + d_{y,i} \leq G_Y \land z_0 + d_{z,i} \leq G_Z$$

### Objective Function
For a state $S$ with placed blocks $P(S) \subseteq B$:
$$\text{Value}(S) = \sum_{b_i \in P(S)} v_i$$

### Optimization Problem
$$\boxed{\max_{S \in \mathcal{S}} \text{Value}(S)}$$

where $\mathcal{S}$ is the set of all feasible states.

### Problem Classification
- **NP-Hard**: The 3D bin packing problem is NP-hard in the strong sense
- **Related to**: 0/1 Knapsack (relaxed version), 3D Rectangle Packing
- **Computational Complexity**: No known polynomial-time algorithm for optimal solution
- **State Space Size**: $|\mathcal{S}| = O((G_X \times G_Y \times G_Z)^n)$ (exponential)

---

## Algorithm Analysis

### Algorithm 1: Greedy Algorithm

#### Description
The greedy algorithm makes locally optimal choices by prioritizing blocks with the **highest density** (value per unit volume).

#### Pseudocode
```
GREEDY(blocks, GX, GY, GZ):
    grid ← empty 3D array [GX][GY][GZ]
    total_value ← 0
    steps ← 0
    
    // Sort by density (value/volume) in descending order
    sorted_blocks ← SORT(blocks, by=value/(dx*dy*dz), desc)
    
    FOR EACH block b = (dx, dy, dz, value, id) IN sorted_blocks:
        placed ← FALSE
        
        FOR ox FROM 0 TO GX-1:
            IF placed THEN break
            FOR oy FROM 0 TO GY-1:
                IF placed THEN break
                FOR oz FROM 0 TO GZ-1:
                    steps ← steps + 1
                    IF can_place(grid, ox, oy, oz, dx, dy, dz) THEN:
                        place_block(grid, ox, oy, oz, dx, dy, dz, id)
                        total_value ← total_value + value
                        placed ← TRUE
                        break
    
    RETURN (grid, total_value, steps)
```

#### Mathematical Formulation
At iteration $i$, the greedy algorithm selects:
$$b_{greedy} = \arg\max_{b \in B_{remaining}} \frac{v_b}{d_{x,b} \cdot d_{y,b} \cdot d_{z,b}}$$

where $B_{remaining}$ is the set of unplaced blocks.

#### Characteristics
- **Time Complexity**: $O(n \cdot (G_X \cdot G_Y \cdot G_Z))$ where $n = |B|$
- **Space Complexity**: $O(G_X \cdot G_Y \cdot G_Z)$
- **Optimality**: No guarantee (approximation algorithm)
- **Approximation Ratio**: Can be arbitrarily bad in worst case
- **Advantages**:
  - Fast execution
  - Simple to implement and understand
  - Works well for many practical instances
  - Greedy choice heuristic is intuitive
- **Disadvantages**:
  - May miss optimal solutions due to fragmentation
  - No backtracking capability
  - Local optima trap: placing a large block early may prevent better packing later

---

### Algorithm 2: Dynamic Programming (DP)

#### Description
Treats the problem as a **volume-relaxed 0/1 knapsack** problem. Instead of considering exact 3D placements, DP solves which blocks to select based on total volume constraint, then performs spatial placement afterward.

#### Mathematical Formulation
Define $dp[v]$ as the maximum value achievable using exactly $v$ cells of volume.

**Recurrence Relation**:
$$dp[v] = \max \begin{cases} 
dp[v] & \text{(don't include block } b_i) \\
dp[v - \text{vol}_i] + val_i & \text{(include block } b_i)
\end{cases}$$

where $\text{vol}_i = d_{x,i} \cdot d_{y,i} \cdot d_{z,i}$

**Base Case**:
$$dp[0] = 0, \quad dp[v] = 0 \text{ for all } v > 0 \text{ initially}$$

**Optimal Selection**:
$$\text{Value}_{DP} = \max_{v \in [0, G_X \cdot G_Y \cdot G_Z]} dp[v]$$

#### Pseudocode
```
DP_KNAPSACK(blocks, GX, GY, GZ):
    capacity ← GX * GY * GZ
    dp ← array[0...capacity] initialized to 0
    chosen ← array[0...capacity] of empty lists
    
    FOR EACH block b = (dx, dy, dz, value, id) IN blocks:
        vol ← dx * dy * dz
        
        // Process in reverse to ensure 0/1 property
        FOR v FROM capacity DOWN TO vol:
            IF dp[v - vol] + value > dp[v] THEN:
                dp[v] ← dp[v - vol] + value
                chosen[v] ← chosen[v - vol] + [b]
    
    // Find best volume
    best_v ← argmax(dp[v]) for v in [0, capacity]
    selected_blocks ← chosen[best_v]
    
    // Place selected blocks spatially
    grid ← GREEDY_PLACEMENT(selected_blocks, GX, GY, GZ)
    
    RETURN (grid, dp[best_v], capacity - best_v)
```

#### Characteristics
- **Time Complexity**: $O(n \cdot C)$ where $C = G_X \cdot G_Y \cdot G_Z$ (pseudo-polynomial)
- **Space Complexity**: $O(C)$ for DP table
- **Optimality Guarantee**: Optimal solution for **volume-relaxed** problem (not spatial)
- **Upper Bound**: $dp[best\_v]$ is an **upper bound** for the true 3D packing
- **Advantages**:
  - Provides provable upper bound on solution quality
  - Better than greedy in many cases
  - Systematic exploration of block combinations
  - Polynomial in capacity (pseudo-polynomial)
- **Disadvantages**:
  - Assumes blocks can be "cut" or rearranged freely (volume relaxation)
  - Spatial placement after DP may not achieve DP's value
  - Memory intensive for large grids
  - Does not account for geometric constraints properly

#### Gap Analysis
$$\text{Gap} = \text{Value}_{DP} - \text{Value}_{actual}$$

The gap arises because DP ignores spatial geometry—it's possible to select blocks whose total volume fits but cannot be spatially packed.

---

### Algorithm 3: Simulated Annealing (SA)

#### Description
A **metaheuristic** optimization algorithm that uses controlled randomness and cooling schedule to escape local optima and explore the solution space probabilistically.

#### Theoretical Foundation
Simulated annealing mimics the physical process of annealing in metallurgy:
- **High Temperature**: Accept bad moves with high probability (explore)
- **Low Temperature**: Accept bad moves with low probability (exploit)

#### State Transition Probability
At temperature $T$, accept a neighbor state with value $v_{new}$ from current state with value $v_{cur}$:

$$P(\text{accept}) = \begin{cases}
1 & \text{if } v_{new} \geq v_{cur} \\
e^{\frac{v_{new} - v_{cur}}{T}} & \text{if } v_{new} < v_{cur}
\end{cases}$$

#### Pseudocode
```
SIMULATED_ANNEALING(blocks, GX, GY, GZ):
    current_grid ← GREEDY(blocks, GX, GY, GZ)
    current_value ← VALUE(current_grid)
    best_grid ← COPY(current_grid)
    best_value ← current_value
    
    T ← initial_temperature
    T_final ← final_temperature
    cooling_rate ← 0.92
    iterations_per_temp ← 150
    
    WHILE T > T_final:
        FOR i FROM 1 TO iterations_per_temp:
            neighbor_grid ← GENERATE_NEIGHBOR(current_grid, blocks)
            neighbor_value ← VALUE(neighbor_grid)
            
            delta ← neighbor_value - current_value
            
            IF delta > 0 THEN:
                current_grid ← neighbor_grid
                current_value ← neighbor_value
                
                IF neighbor_value > best_value THEN:
                    best_grid ← neighbor_grid
                    best_value ← neighbor_value
            ELSE IF RANDOM() < exp(delta / T) THEN:
                current_grid ← neighbor_grid
                current_value ← neighbor_value
        
        T ← T * cooling_rate
    
    RETURN (best_grid, best_value)
```

#### Neighbor Generation Strategies
Three types of moves generate neighbors:

1. **ADD**: Insert an unplaced block at random position
   - Selects an unplaced block
   - Tries random positions until feasible placement found
   - Increases value if successful

2. **REMOVE**: Delete a placed block
   - Selects random placed block
   - Removes it from grid
   - Decreases value

3. **MOVE**: Relocate a placed block
   - Removes placed block temporarily
   - Finds new random position
   - Reinserts if feasible

#### Mathematical Characteristics
- **Acceptance Criterion** (Metropolis):
$$\text{Accept} = \begin{cases}
\text{TRUE} & \text{if } \Delta E \leq 0 \\
\text{TRUE w.p. } e^{-\Delta E / T} & \text{if } \Delta E > 0
\end{cases}$$

- **Temperature Schedule** (Exponential Decay):
$$T_k = T_0 \cdot r^k, \quad r = 0.92$$

#### Characteristics
- **Time Complexity**: $O(\text{max\_iterations} \times \text{neighborhood\_check})$
- **Space Complexity**: $O(G_X \cdot G_Y \cdot G_Z)$
- **Convergence**: Probabilistic convergence to global optimum (given infinite time)
- **Optimality**: No guarantee, but often finds very good solutions
- **Advantages**:
  - Can escape local optima
  - Explores diverse regions of solution space
  - Balances exploration and exploitation
  - Adaptive to problem structure via cooling schedule
  - Empirically very effective
- **Disadvantages**:
  - Parameter tuning required (initial temp, cooling rate, iterations)
  - Slow convergence if cooling too fast
  - May not reach global optimum in practice
  - Stochastic: results vary between runs

#### Cooling Schedule Analysis
The exponential cooling schedule:
$$T_k = T_0 \cdot 0.92^k$$

- **Early iterations** ($k$ small): $T$ large → high acceptance probability → broad search
- **Late iterations** ($k$ large): $T$ small → low acceptance probability → local refinement
- **Critical ratio**: $\text{iterations\_per\_temp} = 150$ iterations at each temperature

---

## State Space Analysis

### State Space Definition
A **state** $S$ in the search space is a configuration of the 3D grid:
$$S = \{s_{xyz} : (x,y,z) \in [0,G_X) \times [0,G_Y) \times [0,G_Z), \, s_{xyz} \in B \cup \{\emptyset\}\}$$

The **state space** is:
$$\Omega = \{S : S \text{ is a feasible grid configuration}\}$$

### State Space Size
**Upper bound** on number of states:
$$(n+1)^{G_X \cdot G_Y \cdot G_Z}$$

where $n = |B|$ (each cell can be empty or contain one of $n$ block IDs).

**Example**: For a $3 \times 3 \times 3$ grid (27 cells) with 15 blocks:
$$|Omega| \leq 16^{27} \approx 10^{32} \text{ states}$$

This exponential growth demonstrates why finding optimal solutions is computationally hard.

### State Space Structure
**Key Observations**:

1. **DAG Structure**: The directed acyclic graph (DAG) of state transitions forms a tree-like structure where:
   - **Root**: Empty grid (all cells empty)
   - **Nodes**: Valid configurations
   - **Edges**: Transitions by adding/removing/moving blocks
   - **Leaves**: Terminal states (no more blocks can be added)

2. **Value Monotonicity**: Along any path from root to leaf:
   - Value is **non-decreasing** when adding blocks
   - Value can decrease when removing blocks (SA only)
   - Greedy explores primarily upward-trending paths

3. **Connectivity**: 
   - Multiple paths may lead to same state
   - Hashing identifies duplicate states (compression)
   - Graph has cycles due to move operations (SA)

---

## Tree Structure Visualization

### Expected Tree Hierarchy

```
                        ∅ (value=0)  ← ROOT (empty grid)
                        |
        ____________________________________________________________
       /              |                |              \
      b₁             b₂               b₃             b₄            ← LEVEL 1 (one block placed)
     / \             / \             / \             / \
   b₂  b₃          b₁  b₃          b₁  b₂          b₁  b₂          ← LEVEL 2 (two blocks placed)
   |    |          |    |          |    |          |    |
  ...  ...        ...  ...        ...  ...        ...  ...
   
   [Node size ∝ state value]
   [Color intensity ∝ state value]
   [Depth ∝ number of placement decisions]
```

### Tree Characteristics by Algorithm

#### Greedy Tree
```
Properties:
- Single path from root to leaf (deterministic)
- Strictly increasing value along path
- Depth = number of successfully placed blocks
- Width = 1 (no branching)
- Example depth for 3×3×3 grid: typically 5-8 blocks placed

Structure:
                 ∅ (0)
                  |
              b_dense1 (v₁)
                  |
              b_dense2 (v₁ + v₂)
                  |
                 ...
                  |
           FINAL (max_greedy_value)
```

**Interpretation**: Linear path shows greedy's deterministic nature—no exploration of alternatives.

#### DP Tree
```
Properties:
- Multiple branches from knapsack combinations
- Represents selected blocks → then spatial placement
- Width = number of subset combinations
- Depth = moderate (depends on selected subset size)
- Shows potential solutions before spatial placement

Structure:
                 ∅ (0)
              /  |  \
           subset_1 subset_2 subset_3
            |       |         |
          spatial  spatial   spatial
          place    place     place
          (value₁) (value₂)  (value₃)
```

**Interpretation**: Branching shows DP exploring different block combinations; different values show quality variance.

#### Simulated Annealing Tree
```
Properties:
- Highly branched tree with cycles possible
- Explores diverse regions of solution space
- Contains both value-increasing and value-decreasing transitions
- Width = large (explores many neighbors per state)
- Depth = moderate to deep (can accept bad moves)
- May revisit states (cycles)

Structure:
                 ∅ (0)
              /  |  \
          state1 state2 state3
           / |   / | \   |  \
         ... ... ... ...  ...
          (Many paths with both ↑ and ↓ value changes)
          
    Final node often in a different branch than greedy
```

**Interpretation**: Complex branching shows SA's ability to explore alternatives and escape local optima through controlled randomness.

### Visual Hierarchy in State Graph PNG

The generated PNG files visualize these structures as:

**Visual Elements**:
- **Node Position** (Y-axis): Depth level (root at top, leaves at bottom)
- **Node Position** (X-axis): Breadth at each level
- **Node Size**: Larger for higher-value states
- **Node Color**: Viridis/Plasma colormap from low (dark) to high (bright) values
- **Edge Direction**: Arrows show state transitions
- **Edge Style**: Curved to avoid overlaps
- **Colorbar**: Maps numerical values to colors for reference

**Example Interpretation of Tree Appearance**:
- **Greedy**: Narrow tree, single winding path with monotonic increase
- **DP**: More spread tree, multiple terminal values showing subset effectiveness
- **SA**: Bushy tree, many branches, multiple local regions explored, frequent value oscillations

---

## Comparative Analysis

| Aspect | Greedy | DP | Simulated Annealing |
|--------|--------|-----|---------------------|
| **Optimality** | No guarantee | Upper bound (volume) | Probabilistic global |
| **Time** | $O(n \cdot G^3)$ | $O(n \cdot C)$ | $O(I \cdot M)$ |
| **Memory** | $O(G^3)$ | $O(C)$ | $O(G^3)$ |
| **Deterministic** | Yes | Yes | No (stochastic) |
| **Solution Quality** | Fair | Better (relaxed) | Best (empirical) |
| **Convergence** | Fast | Fast | Slow |
| **Robustness** | Consistent | Consistent | Variable |
| **Parallelizable** | Difficult | Moderate | Easy (multi-run) |
| **Problem Size Limit** | Large | Medium | Medium |

---

## Conclusion

The 3D bin packing problem is a challenging NP-hard optimization problem solved here by three complementary algorithms:

1. **Greedy**: Fast and practical, provides baseline solution
2. **DP**: Theoretically grounded, provides upper bound
3. **SA**: Exploration-based, often finds best empirical solutions

The **state space tree** visualization reveals the exploration strategy of each algorithm, providing insight into their relative effectiveness and trade-offs between solution quality and computational efficiency.

The hierarchical tree structure naturally emerges from the sequential decision-making process, where each level represents the number of blocks placed, and branches represent different placement choices or sequences.
