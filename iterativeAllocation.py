import numpy as np


def matchingAlg(totAppl, capacity_per_edge, service_rate_edge, app_cost, edge, numAppl, mu_appl):
    allocations = np.zeros((numAppl, edge + 1), dtype=np.int64)
    partitions = np.zeros((numAppl, edge + 1), dtype=np.int64)

    while sum(totAppl) > 0:
        proposals = np.zeros((edge, numAppl), dtype=np.int64)

        for i in range(numAppl):
            if totAppl[i] == 0:
                continue

            # Nodo preferito
            cost_vector = np.array(app_cost[i][:])
            capacity_filter = np.array(capacity_per_edge)
            valid_nodes = (capacity_filter > 0).astype(int)

            if i >= mu_appl:
                # LAMBDA → vincolo sul service rate
                rate_filter = (np.array(service_rate_edge) <= totAppl[i]).astype(int)
                valid_nodes *= rate_filter

            valid_nodes = np.append(valid_nodes, 1)  # il cloud è sempre disponibile
            masked_cost = cost_vector * valid_nodes
            masked_cost[valid_nodes == 0] = 1e9  # escludi nodi non validi

            preferred = np.argmin(masked_cost)

            if preferred == edge:
                # Cloud: alloca direttamente
                allocations[i][edge] = 1
                partitions[i][edge] = totAppl[i]
                totAppl[i] = 0
            else:
                proposals[preferred][i] = 1

        for j in range(edge):
            candidates = np.where(proposals[j] == 1)[0]
            if len(candidates) == 0:
                continue

            costs = app_cost[candidates, j]
            best_idx = np.argmin(costs)
            best_app = candidates[best_idx]

            allocations[best_app][j] = 1

            if best_app < mu_appl:
                # MU → tutta o niente
                if capacity_per_edge[j] >= totAppl[best_app]:
                    partitions[best_app][j] = totAppl[best_app]
                    capacity_per_edge[j] -= totAppl[best_app]
                    totAppl[best_app] = 0
                else:
                    # Cloud fallback
                    allocations[best_app][edge] = 1
                    partitions[best_app][edge] = totAppl[best_app]
                    totAppl[best_app] = 0
            else:
                # LAMBDA → splittabile
                alloc = min(capacity_per_edge[j], totAppl[best_app])
                partitions[best_app][j] = alloc
                capacity_per_edge[j] -= alloc
                totAppl[best_app] -= alloc

                # se resta ancora da allocare, tornerà nel ciclo successivo

    return allocations.tolist(), partitions.tolist()