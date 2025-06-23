from allocation import centralized_allocate

def run_centralized(init_data, events, regime, ne):
    """
    Centralized: ricalcolo ogni ne eventi effettivi, nuove app sempre sul cloud.
    Restituisce (mean_cost, total_reloc, total_effective_events, total_cycles).
    """
    # Stato iniziale
    app_cost          = [r.tolist() for r in init_data['app_cost']]
    totAppl           = list(init_data['totAppl'])
    service_rate_edge = init_data['service_rate_edge']
    num_edge          = init_data['num_edge']
    mu_appl           = init_data['mu_appl']

    containers   = 5 if regime == 'scarsità' else 10
    full_cap     = [containers * r for r in service_rate_edge]

    sum_cost        = 0.0
    total_reloc     = 0
    effective_events= 0
    cycle_events    = 0
    cycle_count     = 0

    # --- slot 0: prima allocazione globale ---
    cost0, _, parts0 = centralized_allocate(
        app_cost, totAppl, full_cap.copy(),
        service_rate_edge, num_edge, mu_appl
    )
    last_parts = [row.tolist() for row in parts0]
    sum_cost   += cost0
    cycle_count += 1

    # --- elaborazione eventi ---
    for typ, *args in events:
        #stampiamo ogni inizio cycle per il centralized
        print(f"Cycle Centralized {cycle_count} - Event: {typ}")

        is_eff = typ in ('death','birth_lambda','birth_mu','migration')
        if is_eff:
            effective_events += 1
            cycle_events     += 1

        # 1) Applica evento
        if typ == 'death':
            idx = args[0]
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
            # nuova app sul cloud
            row = [0]*(num_edge+1)
            row[num_edge] = q
            last_parts.append(row)

        elif typ == 'migration':
            idx, new_type, d = args
            # rimuovo vecchia
            del last_parts[idx]
            del app_cost[idx]
            del totAppl[idx]
            if idx < mu_appl:
                mu_appl -= 1
            # nuova app sul cloud
            q     = int(d['totAppl'][-1])
            costs = d['app_cost'][-1].tolist()
            app_cost.append(costs)
            totAppl.append(q)
            if new_type == 'mu':
                mu_appl += 1
            row = [0]*(num_edge+1)
            row[num_edge] = q
            last_parts.append(row)

        # 2) Costo dopo evento
        slot_cost = sum(
            last_parts[i][j] * app_cost[i][j]
            for i in range(len(last_parts))
            for j in range(len(last_parts[i]))
        )
        sum_cost += slot_cost

        # 3) Ricalcolo globale ogni ne eventi effettivi
        if cycle_events == ne:
            cost_r, _, parts_r = centralized_allocate(
                app_cost, totAppl, full_cap.copy(),
                service_rate_edge, num_edge, mu_appl
            )
            # conteggio rilocazioni
            new_parts = [row.tolist() for row in parts_r]
            reloc = sum(
                1 for i in range(len(new_parts))
                if new_parts[i] != last_parts[i]
            )
            total_reloc += reloc
            last_parts   = new_parts
            sum_cost    += cost_r  # includi anche il costo del ricalcolo
            cycle_count += 1
            cycle_events = 0

    # includiamo lo slot 0 nel denominatore
    mean_cost = sum_cost / (len(events) + 1)
    return mean_cost, total_reloc, effective_events, cycle_count
