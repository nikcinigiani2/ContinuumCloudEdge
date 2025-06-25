from allocation import greedy_allocate

def run_matchingDynamic(init_data, events, regime, ne):
    app_cost=[r.tolist() for r in init_data['app_cost']]
    totAppl=list(init_data['totAppl']); service_rate_edge=init_data['service_rate_edge']
    num_edge=init_data['num_edge']; mu_appl=init_data['mu_appl']
    containers=5 if regime=='scarsità' else 10
    full_cap=[containers*r for r in service_rate_edge]
    cost_per_slot=[]; total_reloc=effective_events=cycle_events=cycle_count=0
    # slot0
    _, parts0, c0=greedy_allocate(app_cost, totAppl, full_cap.copy(), service_rate_edge, num_edge, mu_appl)
    last_parts=[r.copy() for r in parts0]; cost_per_slot.append(c0)
    cap_edge=full_cap.copy()
    for row in last_parts:
        for j in range(num_edge): cap_edge[j]-=row[j]
    cycle_count=1
    for typ,*args in events:
        if typ in ('death','birth_lambda','birth_mu','migration'):
            effective_events+=1; cycle_events+=1; old=[r.copy() for r in last_parts]
        if typ=='death':
            idx=args[0]
            for j in range(num_edge): cap_edge[j]+=last_parts[idx][j]
            del last_parts[idx]; del app_cost[idx]; del totAppl[idx]
            if idx<mu_appl: mu_appl-=1
        elif typ in ('birth_lambda','birth_mu'):
            d=args[0]; q=int(d['totAppl'][-1]); costs=d['app_cost'][-1].tolist()
            app_cost.append(costs); totAppl.append(q)
            if typ=='birth_mu': mu_appl+=1
            cand=[j for j in range(num_edge) if cap_edge[j]>=q]
            jm=min(cand,key=lambda j:costs[j]) if cand else num_edge
            if jm<num_edge: cap_edge[jm]-=q
            row=[0]*(num_edge+1); row[jm]=q; last_parts.append(row)
        elif typ=='migration':
            idx,new_type,d=args
            for j in range(num_edge): cap_edge[j]+=last_parts[idx][j]
            del last_parts[idx]; del app_cost[idx]; del totAppl[idx]
            if idx<mu_appl: mu_appl-=1
            q=int(d['totAppl'][-1]); costs=d['app_cost'][-1].tolist()
            app_cost.append(costs); totAppl.append(q)
            if new_type=='mu': mu_appl+=1
            cand=[j for j in range(num_edge) if cap_edge[j]>=q]
            jm=min(cand,key=lambda j:costs[j]) if cand else num_edge
            if jm<num_edge: cap_edge[jm]-=q
            row=[0]*(num_edge+1); row[jm]=q; last_parts.append(row)
        sc=sum(last_parts[i][j]*app_cost[i][j] for i in range(len(last_parts)) for j in range(len(last_parts[i])))
        cost_per_slot.append(sc)
        if typ in ('death','birth_lambda','birth_mu','migration') and cycle_events==ne:
            _, pr, cr=greedy_allocate(app_cost, totAppl, full_cap.copy(), service_rate_edge, num_edge, mu_appl)
            reloc=sum(1 for i in range(len(pr)) if pr[i]!=last_parts[i])
            total_reloc+=reloc
            last_parts=[r.copy() for r in pr]
            cap_edge=full_cap.copy()
            for row in last_parts:
                for j in range(num_edge): cap_edge[j]-=row[j]
            cost_per_slot[-1]+=cr
            cycle_count+=1; cycle_events=0
    mean_cost=sum(cost_per_slot)/len(cost_per_slot)
    return mean_cost, total_reloc, effective_events, cycle_count, cost_per_slot
