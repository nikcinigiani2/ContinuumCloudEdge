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
      - costo medio Centralized, Greedy Static e Greedy Dynamic modificato
      - numero di rilocazioni (reallocazioni di righe) al ricalcolo Centralized
      - numero di rilocazioni al ricalcolo Dynamic

    Restituisce: (mean_c, mean_gs, mean_gd, total_reloc_centralized, total_reloc_dynamic)
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
    # Centralized
    c_cost, _, partsC = centralized_allocate(
        app_cost, totAppl, cap_edge, service_rate_edge, num_edge, mu_appl
    )
    partsC = [list(r) for r in partsC]

    # Greedy Static
    _, partsG_static, _ = greedy_allocate(
        app_cost, totAppl,
        cap_edge.copy(), service_rate_edge,
        num_edge, mu_appl
    )
    partsG_static = [list(r) for r in partsG_static]

    # Greedy Dynamic modificato
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

    # Lista dove accumulo le rilocazioni ad ogni ricalcolo
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
            mu_appl = handle_death(
                idx, app_cost, totAppl,
                partsC, partsG_dynamic,
                mu_appl
            )
            # Rimuovo la stessa riga in partsG_static se esiste
            if 0 <= idx < len(partsG_static):
                del partsG_static[idx]

        elif ev == 'birth_lambda':
            # Nuova λ-app: handle_birth_lambda aggiorna app_cost, totAppl, partsC e partsG_dynamic (riga zero)
            handle_birth_lambda(app_cost, totAppl, partsC, partsG_dynamic)

            # --- Greedy Static: assegno subito la new λ-app
            q = totAppl[-1]
            costs = app_cost[-1]
            j_min = min(range(num_cols), key=lambda j: costs[j])
            row_static = [0] * num_cols
            row_static[j_min] = q
            partsG_static.append(row_static)

            # --- Greedy Dynamic modificato: tolgo la riga zero e la riassegno subito ---
            partsG_dynamic.pop()  # rimuovo la riga di zeri
            row_dynamic = [0] * num_cols
            row_dynamic[j_min] = q
            partsG_dynamic.append(row_dynamic)

        elif ev == 'birth_mu':
            handle_birth_mu(app_cost, totAppl, partsC, partsG_dynamic)
            mu_appl += 1

            # --- Greedy Static: assegno subito la new μ-app
            costs = app_cost[-1]
            j_min = min(range(num_cols), key=lambda j: costs)
            row_static = [0] * num_cols
            row_static[j_min] = 1
            partsG_static.append(row_static)

            # --- Greedy Dynamic modificato: tolgo la riga zero e la riassegno subito ---
            partsG_dynamic.pop()
            row_dynamic = [0] * num_cols
            row_dynamic[j_min] = 1
            partsG_dynamic.append(row_dynamic)

        elif ev == 'migration':
            idx = info
            # Rimuovo la vecchia app
            mu_appl = handle_death(
                idx, app_cost, totAppl,
                partsC, partsG_dynamic,
                mu_appl
            )
            if 0 <= idx < len(partsG_static):
                del partsG_static[idx]

            # Inverse birth: ricreo come λ o μ
            if idx < (len(totAppl) - mu_appl):
                # diventava λ → ora new μ
                handle_birth_mu(app_cost, totAppl, partsC, partsG_dynamic)
                mu_appl += 1

                # Greedy Static: assegno subito la new μ
                costs = app_cost[-1]
                j_min = min(range(num_cols), key=lambda j: costs)
                row_static = [0] * num_cols
                row_static[j_min] = 1
                partsG_static.append(row_static)

                # Greedy Dynamic: tolgo riga zero e assegno subito
                partsG_dynamic.pop()
                row_dynamic = [0] * num_cols
                row_dynamic[j_min] = 1
                partsG_dynamic.append(row_dynamic)

            else:
                # diventava μ → ora new λ
                handle_birth_lambda(app_cost, totAppl, partsC, partsG_dynamic)

                # Greedy Static: assegno subito la new λ
                q = totAppl[-1]
                costs = app_cost[-1]
                j_min = min(range(num_cols), key=lambda j: costs)
                row_static = [0] * num_cols
                row_static[j_min] = q
                partsG_static.append(row_static)

                # Greedy Dynamic: tolgo riga zero e assegno subito
                partsG_dynamic.pop()
                row_dynamic = [0] * num_cols
                row_dynamic[j_min] = q
                partsG_dynamic.append(row_dynamic)

        # 4.2) ricalcolo globale ogni ne eventi
        if event_count % ne == 0:
            # ── Centralized ──
            # salvo copia precedente di partsC per contare le rilocazioni
            oldC = [row.copy() for row in partsC]

            c_cost, _, partsC = centralized_allocate(
                app_cost, totAppl,
                cap_edge, service_rate_edge,
                num_edge, mu_appl
            )
            partsC = [list(r) for r in partsC]

            # conto quante righe cambiano tra oldC e new partsC
            relocC = sum(1 for i in range(len(partsC)) if oldC[i] != partsC[i])
            total_reloc_centralized += relocC

            # ── Greedy Static ──
            _, partsG_static, _ = greedy_allocate(
                app_cost, totAppl,
                cap_edge.copy(), service_rate_edge,
                num_edge, mu_appl
            )
            partsG_static = [list(r) for r in partsG_static]

            # ── Greedy Dynamic globale ──
            # salvo copia precedente di partsG_dynamic per contare le rilocazioni
            oldG = [row.copy() for row in partsG_dynamic]

            _, partsG_dynamic, _ = greedy_allocate(
                app_cost, totAppl,
                cap_edge.copy(), service_rate_edge,
                num_edge, mu_appl
            )
            partsG_dynamic = [list(r) for r in partsG_dynamic]

            # conto quante righe cambiano tra oldG e new partsG_dynamic
            relocG = sum(1 for i in range(len(partsG_dynamic)) if oldG[i] != partsG_dynamic[i])
            total_reloc_dynamic += relocG

        # 4.3) accumulo costi correnti (dopo eventuale ricalcolo)
        sum_c  += recompute_central_cost(app_cost, partsC)
        sum_gs += recompute_central_cost(app_cost, partsG_static)
        sum_gd += recompute_central_cost(app_cost, partsG_dynamic)

        event_count += 1

    # restituisco anche i conteggi di rilocazioni
    return (sum_c / T,
            sum_gs / T,
            sum_gd / T,
            total_reloc_centralized,
            total_reloc_dynamic)
