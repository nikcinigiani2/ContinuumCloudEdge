

import numpy as np
from centralizedAllocation import centralized_allocation, allocate_lambda    # import di allocate_lambda
from iterativeAllocation import matchingAlg

def centralized_allocate(app_cost, totAppl, capacity_per_edge,
                         service_rate_edge, num_edge, mu_appl):
    """
    Wrapper su centralized_allocation:
      - converte app_cost in np.array
      - se mu_appl>0 usa Hungarian+min-cost-flow
      - se mu_appl==0 chiama solo allocate_lambda
    """
    app_cost_arr = np.array(app_cost, dtype=int)

    if mu_appl > 0:
        total_cost, alloc_bin, parts, mu_cost, lambda_cost = centralized_allocation(
            app_cost_arr, totAppl, capacity_per_edge, num_edge, mu_appl
        )
    else:
        # Solo λ-app: bypass allocate_mu
        lambda_bin, lambda_parts, lambda_cost = allocate_lambda(
            app_cost_arr, totAppl, capacity_per_edge, num_edge, mu_appl
        )
        alloc_bin   = lambda_bin
        parts       = lambda_parts
        total_cost  = lambda_cost

    return total_cost, alloc_bin, parts

def greedy_allocate(app_cost, totAppl, capacity_per_edge,
                    service_rate_edge, num_edge, mu_appl):
    """
    Wrapper su matchingAlg:
      - converte app_cost in np.array per supportare l’indicizzazione
      - calcola allocazione greedy + costo
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

    parts_arr  = np.array(parts, dtype=int)
    total_cost = int(np.sum(parts_arr * app_cost_arr))

    return alloc, parts, total_cost
