# scenario.py

import random
from copy import deepcopy
from dataGenerator import generate_data
from simulation import (
    handle_birth_lambda,
    handle_birth_mu,
    handle_death
)
from allocation import centralized_allocate, greedy_allocate

# tassi globali
from simulation import nm, p


def recompute_central_cost(app_cost, parts):
    """
    Calcola il costo totale dato app_cost e parts di stessa lunghezza.
    """
    total = 0
    for i, row in enumerate(parts):
        costs = app_cost[i]
        for j, qty in enumerate(row):
            total += qty * costs[j]
    return total


def generate_scenario(timeHorizon, base_init):
    """
    Genera una sequenza di eventi (death, birth_lambda, birth_mu, migration, noop)
    restituendo copia dello stato iniziale e lista di eventi.
    """
    app_cost = [r.tolist() for r in base_init['app_cost']]
    totAppl  = list(base_init['totAppl'])
    mu_appl  = base_init['mu_appl']
    events   = []

    for _ in range(timeHorizon):
        lam_appl = len(totAppl) - mu_appl
        qi = p * (1 + lam_appl + mu_appl) / (lam_appl + mu_appl) if lam_appl+mu_appl>0 else 0
        ri = nm * p
        x1, x2 = random.random(), random.random()
        N = len(totAppl)

        if x1 < qi and N>0:
            idx = random.randrange(N)
            events.append(('death', idx))
            mu_appl = handle_death(idx, app_cost, totAppl, [], [], mu_appl)

        elif x1 < qi + p:
            d = generate_data()
            if x2 < 0.5:
                events.append(('birth_lambda', d))
                handle_birth_lambda(app_cost, totAppl, [], [])
            else:
                events.append(('birth_mu', d))
                handle_birth_mu(app_cost, totAppl, [], [])
                mu_appl += 1

        elif x1 < qi + p + ri and N>0:
            idx = random.randrange(N)
            events.append(('migration', idx))
            mu_appl = handle_death(idx, app_cost, totAppl, [], [], mu_appl)
            if x2 < 0.5:
                handle_birth_mu(app_cost, totAppl, [], [])
                mu_appl += 1
            else:
                handle_birth_lambda(app_cost, totAppl, [], [])
        else:
            events.append(('noop', None))

    return deepcopy(base_init), events


def replay_scenario(init_data, events, regime, ne):
    """
    Riapplica gli eventi su init_data e accumula costo medio
    per centralized, greedy static e greedy dynamic.
    """
    app_cost = [r.tolist() for r in init_data['app_cost']]
    totAppl  = list(init_data['totAppl'])
    service_rate_edge = init_data['service_rate_edge']
    num_edge = init_data['num_edge']
    mu_appl  = init_data['mu_appl']

    containers = 5 if regime=='scarsità' else 10
    cap_edge   = [containers*r for r in service_rate_edge]

    # allocazioni iniziali
    c_cost, _, partsC = centralized_allocate(
        app_cost, totAppl, cap_edge, service_rate_edge, num_edge, mu_appl
    )
    partsC = [list(r) for r in partsC]

    _, partsG_static, g_static = greedy_allocate(
        app_cost, totAppl, cap_edge.copy(), service_rate_edge, num_edge, mu_appl
    )
    partsG_static = [list(r) for r in partsG_static]
    # inizializzo dynamic con static copy
    partsG_dynamic = [row.copy() for row in partsG_static]

    sum_c = sum_gs = sum_gd = 0.0
    event_count = 0

    # static partition colonne
    num_cols = len(partsG_static[0])

    print(f"[DEBUG] Regime={regime}, ne={ne} → avvio replay", flush=True)
    for ev, info in events:
        if ev=='death':
            idx = info
            mu_appl = handle_death(idx, app_cost, totAppl, partsC, partsG_dynamic, mu_appl)
            del partsG_static[idx]
        elif ev=='birth_lambda':
            handle_birth_lambda(app_cost, totAppl, partsC, partsG_dynamic)
            partsG_static.append([0]*num_cols)
        elif ev=='birth_mu':
            handle_birth_mu(app_cost, totAppl, partsC, partsG_dynamic)
            mu_appl += 1
            partsG_static.append([0]*num_cols)
        elif ev=='migration':
            idx = info
            mu_appl = handle_death(idx, app_cost, totAppl, partsC, partsG_dynamic, mu_appl)
            del partsG_static[idx]
            if info < (len(totAppl)-mu_appl):
                handle_birth_mu(app_cost, totAppl, partsC, partsG_dynamic)
                mu_appl += 1
            else:
                handle_birth_lambda(app_cost, totAppl, partsC, partsG_dynamic)
            partsG_static.append([0]*num_cols)
        # noop: no state change

        # centralized: ricalcolo ogni ne eventi
        if event_count % ne == 0:
            c_cost, _, partsC = centralized_allocate(
                app_cost, totAppl, cap_edge, service_rate_edge, num_edge, mu_appl
            )
            partsC = [list(r) for r in partsC]
        sum_c  += recompute_central_cost(app_cost, partsC)
        # greedy static: costo corrente
        sum_gs += recompute_central_cost(app_cost, partsG_static)
        # greedy dynamic: ricalcolo ogni ne
        if event_count % ne == 0:
            _, partsG_dynamic, _ = greedy_allocate(
                app_cost, totAppl, cap_edge.copy(), service_rate_edge, num_edge, mu_appl
            )
        sum_gd += recompute_central_cost(app_cost, partsG_dynamic)

        event_count += 1

    T = len(events)
    return sum_c/T, sum_gs/T, sum_gd/T
