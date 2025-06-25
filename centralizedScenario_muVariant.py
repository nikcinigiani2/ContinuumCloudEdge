import numpy as np
from allocation import centralized_allocate

def run_centralized_mu_variant(init_data, events, regime, ne):
    """
    Variante MU:
    - Ricalcolo globale ogni ne eventi effettivi
    - Prime allocazioni e ricalcoli con centralized_allocate
    - Tra ricalcoli:
      * lambda_app -> sempre cloud
      * mu_app -> greedy on-the-fly: edge meno costoso disponibile, altrimenti cloud
    - Restituisce (mean_cost, total_reloc, total_effective_events, total_cycles)
    """
    # Stato iniziale
    app_cost          = [r.tolist() for r in init_data['app_cost']]
    totAppl           = list(init_data['totAppl'])
    service_rate_edge = init_data['service_rate_edge']
    num_edge          = init_data['num_edge']
    mu_appl           = init_data['mu_appl']

    # Capacità edge
    containers = 5 if regime == 'scarsità' else 10
    full_cap   = [containers * r for r in service_rate_edge]

    sum_cost         = 0.0
    total_reloc      = 0
    effective_events = 0
    cycle_events     = 0
    cycle_count      = 0

    # --- slot 0: prima allocazione globale ---
    cost0, _, parts0 = centralized_allocate(
        app_cost, totAppl, full_cap.copy(), service_rate_edge, num_edge, mu_appl
    )
    last_parts = [row.tolist() for row in parts0]
    sum_cost   += cost0
    cycle_count += 1

    # Mantieni capacità residua tra ricalcoli
    cap_edge = full_cap.copy()
    # calcola usata dagli edge nel partizionamento iniziale
    for row in last_parts:
        for j in range(num_edge):
            cap_edge[j] -= row[j]

    # Elaborazione eventi
    for typ, *args in events:
        is_eff = typ in ('death','birth_lambda','birth_mu','migration')
        if is_eff:
            effective_events += 1
            cycle_events     += 1
            old_parts = [row.copy() for row in last_parts]

        # 1) Gestione evento
        if typ == 'death':
            idx = args[0]
            # libera capacità
            for j in range(num_edge): cap_edge[j] += last_parts[idx][j]
            # rimuovi app
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
            # aggiorna mu count
            if typ == 'birth_mu': mu_appl += 1
            # on-the-fly
            if typ == 'birth_lambda':
                # sempre cloud
                row = [0]*(num_edge+1)
                row[num_edge] = q
            else:
                # mu: greedy edge
                # candidates con cap sufficiente
                cand = [j for j in range(num_edge) if cap_edge[j] >= q]
                if cand:
                    # costo locale
                    j_min = min(cand, key=lambda j: costs[j])
                    cap_edge[j_min] -= q
                    row = [0]*(num_edge+1)
                    row[j_min] = q
                else:
                    row = [0]*(num_edge+1)
                    row[num_edge] = q
            last_parts.append(row)

        elif typ == 'migration':
            idx, new_type, d = args
            # remove old
            for j in range(num_edge): cap_edge[j] += last_parts[idx][j]
            del last_parts[idx]
            del app_cost[idx]
            del totAppl[idx]
            if idx < mu_appl: mu_appl -= 1
            # nuova app
            q     = int(d['totAppl'][-1])
            costs = d['app_cost'][-1].tolist()
            app_cost.append(costs)
            totAppl.append(q)
            if new_type == 'mu': mu_appl += 1
            # greedy per mu, lambda->cloud
            if new_type == 'lambda':
                row = [0]*(num_edge+1)
                row[num_edge] = q
            else:
                cand = [j for j in range(num_edge) if cap_edge[j] >= q]
                if cand:
                    j_min = min(cand, key=lambda j: costs[j])
                    cap_edge[j_min] -= q
                    row = [0]*(num_edge+1)
                    row[j_min] = q
                else:
                    row = [0]*(num_edge+1)
                    row[num_edge] = q
            last_parts.append(row)

        # 2) Costo slot dopo evento
        slot_cost = sum(
            last_parts[i][j] * app_cost[i][j]
            for i in range(len(last_parts))
            for j in range(len(last_parts[i]))
        )
        sum_cost += slot_cost

        # 3) Ricalcolo globale ogni ne eventi
        if cycle_events == ne:
            cost_r, _, parts_r = centralized_allocate(
                app_cost, totAppl, full_cap.copy(), service_rate_edge, num_edge, mu_appl
            )
            new_parts = [row.tolist() for row in parts_r]
            # conteggio rilocazioni
            reloc = sum(1 for i in range(len(new_parts)) if new_parts[i] != last_parts[i])
            total_reloc += reloc
            # aggiorna stato e capacità
            last_parts = new_parts
            # ricostruisci cap_edge
            cap_edge = full_cap.copy()
            for row in last_parts:
                for j in range(num_edge): cap_edge[j] -= row[j]
            sum_cost += cost_r
            cycle_count += 1
            cycle_events = 0

    # mean sul timeHorizon+1
    mean_cost = sum_cost / 30000
    return mean_cost, total_reloc, effective_events, cycle_count
