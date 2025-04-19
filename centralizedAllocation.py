import networkx as nx
import numpy as np
from munkres import Munkres


def allocate_mu(app_cost, totAppl, num_edge, mu_appl):
    """
    Allocazione delle μ-app usando l'algoritmo di Hungarian (Munkres).
    Restituisce:
      - mu_allocation: matrice binaria (mu_appl x (num_edge+1))
      - mu_partitions: matrice quantitativa (mu_appl x (num_edge+1))
      - mu_cost: costo totale per le μ-app
    """
    # Considera solo le prime mu_appl richieste
    mu_totAppl = np.array(totAppl[:mu_appl], dtype=int)
    cost_matrix = np.array(app_cost[:mu_appl, :], dtype=int)

    # Replica la matrice per Hungarian
    replicated = np.hstack([cost_matrix] * mu_appl)
    m = Munkres()
    assignments = m.compute(replicated.tolist())

    mu_allocation = np.zeros((mu_appl, num_edge+1), dtype=int)
    mu_partitions = np.zeros((mu_appl, num_edge+1), dtype=int)
    mu_cost = 0

    for row, col in assignments:
        app_idx = row
        edge_idx = col % (num_edge+1)
        if app_idx < mu_appl:
            mu_allocation[app_idx, edge_idx] = 1
            mu_partitions[app_idx, edge_idx] = mu_totAppl[app_idx]
            mu_cost += mu_totAppl[app_idx] * cost_matrix[app_idx, edge_idx]

    return mu_allocation, mu_partitions, mu_cost


def allocate_lambda(app_cost, totAppl, capacity_per_edge, num_edge, mu_appl):
    """
    Allocazione delle λ-app mediante min cost flow.
    Restituisce:
      - lambda_cost: costo totale per le λ-app
      - lambda_binary: matrice binaria (l_app x (num_edge+1))
      - lambda_quantitative: matrice quantitativa (l_app x (num_edge+1))
    """
    lambda_app_cost = np.array(app_cost[mu_appl:], dtype=int)
    lambda_totAppl = np.array(totAppl[mu_appl:], dtype=int)
    l_app = lambda_totAppl.size

    G = nx.DiGraph()
    G.add_node('s', demand=-int(lambda_totAppl.sum()))
    G.add_node('t', demand= int(lambda_totAppl.sum()))

    # nodi applicazione
    app_nodes = []
    for i in range(l_app):
        for c in range(lambda_totAppl[i]):
            node = f"app_{i}_{c}"
            G.add_node(node, demand=0)
            G.add_edge('s', node, capacity=1, weight=0)
            app_nodes.append((i, node))

    # nodi edge
    for j in range(num_edge):
        edge_node = f"edge_{j}"
        G.add_node(edge_node, demand=0)
        G.add_edge(edge_node, 't', capacity=int(capacity_per_edge[j]), weight=0)
        for i, node in app_nodes:
            G.add_edge(node, edge_node, capacity=1, weight=int(lambda_app_cost[i, j]))

    # nodo cloud
    G.add_node('cloud', demand=0)
    G.add_edge('cloud', 't', capacity=10**9, weight=0)
    for i, node in app_nodes:
        G.add_edge(node, 'cloud', capacity=1, weight=int(lambda_app_cost[i, num_edge]))

    flowDict = nx.min_cost_flow(G)
    lambda_cost = sum(G[u][v]['weight'] * flowDict[u][v] for u, v in G.edges())

    lambda_binary = np.zeros((l_app, num_edge+1), dtype=int)
    lambda_quantitative = np.zeros((l_app, num_edge+1), dtype=int)
    for i in range(l_app):
        # edge
        for j in range(num_edge):
            flow = sum(flowDict.get(f"app_{i}_{c}", {}).get(f"edge_{j}", 0)
                       for c in range(lambda_totAppl[i]))
            if flow:
                lambda_binary[i, j] = 1
                lambda_quantitative[i, j] = flow
        # cloud
        flow_c = sum(flowDict.get(f"app_{i}_{c}", {}).get('cloud', 0)
                     for c in range(lambda_totAppl[i]))
        if flow_c:
            lambda_binary[i, num_edge] = 1
            lambda_quantitative[i, num_edge] = flow_c

    return lambda_binary, lambda_quantitative, lambda_cost


def centralized_allocation(app_cost, totAppl, capacity_per_edge, num_edge, mu_appl):
    """
    Combina l'allocazione di μ-app e λ-app:
      - mu_app su edge/cloud con Hungarian
      - lambda_app con min cost flow
    Restituisce:
      total_cost, allocation_binary, partitions, mu_cost, lambda_cost
    """
    mu_bin, mu_part, mu_cost = allocate_mu(app_cost, totAppl, num_edge, mu_appl)
    lambda_bin, lambda_part, lambda_cost = allocate_lambda(
        app_cost, totAppl, capacity_per_edge, num_edge, mu_appl
    )

    allocation_binary = np.vstack([mu_bin, lambda_bin])
    partitions = np.vstack([mu_part, lambda_part])
    total_cost = mu_cost + lambda_cost

    return total_cost, allocation_binary, partitions, mu_cost, lambda_cost
