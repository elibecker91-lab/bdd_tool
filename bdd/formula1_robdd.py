# robdd_build.py
#
# Constructs an ROBDD for:
#   (a ∧ ¬c) ∨ (b ⊕ d)
# Variable order:
#   a, c, b, d
#
# Minimization rules implemented:
# 1) If low == high, do not create the node, just return the child.
# 2) If a node with same (var, low, high) already exists, reuse it (merge).
#
# Outputs:
# - prints nodes and edges
# - writes graphviz.dot

from dataclasses import dataclass
from typing import Dict, Optional, List, Tuple


# Hardcoded formula: (a ∧ ¬c) ∨ (b ⊕ d)
def formula(env: Dict[str, int]) -> int:
    a = env["a"]
    b = env["b"]
    c = env["c"]
    d = env["d"]

    left = a & (1 - c)   # a AND (NOT c)
    right = b ^ d        # b XOR d
    return 1 if (left | right) else 0


@dataclass
class Node:
    # var is None for terminals
    var: Optional[str]
    low: int   # child when var=0
    high: int  # child when var=1


class ROBDD:
    def __init__(self, var_order: List[str]):
        self.var_order = var_order

        # Node IDs:
        # 0 = terminal 0
        # 1 = terminal 1
        self.nodes: List[Node] = [
            Node(None, 0, 0),  # id 0
            Node(None, 1, 1),  # id 1
        ]

        # Rule (2): unique table for merging identical nodes
        # key = (var, low, high) -> node_id
        self.unique_table: Dict[Tuple[str, int, int], int] = {}

        # Memoization so we don't rebuild the same subproblem
        # key = (idx, frozen_partial_assignment) -> node_id
        self.memo: Dict[Tuple[int, Tuple[Tuple[str, int], ...]], int] = {}

    def mk(self, var: str, low: int, high: int) -> int:
        """
        Create or reuse a node (var, low, high), applying both ROBDD rules.

        Rule (1): if low == high, the test is pointless -> return the child.
        Rule (2): if (var, low, high) already exists -> reuse it.
        """
        if low == high:
            return low  # Rule (1)

        key = (var, low, high)
        if key in self.unique_table:
            return self.unique_table[key]  # Rule (2)

        nid = len(self.nodes)
        self.nodes.append(Node(var, low, high))
        self.unique_table[key] = nid
        return nid

    def build(self, idx: int, env_partial: Dict[str, int]) -> int:
        """
        Shannon expansion in the given variable order:
        - If all variables assigned, evaluate the formula -> terminal 0/1.
        - Otherwise split on next variable v:
            low = build(v=0)
            high = build(v=1)
            return mk(v, low, high)  (which reduces/merges)
        """
        frozen_env = tuple(sorted(env_partial.items()))
        memo_key = (idx, frozen_env)
        if memo_key in self.memo:
            return self.memo[memo_key]

        # Done assigning all vars -> terminal
        if idx == len(self.var_order):
            val = formula(env_partial)
            out = 1 if val == 1 else 0
            self.memo[memo_key] = out
            return out

        v = self.var_order[idx]

        # v = 0 branch
        env0 = dict(env_partial)
        env0[v] = 0
        low_id = self.build(idx + 1, env0)

        # v = 1 branch
        env1 = dict(env_partial)
        env1[v] = 1
        high_id = self.build(idx + 1, env1)

        out = self.mk(v, low_id, high_id)
        self.memo[memo_key] = out
        return out

    def print_nodes_edges(self, root: int) -> None:
        print("ROBDD")
        print("Variable order:", self.var_order)
        print("Root id:", root)
        print()

        print("NODES:")
        print("  0: TERMINAL 0")
        print("  1: TERMINAL 1")
        for nid in range(2, len(self.nodes)):
            n = self.nodes[nid]
            print(f"  {nid}: var={n.var}, low={n.low}, high={n.high}")

        print()
        print("EDGES:")
        for nid in range(2, len(self.nodes)):
            n = self.nodes[nid]
            print(f"  {nid} --0--> {n.low}")
            print(f"  {nid} --1--> {n.high}")

    def write_dot(self, root: int, filename: str = "graphviz.dot") -> None:
        lines: List[str] = []
        lines.append("digraph ROBDD {")
        lines.append("  rankdir=TB;")
        lines.append('  0 [shape=box,label="0"];')
        lines.append('  1 [shape=box,label="1"];')

        for nid in range(2, len(self.nodes)):
            n = self.nodes[nid]
            lines.append(f'  {nid} [label="{n.var}"];')

        for nid in range(2, len(self.nodes)):
            n = self.nodes[nid]
            lines.append(f'  {nid} -> {n.low} [label="0",style=dashed];')
            lines.append(f'  {nid} -> {n.high} [label="1"];')

        lines.append('  root [shape=plaintext,label="root"];')
        lines.append(f"  root -> {root};")
        lines.append("}")

        with open(filename, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        print()
        print(f"Wrote {filename}")


if __name__ == "__main__":
    order = ["a", "c", "b", "d"]
    robdd = ROBDD(order)

    root_id = robdd.build(0, {})
    robdd.print_nodes_edges(root_id)
    robdd.write_dot(root_id, "graphviz.dot")
