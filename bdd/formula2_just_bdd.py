# bdd_part_b.py
#
# BDD (not reduced) for:
#   f(x1..x5) = 1 iff count of 1s >= 3
# Variable order: x1, x2, x3, x4, x5
#
# Prints nodes and edges, writes graphviz.dot

from dataclasses import dataclass
from typing import Dict, Optional, List


def formula(env: Dict[str, int]) -> int:
    ones = env["x1"] + env["x2"] + env["x3"] + env["x4"] + env["x5"]
    return 1 if ones >= 3 else 0


@dataclass
class Node:
    var: Optional[str]
    low: int
    high: int


class BDD:
    def __init__(self, var_order: List[str]):
        self.var_order = var_order
        self.nodes: List[Node] = [
            Node(None, 0, 0),  # terminal 0
            Node(None, 1, 1),  # terminal 1
        ]

    def new_node(self, var: str, low: int, high: int) -> int:
        nid = len(self.nodes)
        self.nodes.append(Node(var, low, high))
        return nid

    def build(self, idx: int, env_partial: Dict[str, int]) -> int:
        if idx == len(self.var_order):
            return 1 if formula(env_partial) == 1 else 0

        v = self.var_order[idx]

        env0 = dict(env_partial)
        env0[v] = 0
        low_id = self.build(idx + 1, env0)

        env1 = dict(env_partial)
        env1[v] = 1
        high_id = self.build(idx + 1, env1)

        return self.new_node(v, low_id, high_id)

    def print_nodes_edges(self, root: int) -> None:
        print("BDD (not reduced)")
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
        lines.append("digraph BDD {")
        lines.append("  rankdir=TB;")
        lines.append('  0 [shape=box,label="0"];')
        lines.append('  1 [shape=box,label="1"];')

        for nid in range(2, len(self.nodes)):
            lines.append(f'  {nid} [label="{self.nodes[nid].var}"];')

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
    order = ["x1", "x2", "x3", "x4", "x5"]
    bdd = BDD(order)
    root_id = bdd.build(0, {})
    bdd.print_nodes_edges(root_id)
    bdd.write_dot(root_id, "graphviz.dot")
