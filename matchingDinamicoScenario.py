from allocation import greedy_allocate

def run_matchingDynamic(init_data, events, regime, ne):
    """
    Greedy dinamico: prima allocazione con matchingAlg, poi ricalcolo globale
    ogni ne eventi effettivi e tra ricalcoli nuove app allocate in modo greedy.
    Restituisce (mean_cost, total_reloc, total_effective_events, total_cycles).
    """
    app_cost          = [r.tolist() for r in init_data['app_cost']]
    totAppl           = list(init_data['totAppl'])
    service_rate_edge = init_data['service_rate_edge']
    num_edge          = init_data['num_edge']
    mu_appl           = init_data['mu_appl']

    containers = 5 if regime == 'scarsità' else 10
    full_cap   = [containers * r for r in service_rate_edge]

    sum_cost         = 0.0
    total_reloc      = 0
    effective_events = 0
    cycle_events     = 0
    cycle_count      = 0

    # slot 0: allocazione iniziale
    _, parts0, _ = greedy_allocate(
        app_cost, totAppl, full_cap.copy(),
        service_rate_edge, num_edge, mu_appl
    )
    last_parts = [row.copy() for row in parts0]
    # aggiorna capacità
    cap_edge = full_cap.copy()
    for row in last_parts:
        for j in range(num_edge):
            cap_edge[j] -= row[j]

    # costo slot 0
    sum_cost += sum(
        last_parts[i][j] * app_cost[i][j]
        for i in range(len(last_parts))
        for j in range(len(last_parts[i]))
    )
    cycle_count += 1

    # processa eventi
    for typ, *args in events:

        is_eff = typ in ('death','birth_lambda','birth_mu','migration')
        if is_eff:
            effective_events += 1
            cycle_events     += 1
            old_parts = [row.copy() for row in last_parts]

        # evento tra ricalcoli: greedy on-the-fly
        if typ == 'death':
            idx = args[0]
            for j in range(num_edge):
                cap_edge[j] += last_parts[idx][j]
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
            cand = [j for j in range(num_edge) if cap_edge[j] >= q]
            j_min = min(cand, key=lambda j: costs[j]) if cand else num_edge
            if j_min < num_edge:
                cap_edge[j_min] -= q
            row = [0]*(num_edge+1)
            row[j_min] = q
            last_parts.append(row)

        elif typ == 'migration':
            idx, new_type, d = args
            for j in range(num_edge):
                cap_edge[j] += last_parts[idx][j]
            del last_parts[idx]
            del app_cost[idx]
            del totAppl[idx]
            if idx < mu_appl:
                mu_appl -= 1
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

        # costo dopo evento
        sum_cost += sum(
            last_parts[i][j] * app_cost[i][j]
            for i in range(len(last_parts))
            for j in range(len(last_parts[i]))
        )

        # ricalcolo globale ogni ne eventi effettivi
        if cycle_events == ne:
            print(f"Ricalcolo Matching Dinamico al ciclo {cycle_count} con ne={ne}")

            _, parts_r, _ = greedy_allocate(
                app_cost, totAppl, full_cap.copy(),
                service_rate_edge, num_edge, mu_appl
            )
            new_parts = [row.copy() for row in parts_r]
            # aggiorna capacità
            cap_edge = full_cap.copy()
            for row in new_parts:
                for j in range(num_edge):
                    cap_edge[j] -= row[j]
            # conteggio rilocazioni
            reloc = sum(
                1 for i in range(len(new_parts))
                if new_parts[i] != last_parts[i]
            )
            total_reloc += reloc
            last_parts  = new_parts
            cycle_count += 1
            cycle_events = 0

    mean_cost = sum_cost / 30000
    return mean_cost, total_reloc, effective_events, cycle_count
