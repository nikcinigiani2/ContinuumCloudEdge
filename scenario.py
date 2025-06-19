import random
import time
from copy import deepcopy
from dataGenerator import generate_data
from allocation import centralized_allocate, greedy_allocate



from dataGenerator import generate_data

# Parametri fissi
nm = 6    # numero di nodi edge (per il tasso di migrazione)
p  = 0.05 # probabilità base di nascita pura

def handle_birth_lambda(app_cost, totAppl, partsC, partsG, d):
    """
    Gestisce la nascita di una λ-app a partire dai dati già generati in d:
      - app_cost, totAppl, partsC, partsG: strutture da aggiornare
      - d: dizionario restituito da generate_data() con i parametri dell’app
    """
    new_cost = d['app_cost'][-1].tolist()
    new_tot  = int(d['totAppl'][-1])

    # 1) aggiorno costo e domanda
    app_cost.append(new_cost)
    totAppl.append(new_tot)

    num_cols = len(new_cost)
    # 2) centralized: tutta la domanda sul cloud (ultima colonna)
    rowC = [0] * num_cols
    rowC[-1] = new_tot
    partsC.append(rowC)

    # 3) dynamic greedy: nessuna allocazione finché non ricalcolo
    partsG.append([0] * num_cols)


def handle_birth_mu(app_cost, totAppl, partsC, partsG, d):
    """
    Gestisce la nascita di una µ-app a partire dai dati già generati in d.
    """
    new_cost = d['app_cost'][-1].tolist()
    new_tot  = int(d['totAppl'][-1])  # tipicamente 1, ma usiamo il valore

    app_cost.append(new_cost)
    totAppl.append(new_tot)

    num_cols = len(new_cost)
    rowC = [0] * num_cols
    rowC[-1] = new_tot
    partsC.append(rowC)

    partsG.append([0] * num_cols)


def handle_death(idx, app_cost, totAppl, partsC, partsG, mu_appl):
    """
    Rimuove un'applicazione morta da tutte le strutture.
    """
    if 0 <= idx < len(app_cost):
        # elimino i vettori corrispondenti
        del app_cost[idx]
        del totAppl[idx]
        if idx < len(partsC):
            del partsC[idx]
        if idx < len(partsG):
            del partsG[idx]
        # aggiorno il conteggio delle µ-app
        if idx < mu_appl:
            mu_appl -= 1
    return mu_appl


def recompute_central_cost(app_cost, parts):
    total = 0
    for i, row in enumerate(parts):
        costs = app_cost[i]
        for j, qty in enumerate(row):
            total += qty * costs[j]
    return total

def generate_scenario(timeHorizon, base_init, p, nm):
    # Stato iniziale
    app_cost = [r.tolist() for r in base_init['app_cost']]
    totAppl  = list(base_init['totAppl'])
    mu_appl  = base_init['mu_appl']

    events   = []
    for _ in range(timeHorizon):
        # calcolo probabilità basate sullo stato attuale
        lam_appl = len(totAppl) - mu_appl
        qi = p * (1 + lam_appl + mu_appl) / (lam_appl + mu_appl) if lam_appl + mu_appl > 0 else 0
        ri = nm * p
        x1, x2 = random.random(), random.random()
        N = len(totAppl)

        if x1 < qi and N > 0:
            # morte
            idx = random.randrange(N)
            events.append(('death', idx))
            # aggiorno stato
            mu_appl = handle_death(idx, app_cost, totAppl, [], [], mu_appl)

        elif x1 < qi + p:
            # nascita
            d = generate_data()
            if x2 < 0.5:
                events.append(('birth_lambda', d))
                handle_birth_lambda(app_cost, totAppl, [], [], d)
            else:
                events.append(('birth_mu', d))
                handle_birth_mu(app_cost, totAppl, [], [], d)
                mu_appl += 1

        elif x1 < qi + p + ri and N > 0:
            # migrazione
            idx = random.randrange(N)
            d = generate_data()
            if x2 < 0.5:
                # λ -> µ
                events.append(('migration', idx, 'mu', d))
                mu_appl = handle_death(idx, app_cost, totAppl, [], [], mu_appl)
                handle_birth_mu(app_cost, totAppl, [], [], d)
                mu_appl += 1
            else:
                # µ -> λ
                events.append(('migration', idx, 'lambda', d))
                mu_appl = handle_death(idx, app_cost, totAppl, [], [], mu_appl)
                handle_birth_lambda(app_cost, totAppl, [], [], d)

        else:
            # nessun evento significativo
            events.append(('noop', None))

    # ritorno lo stato iniziale invariato più la lista di eventi dettagliati
    return deepcopy(base_init), events


