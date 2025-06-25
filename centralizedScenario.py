from allocation import centralized_allocate

def run_centralized(init_data, events, regime, ne):
    """
    Centralized: ricalcolo ogni ne eventi effettivi, nuove app sempre sul cloud.
    Ora restituisce anche cost_per_slot.
    """
    app_cost          = [r.tolist() for r in init_data['app_cost']]
    totAppl           = list(init_data['totAppl'])
    service_rate_edge = init_data['service_rate_edge']
    num_edge          = init_data['num_edge']
    mu_appl           = init_data['mu_appl']
    containers        = 5 if regime == 'scarsità' else 10
    full_cap          = [containers * r for r in service_rate_edge]

    cost_per_slot = []
    total_reloc = effective_events = cycle_events = cycle_count = 0

    # slot 0
    c0, _, parts0 = centralized_allocate(app_cost, totAppl, full_cap.copy(), service_rate_edge, num_edge, mu_appl)
    last_parts = [row.tolist() for row in parts0]
    cost_per_slot.append(c0)
    cycle_count = 1

    # simulate
    for typ, *args in events:
        # apply event
        if typ == 'death':
            idx = args[0]
            del last_parts[idx]; del app_cost[idx]; del totAppl[idx]
            if idx < mu_appl: mu_appl -= 1
        elif typ in ('birth_lambda','birth_mu'):
            d = args[0]; q=int(d['totAppl'][-1]); costs=d['app_cost'][-1].tolist()
            app_cost.append(costs); totAppl.append(q)
            if typ=='birth_mu': mu_appl+=1
            row=[0]*(num_edge+1); row[num_edge]=q; last_parts.append(row)
        elif typ=='migration':
            idx,new_type,d=args
            del last_parts[idx]; del app_cost[idx]; del totAppl[idx]
            if idx<mu_appl: mu_appl-=1
            q=int(d['totAppl'][-1]); costs=d['app_cost'][-1].tolist()
            app_cost.append(costs); totAppl.append(q)
            if new_type=='mu': mu_appl+=1
            row=[0]*(num_edge+1); row[num_edge]=q; last_parts.append(row)

        # cost for this slot
        slot_cost = sum(last_parts[i][j]*app_cost[i][j]
                        for i in range(len(last_parts))
                        for j in range(len(last_parts[i])))
        cost_per_slot.append(slot_cost)

        # recalc if needed
        if typ in ('death','birth_lambda','birth_mu','migration'):
            effective_events+=1; cycle_events+=1
            if cycle_events==ne:
               #stampa inizio ciclo centralized
                print(f'Centralized cycle {cycle_count}' )
                cr, _, pr = centralized_allocate(app_cost, totAppl, full_cap.copy(), service_rate_edge, num_edge, mu_appl)
                reloc = sum(1 for i in range(len(pr)) if pr[i].tolist()!=last_parts[i])
                total_reloc+=reloc
                last_parts=[row.tolist() for row in pr]
                cost_per_slot[-1]+=cr
                cycle_count+=1; cycle_events=0

    mean_cost = sum(cost_per_slot)/30000
    return mean_cost, total_reloc, effective_events, cycle_count, cost_per_slot
