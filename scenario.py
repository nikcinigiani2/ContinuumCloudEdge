import random
import time
from copy import deepcopy
from dataGenerator import generate_data
from simulation import (
    handle_birth_lambda,
    handle_birth_mu,
    handle_death
)
from allocation import centralized_allocate, greedy_allocate
from simulation import nm, p

def recompute_central_cost(app_cost, parts):
    total = 0
    for i, row in enumerate(parts):
        costs = app_cost[i]
        for j, qty in enumerate(row):
            total += qty * costs[j]
    return total

def generate_scenario(timeHorizon, base_init):
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
    Riapplica gli eventi su init_data e calcola:
      - costo medio Centralized
      - costo medio Greedy Static senza ricalcoli globali
      - costo medio Greedy Dynamic modificato (con ricalcoli ogni ne eventi)
      - numero di rilocazioni Centralized e Dynamic

    In questa versione, Greedy Static fa un solo ricalcolo iniziale con greedy_allocate
    e poi aggiorna le nuove app “on-the-fly” senza mai ricalcolare globalmente.
    """
    # --- 1) stato iniziale ---
    app_cost = [r.tolist() for r in init_data['app_cost']]
    totAppl  = list(init_data['totAppl'])
    service_rate_edge = init_data['service_rate_edge']
    num_edge = init_data['num_edge']
    mu_appl  = init_data['mu_appl']

    # capacità per regime
    containers = 5 if regime == 'scarsità' else 15
    cap_edge   = [containers * r for r in service_rate_edge]

    # --- 2) partizioni iniziali ---
    # Centralized (ricalcolato ogni ne eventi)
    c_cost, _, partsC = centralized_allocate(
        app_cost, totAppl, cap_edge, service_rate_edge, num_edge, mu_appl
    )
    partsC = [list(r) for r in partsC]

    # Greedy Static: unico ricalcolo iniziale
    _, partsG_static, _ = greedy_allocate(
        app_cost, totAppl,
        cap_edge.copy(), service_rate_edge,
        num_edge, mu_appl
    )
    partsG_static = [list(r) for r in partsG_static]

    # Greedy Dynamic modificato: “on-the-fly” + ricalcoli ogni ne eventi
    _, partsG_dynamic, _ = greedy_allocate(
        app_cost, totAppl,
        cap_edge.copy(), service_rate_edge,
        num_edge, mu_appl
    )
    partsG_dynamic = [list(r) for r in partsG_dynamic]

    # --- Debug iniziale ---
    T = len(events)
    print(f"[DEBUG] Regime={regime}, ne={ne}, eventi={T} → avvio replay", flush=True)

    # --- 3) accumuli e contatori ---
    sum_c = sum_gs = sum_gd = 0.0
    event_count = 0
    ciclo = 0
    num_cols = num_edge + 1  # num_edge edge + 1 colonna cloud

    total_reloc_centralized = 0
    total_reloc_dynamic    = 0

    # --- 4) ciclo sugli eventi ---
    for ev, info in events:
        # Debug di inizio ciclo
        if event_count % ne == 0:
            ciclo += 1
            print(f"[DEBUG]  Inizio ciclo {ciclo}: evento {event_count}/{T}", flush=True)

        # 4.1) applica evento su tutte le strutture
        if ev == 'death':
            idx = info
            # Centralized & Dynamic: handle_death rimuove la riga
            mu_appl = handle_death(
                idx, app_cost, totAppl,
                partsC, partsG_dynamic,
                mu_appl
            )
            # Static: rimuovo la riga corrispondente
            if 0 <= idx < len(partsG_static):
                del partsG_static[idx]

        elif ev == 'birth_lambda':
            # Centralized & Dynamic: handle_birth_lambda aggiunge riga zero in partsC e partsG_dynamic
            handle_birth_lambda(app_cost, totAppl, partsC, partsG_dynamic)

            # Static: assegna subito la nuova λ-app
            q = totAppl[-1]
            costs = app_cost[-1]
            j_min = min(range(num_cols), key=lambda j: costs[j])
            row_static = [0] * num_cols
            row_static[j_min] = q
            partsG_static.append(row_static)

            # Dynamic modificato: tolgo la riga zero e assegno subito
            partsG_dynamic.pop()
            row_dynamic = [0] * num_cols
            row_dynamic[j_min] = q
            partsG_dynamic.append(row_dynamic)

        elif ev == 'birth_mu':
            # Centralized & Dynamic: handle_birth_mu aggiunge riga zero in partsC e partsG_dynamic
            handle_birth_mu(app_cost, totAppl, partsC, partsG_dynamic)
            mu_appl += 1

            # Static: assegna subito la nuova μ-app
            costs = app_cost[-1]
            j_min = min(range(num_cols), key=lambda j: costs)
            row_static = [0] * num_cols
            row_static[j_min] = 1
            partsG_static.append(row_static)

            # Dynamic modificato: tolgo riga zero e assegno subito
            partsG_dynamic.pop()
            row_dynamic = [0] * num_cols
            row_dynamic[j_min] = 1
            partsG_dynamic.append(row_dynamic)

        elif ev == 'migration':
            idx = info
            # Centralized & Dynamic: rimuovo la vecchia app
            mu_appl = handle_death(
                idx, app_cost, totAppl,
                partsC, partsG_dynamic,
                mu_appl
            )
            # Static: rimuovo la riga in partsG_static
            if 0 <= idx < len(partsG_static):
                del partsG_static[idx]

            # Inverse birth: ricreo come λ o μ
            if idx < (len(totAppl) - mu_appl):
                # diventava λ → ora nuova μ
                handle_birth_mu(app_cost, totAppl, partsC, partsG_dynamic)
                mu_appl += 1

                # Static: assegno subito la nuova μ
                costs = app_cost[-1]
                j_min = min(range(num_cols), key=lambda j: costs)
                row_static = [0] * num_cols
                row_static[j_min] = 1
                partsG_static.append(row_static)

                # Dynamic: tolgo riga zero e assegno subito
                partsG_dynamic.pop()
                row_dynamic = [0] * num_cols
                row_dynamic[j_min] = 1
                partsG_dynamic.append(row_dynamic)

            else:
                # diventava μ → ora nuova λ
                handle_birth_lambda(app_cost, totAppl, partsC, partsG_dynamic)

                # Static: assegno subito la nuova λ
                q = totAppl[-1]
                costs = app_cost[-1]
                j_min = min(range(num_cols), key=lambda j: costs)
                row_static = [0] * num_cols
                row_static[j_min] = q
                partsG_static.append(row_static)

                # Dynamic: tolgo riga zero e assegno subito
                partsG_dynamic.pop()
                row_dynamic = [0] * num_cols
                row_dynamic[j_min] = q
                partsG_dynamic.append(row_dynamic)

        # 4.2) ricalcolo globale ogni ne eventi in Centralized e Dynamic
        if event_count % ne == 0:
            # —— Centralized ——
            oldC = [row.copy() for row in partsC]
            c_cost, _, partsC = centralized_allocate(
                app_cost, totAppl,
                cap_edge, service_rate_edge,
                num_edge, mu_appl
            )
            partsC = [list(r) for r in partsC]
            relocC = sum(1 for i in range(len(partsC)) if oldC[i] != partsC[i])
            total_reloc_centralized += relocC

            # —— Greedy Dynamic globale ——
            oldG = [row.copy() for row in partsG_dynamic]
            _, partsG_dynamic, _ = greedy_allocate(
                app_cost, totAppl,
                cap_edge.copy(), service_rate_edge,
                num_edge, mu_appl
            )
            partsG_dynamic = [list(r) for r in partsG_dynamic]
            relocG = sum(1 for i in range(len(partsG_dynamic)) if oldG[i] != partsG_dynamic[i])
            total_reloc_dynamic += relocG

        # 4.3) accumulo costi correnti
        sum_c  += recompute_central_cost(app_cost, partsC)
        sum_gs += recompute_central_cost(app_cost, partsG_static)   # Static non ricalcola più
        sum_gd += recompute_central_cost(app_cost, partsG_dynamic)

        event_count += 1

    return (
        sum_c / T,
        sum_gs / T,
        sum_gd / T,
        total_reloc_centralized,
        total_reloc_dynamic
    )