def replay_scenario(init_data, events, regime, ne):
    # --- 1) Stato iniziale ---
    app_cost = [r.tolist() for r in init_data['app_cost']]
    totAppl = list(init_data['totAppl'])
    service_rate_edge = init_data['service_rate_edge']
    num_edge = init_data['num_edge']
    mu_appl = init_data['mu_appl']

    # Imposto capacità in base al regime
    containers = 5 if regime == 'scarsità' else 10
    cap_edge = [containers * r for r in service_rate_edge]

    # --- 2) Allocazioni iniziali ---
    # Centralized: prima allocazione globale
    c_cost, _, partsC = centralized_allocate(
        app_cost, totAppl, cap_edge, service_rate_edge, num_edge, mu_appl
    )
    partsC = [list(r) for r in partsC]

    # Greedy Static: un solo ricalcolo
    _, partsG_static, _ = greedy_allocate(
        app_cost, totAppl, cap_edge.copy(), service_rate_edge, num_edge, mu_appl
    )
    partsG_static = [list(r) for r in partsG_static]
    # Aggiorno capacità residua per static
    cap_static = cap_edge.copy()
    for row in partsG_static:
        for j in range(num_edge):
            cap_static[j] -= row[j]

    # Greedy Dynamic: prima allocazione identica a static
    _, partsG_dynamic, _ = greedy_allocate(
        app_cost, totAppl, cap_edge.copy(), service_rate_edge, num_edge, mu_appl
    )
    partsG_dynamic = [list(r) for r in partsG_dynamic]

    # --- 3) Inizializzo acccumuli e contatori ---
    T = len(events)
    sum_c = sum_gs = sum_gd = 0.0
    event_count = 0
    cycle_count = 0
    total_reloc_centralized = 0
    total_reloc_dynamic = 0

    # --- 4) Ciclo sugli eventi ---
    for event in events:
        ev = event[0]


        # --- 4.1) Gestione evento ---
        if ev == 'death':
            event_count += 1

            idx = event[1]
            # Centralized & Dynamic
            mu_appl = handle_death(idx, app_cost, totAppl, partsC, partsG_dynamic, mu_appl)
            # Static: rimuovo e libero capacità
            if 0 <= idx < len(partsG_static):
                row = partsG_static[idx]
                for j in range(num_edge):
                    cap_static[j] += row[j]
                del partsG_static[idx]

        elif ev == 'birth_lambda':
            event_count += 1

            d = event[1]
            # Centralized & Dynamic: aggiungo riga zero
            handle_birth_lambda(app_cost, totAppl, partsC, partsG_dynamic, d)
            q = int(d['totAppl'][-1])
            costs = d['app_cost'][-1].tolist()

            # Static: allocazione on-the-fly
            candidates = [j for j in range(num_edge) if cap_static[j] >= q]
            j_min = min(candidates, key=lambda j: costs[j]) if candidates else num_edge
            if j_min < num_edge:
                cap_static[j_min] -= q
            row_static = [0] * (num_edge + 1)
            row_static[j_min] = q
            partsG_static.append(row_static)

            # Dynamic: rimuovo zero e rialloco subito
            partsG_dynamic.pop()
            j_min_d = min(range(num_edge + 1), key=lambda j: costs[j])
            row_dyn = [0] * (num_edge + 1)
            row_dyn[j_min_d] = q
            partsG_dynamic.append(row_dyn)

        elif ev == 'birth_mu':
            event_count += 1

            d = event[1]
            handle_birth_mu(app_cost, totAppl, partsC, partsG_dynamic, d)
            mu_appl += 1
            costs = d['app_cost'][-1].tolist()

            candidates = [j for j in range(num_edge) if cap_static[j] >= 1]
            j_min = min(candidates, key=lambda j: costs[j]) if candidates else num_edge
            if j_min < num_edge:
                cap_static[j_min] -= 1
            row_static = [0] * (num_edge + 1)
            row_static[j_min] = 1
            partsG_static.append(row_static)

            partsG_dynamic.pop()
            j_min_d = min(range(num_edge + 1), key=lambda j: costs[j])
            row_dyn = [0] * (num_edge + 1)
            row_dyn[j_min_d] = 1
            partsG_dynamic.append(row_dyn)

        elif ev == 'migration':
            event_count += 1

            idx, new_type, d = event[1], event[2], event[3]
            # Rimuovo vecchia app
            mu_appl = handle_death(idx, app_cost, totAppl, partsC, partsG_dynamic, mu_appl)
            if 0 <= idx < len(partsG_static):
                row = partsG_static[idx]
                for j in range(num_edge):
                    cap_static[j] += row[j]
                del partsG_static[idx]
            # Nuova app secondo new_type
            if new_type == 'mu':
                # come birth_mu
                handle_birth_mu(app_cost, totAppl, partsC, partsG_dynamic, d)
                mu_appl += 1
                costs = d['app_cost'][-1].tolist()
                candidates = [j for j in range(num_edge) if cap_static[j] >= 1]
                j_min = min(candidates, key=lambda j: costs[j]) if candidates else num_edge
                if j_min < num_edge:
                    cap_static[j_min] -= 1
                row_static = [0] * (num_edge + 1)
                row_static[j_min] = 1
                partsG_static.append(row_static)

                partsG_dynamic.pop()
                j_min_d = min(range(num_edge + 1), key=lambda j: costs[j])
                row_dyn = [0] * (num_edge + 1)
                row_dyn[j_min_d] = 1
                partsG_dynamic.append(row_dyn)
            else:
                # come birth_lambda
                handle_birth_lambda(app_cost, totAppl, partsC, partsG_dynamic, d)
                q = int(d['totAppl'][-1])
                costs = d['app_cost'][-1].tolist()
                candidates = [j for j in range(num_edge) if cap_static[j] >= q]
                j_min = min(candidates, key=lambda j: costs[j]) if candidates else num_edge
                if j_min < num_edge:
                    cap_static[j_min] -= q
                row_static = [0] * (num_edge + 1)
                row_static[j_min] = q
                partsG_static.append(row_static)

                partsG_dynamic.pop()
                j_min_d = min(range(num_edge + 1), key=lambda j: costs[j])
                row_dyn = [0] * (num_edge + 1)
                row_dyn[j_min_d] = q
                partsG_dynamic.append(row_dyn)



        # --- 4.2) Ricalcoli globali ogni ne eventi ---


            # quando raggiungo ne eventi, si completa un ciclo:
            if event_count % ne == 0:
                cycle_count += 1

                # — ricalcolo centralizzato —
                oldC = [row.copy() for row in partsC]
                c_cost, _, partsC = centralized_allocate(
                    app_cost, totAppl, cap_edge, service_rate_edge, num_edge, mu_appl
                )
                partsC = [list(r) for r in partsC]
                total_reloc_centralized += sum(
                    1
                    for i in range(len(partsC))
                    if oldC[i] != partsC[i]
                )

                # — ricalcolo greedy dinamico —
                oldG = [row.copy() for row in partsG_dynamic]
                _, partsG_dynamic, _ = greedy_allocate(
                    app_cost, totAppl, cap_edge.copy(), service_rate_edge, num_edge, mu_appl
                )
                partsG_dynamic = [list(r) for r in partsG_dynamic]
                total_reloc_dynamic += sum(
                    1
                    for i in range(len(partsG_dynamic))
                    if oldG[i] != partsG_dynamic[i]
                )
        # --- 4.3) Accumulo costi ---
        sum_c  += recompute_central_cost(app_cost, partsC)
        sum_gs += recompute_central_cost(app_cost, partsG_static)
        sum_gd += recompute_central_cost(app_cost, partsG_dynamic)


    return (
        sum_c / T,
        sum_gs / T,
        sum_gd / T,
        total_reloc_centralized,
        total_reloc_dynamic
    )
