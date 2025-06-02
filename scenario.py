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
    Riapplica gli eventi su init_data e calcola i costi medi per:
      - centralized
      - greedy static (on‐the‐fly + global ogni ne)
      - greedy dynamic modificato (on‐the‐fly + global ogni ne)
    In questa versione, il matching dinamico alloca subito ogni nuova app al nodo
    col costo unitario minore, anziché lasciarla disallocata fino al prossimo ricalcolo.
    """
    # --- 1) stato iniziale ---
    app_cost = [r.tolist() for r in init_data['app_cost']]
    totAppl  = list(init_data['totAppl'])
    service_rate_edge = init_data['service_rate_edge']
    num_edge = init_data['num_edge']
    mu_appl  = init_data['mu_appl']

    # capacità per regime
    containers = 5 if regime == 'scarsità' else 10
    cap_edge   = [containers * r for r in service_rate_edge]

    # --- 2) partizioni iniziali ---
    # centralized
    c_cost, _, partsC = centralized_allocate(
        app_cost, totAppl, cap_edge, service_rate_edge, num_edge, mu_appl
    )
    partsC = [list(r) for r in partsC]

    # greedy static
    _, partsG_static, _ = greedy_allocate(
        app_cost, totAppl,
        cap_edge.copy(), service_rate_edge,
        num_edge, mu_appl
    )
    partsG_static = [list(r) for r in partsG_static]

    # greedy dynamic modificato
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
    num_cols = num_edge + 1  # numero di colonne = num_edge + 1 (l'ultima = cloud)

    # --- 4) ciclo sugli eventi ---
    for ev, info in events:
        # Stampo inizio di ogni ciclo (ogni ne eventi)
        if event_count % ne == 0:
            ciclo += 1
            print(f"[DEBUG]  Inizio ciclo {ciclo}: evento {event_count}/{T}", flush=True)

        # 4.1) applica evento su tutte le strutture
        if ev == 'death':
            idx = info
            # rimuove da app_cost e totAppl e decrementa mu_appl se necessario
            mu_appl = handle_death(
                idx, app_cost, totAppl,
                partsC, partsG_dynamic,
                mu_appl
            )
            # rimuove anche da partsG_static
            if 0 <= idx < len(partsG_static):
                del partsG_static[idx]

        elif ev == 'birth_lambda':
            # genera dati per la nuova λ-app e inserisce riga zero in partsC e partsG_dynamic
            handle_birth_lambda(app_cost, totAppl, partsC, partsG_dynamic)

            # --- GREEDY STATIC: assegno subito la nuova λ-app ---
            costs = app_cost[-1]          # vettore costi (length = num_cols)
            q = totAppl[-1]               # domanda della nuova λ-app
            j_min = min(range(num_cols), key=lambda j: costs[j])
            row_static = [0] * num_cols
            row_static[j_min] = q
            partsG_static.append(row_static)

            # --- GREEDY DYNAMIC MODIFICATO: assegno subito la nuova λ-app ---
            partsG_dynamic.pop()  # tolgo la riga di zeri
            row_dynamic = [0] * num_cols
            row_dynamic[j_min] = q
            partsG_dynamic.append(row_dynamic)

        elif ev == 'birth_mu':
            # genera dati per la nuova μ-app e inserisce riga zero in partsC e partsG_dynamic
            handle_birth_mu(app_cost, totAppl, partsC, partsG_dynamic)
            mu_appl += 1

            # --- GREEDY STATIC: assegno subito la nuova μ-app ---
            costs = app_cost[-1]        # costi unitari della nuova μ-app
            j_min = min(range(num_cols), key=lambda j: costs[j])
            row_static = [0] * num_cols
            row_static[j_min] = 1
            partsG_static.append(row_static)

            # --- GREEDY DYNAMIC MODIFICATO: assegno subito la nuova μ-app ---
            partsG_dynamic.pop()  # tolgo la riga di zeri
            row_dynamic = [0] * num_cols
            row_dynamic[j_min] = 1
            partsG_dynamic.append(row_dynamic)

        elif ev == 'migration':
            idx = info
            # rimuovo la vecchia app
            mu_appl = handle_death(
                idx, app_cost, totAppl,
                partsC, partsG_dynamic,
                mu_appl
            )
            # rimuovo anche da partsG_static
            if 0 <= idx < len(partsG_static):
                del partsG_static[idx]

            # inverse birth: ricreo nuova app (λ o μ)
            if idx < (len(totAppl) - mu_appl):
                # era una λ-app → diventa nuova μ-app
                handle_birth_mu(app_cost, totAppl, partsC, partsG_dynamic)
                mu_appl += 1

                # GREEDY STATIC: assegno subito la nuova μ-app
                costs = app_cost[-1]
                j_min = min(range(num_cols), key=lambda j: costs)
                row_static = [0] * num_cols
                row_static[j_min] = 1
                partsG_static.append(row_static)

                # GREEDY DYNAMIC MODIFICATO: assegno subito la nuova μ-app
                partsG_dynamic.pop()
                row_dynamic = [0] * num_cols
                row_dynamic[j_min] = 1
                partsG_dynamic.append(row_dynamic)

            else:
                # era una μ-app → diventa nuova λ-app
                handle_birth_lambda(app_cost, totAppl, partsC, partsG_dynamic)

                # GREEDY STATIC: assegno subito la nuova λ-app
                costs = app_cost[-1]
                q = totAppl[-1]
                j_min = min(range(num_cols), key=lambda j: costs)
                row_static = [0] * num_cols
                row_static[j_min] = q
                partsG_static.append(row_static)

                # GREEDY DYNAMIC MODIFICATO: assegno subito la nuova λ-app
                partsG_dynamic.pop()
                row_dynamic = [0] * num_cols
                row_dynamic[j_min] = q
                partsG_dynamic.append(row_dynamic)

        # 4.2) ricalcolo globale ogni ne eventi
        if event_count % ne == 0:
            # centralized
            c_cost, _, partsC = centralized_allocate(
                app_cost, totAppl,
                cap_edge, service_rate_edge,
                num_edge, mu_appl
            )
            partsC = [list(r) for r in partsC]

            # greedy static (ricalcola tutto da zero)
            _, partsG_static, _ = greedy_allocate(
                app_cost, totAppl,
                cap_edge.copy(), service_rate_edge,
                num_edge, mu_appl
            )
            partsG_static = [list(r) for r in partsG_static]

            # greedy dynamic globale (ricalcola tutto da zero)
            _, partsG_dynamic, _ = greedy_allocate(
                app_cost, totAppl,
                cap_edge.copy(), service_rate_edge,
                num_edge, mu_appl
            )
            partsG_dynamic = [list(r) for r in partsG_dynamic]

        # 4.3) accumulo costi correnti (dopo eventuale ricalcolo)
        sum_c  += recompute_central_cost(app_cost, partsC)
        sum_gs += recompute_central_cost(app_cost, partsG_static)
        sum_gd += recompute_central_cost(app_cost, partsG_dynamic)

        event_count += 1

    # restituisco le tre medie dei costi
    return sum_c / T, sum_gs / T, sum_gd / T
