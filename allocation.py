
import numpy as np
from centralizedAllocation import centralized_allocation
from iterativeAllocation import matchingAlg

def centralized_allocate(app_cost, totAppl, capacity_per_edge,
                         service_rate_edge, num_edge, mu_appl):
    """
    Wrapper su centralized_allocation:
      - converte app_cost in np.array (per slicing a 2D)
      - usa Hungarian per μ-app e min-cost-flow per λ-app
      - restituisce total_cost, alloc_binary, partitions
    """
    # Assicuriamoci che app_cost sia un array NumPy 2D
    app_cost_arr = np.array(app_cost, dtype=int)

    total_cost, alloc_bin, parts, mu_cost, lambda_cost = centralized_allocation(
        app_cost_arr,           # ora un array, non una lista
        totAppl,
        capacity_per_edge,
        num_edge,
        mu_appl
    )
    return total_cost, alloc_bin, parts

def greedy_allocate(app_cost, totAppl, capacity_per_edge,
                    service_rate_edge, num_edge, mu_appl):
    """
    Wrapper su matchingAlg:
      - converte app_cost in np.array per supportare l’indicizzazione
      - destruttura solo (alloc, parts)
      - calcola poi il costo su partitions * app_cost
      - restituisce alloc_binary, partitions, total_cost
    """
    app_cost_arr = np.array(app_cost, dtype=int)

    alloc, parts = matchingAlg(
        list(totAppl),
        list(capacity_per_edge),
        list(service_rate_edge),
        app_cost_arr,
        num_edge,
        len(totAppl),
        mu_appl
    )

    parts_arr = np.array(parts, dtype=int)
    total_cost = int(np.sum(parts_arr * app_cost_arr))

    return alloc, parts, total_cost
