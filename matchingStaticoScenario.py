from allocation import greedy_allocate

def run_matchingStatic(init_data, events, regime, ne):
    """
    Greedy statico: prima allocazione con matchingAlg, poi nuove app
    assegnate on-the-fly al nodo a costo minimo. Conteggia comunque eventuali
    rilocazioni (dovrebbero restare 0).
    Restituisce (mean_cost, total_reloc, total_effective_events, total_cycles).
    """
    # stato iniziale
    app_cost          = [r.tolist() for r in init_data['app_cost']]
    totAppl           = list(init_data['totAppl'])
    service_rate_edge = init_data['service_rate_edge']
    num_edge          = init_data['num_edge']
    mu_appl           = init_data['mu_appl']

    containers = 5 if regime == 'scarsità' else 10
    cap_edge   = [containers * r for r in service_rate_edge]

    # slot 0: allocazione iniziale greedy
    _, last_parts, cost0 = greedy_allocate(
        app_cost, totAppl, cap_edge.copy(),
        service_rate_edge, num_edge, mu_appl
    )
    # aggiorno capacità residua
    for row in last_parts:
        for j in range(num_edge):
            cap_edge[j] -= row[j]

    sum_cost         = cost0
    total_reloc      = 0
    effective_events = 0
    cycle_count      = 1

    # processa tutti gli eventi
    for typ, *args in events:
        # stampiamo ogni inizio cycle per il statico
        print(f"Cycle Static {cycle_count} - Event: {typ}")
        if typ in ('death','birth_lambda','birth_mu','migration'):
            effective_events += 1


        # Applica evento
        if typ == 'death':
            idx = args[0]
            # libero capacità
            for j in range(num_edge):
                cap_edge[j] += last_parts[idx][j]
            # rimuovo app
            del last_parts[idx]
            del app_cost[idx]
            del totAppl[idx]
            if idx < mu_appl:
                mu_appl -= 1

        elif typ in ('birth_lambda','birth_mu'):
            d = args[0]
            q     = int(d['totAppl'][-1])
            costs = d['app_cost'][-1].tolist()
            app_cost.append(costs)
            totAppl.append(q)
            if typ == 'birth_mu':
                mu_appl += 1
            # on-the-fly greedy
            cand = [j for j in range(num_edge) if cap_edge[j] >= q]
            j_min = min(cand, key=lambda j: costs[j]) if cand else num_edge
            if j_min < num_edge:
                cap_edge[j_min] -= q
            row = [0]*(num_edge+1)
            row[j_min] = q
            last_parts.append(row)

        elif typ == 'migration':
            idx, new_type, d = args
            # rimuovo old
            for j in range(num_edge):
                cap_edge[j] += last_parts[idx][j]
            del last_parts[idx]
            del app_cost[idx]
            del totAppl[idx]
            if idx < mu_appl:
                mu_appl -= 1
            # nuova app
            q     = int(d['totAppl'][-1])
            costs = d['app_cost'][-1].tolist()
            app_cost.append(costs)
            totAppl.append(q)
            if new_type == 'mu':
                mu_appl += 1
            cand = [j for j in range(num_edge) if cap_edge[j] >= q]
            j_min = min(cand, key=lambda j: costs[j]) if cand else num_edge
            if j_min < num_edge:
                cap_edge[j_min] -= q
            row = [0]*(num_edge+1)
            row[j_min] = q
            last_parts.append(row)



        # costo slot (dopo evento)
        slot_cost = sum(
            last_parts[i][j] * app_cost[i][j]
            for i in range(len(last_parts))
            for j in range(len(last_parts[i]))
        )
        sum_cost += slot_cost

    mean_cost = sum_cost / 30000
    return mean_cost, 0, effective_events, cycle_count