import random
import math
import time
import copy

from allocation import centralized_allocate, greedy_allocate
from dataGenerator import generate_data

# Parametri fissi
nm = 6    # numero di nodi edge
p  = 0.05 # probabilità base

def handle_birth_lambda(app_cost, totAppl, partsC):
    d = generate_data()
    new_cost = d['app_cost'][-1].tolist()
    app_cost.append(new_cost)
    new_tot = int(d['totAppl'][-1])
    totAppl.append(new_tot)
    num_cols = len(new_cost)
    new_row  = [0] * num_cols
    new_row[-1] = new_tot
    partsC.append(new_row)

def handle_birth_mu(app_cost, totAppl, partsC):
    d = generate_data()
    new_cost = d['app_cost'][0].tolist()
    app_cost.append(new_cost)
    totAppl.append(1)
    num_cols = len(new_cost)
    new_row  = [0] * num_cols
    new_row[-1] = 1
    partsC.append(new_row)

def handle_death(idx, app_cost, totAppl, mu_appl, partsC):
    total = len(app_cost)
    if 0 <= idx < total:
        del app_cost[idx]
        del totAppl[idx]
        if 0 <= idx < len(partsC):
            del partsC[idx]
        if idx < mu_appl:
            mu_appl -= 1
    return mu_appl

def run_simulation_event_based(init_data, ne, regime, do_greedy=False):
    """
    init_data: dict da generate_data()
    ne: numero di eventi per epoca
    regime: 'scarcity' o 'abundance'
    do_greedy: se True aggiorna greedy ogni epoca
    """
    # --- Inizializzazione stato base ---
    app_cost          = [row.tolist() for row in init_data['app_cost']]
    totAppl           = list(init_data['totAppl'])
    service_rate_edge = init_data['service_rate_edge']
    num_edge          = init_data['num_edge']
    mu_appl           = init_data['mu_appl']

    # capacity per regime
    containers = 5 if regime == 'scarcity' else 10
    capacity_per_edge = [containers * r for r in service_rate_edge]

    # calcolo timeHorizon e total_epochs
    lam_appl     = len(totAppl) - mu_appl
    timeHorizon  = math.ceil(2*(lam_appl + mu_appl) / p) * ne
    total_epochs = math.ceil(timeHorizon / ne)
    print(f">>> Simulazione: timeHorizon={timeHorizon} eventi, ne={ne} ⇒ total_epochs={total_epochs}")

    # Epoca 0 (full centralized) — inizializziamo partsC
    _, _, partsC = centralized_allocate(
        app_cost, totAppl,
        capacity_per_edge, service_rate_edge,
        num_edge, mu_appl
    )
    partsC = [list(r) for r in partsC]

    # --- Serie storiche per ciascuna epoca ---
    history = {
        'ne':             [],   # eventi cumulati
        'alloc_events':   [],   # numero di allocazioni (nascite/dea/migraz)
        'births':         [],
        'deaths':         [],
        'migrations':     [],
        'relocations':    [],
        'central_cost':   [],
        'greedy_cost':    [],
        # in fondo aggiungeremo i totali
    }

    # --- Contatori GLOBALI (su tutta la simulazione) ---
    tot_births      = 0
    tot_deaths      = 0
    tot_migrations  = 0
    tot_relocations = 0

    # --- Contatori per epoca ---
    alloc_events = births = deaths = migrations = 0
    event_count  = 0
    epoch_num    = 0

    # --- Loop sugli eventi ---
    while event_count < timeHorizon:
        x1, x2      = random.random(), random.random()
        lam_appl    = len(totAppl) - mu_appl
        total_apps  = len(totAppl)
        q = (p * (1 + lam_appl + mu_appl) /
             (lam_appl + mu_appl)) if (lam_appl + mu_appl) > 0 else 0

        # ------ MORTE pura ------
        if x1 < q and total_apps > 0:
            idx      = random.randrange(total_apps)
            mu_appl  = handle_death(idx, app_cost, totAppl, mu_appl, partsC)
            deaths  += 1
            tot_deaths += 1         # <<<<<<<<<< Aggiorno il contatore globale
            alloc_events += 1
        # ------ NASCITA pura ------
        elif x1 < q + p:
            if x2 < 0.5:
                handle_birth_lambda(app_cost, totAppl, partsC)
            else:
                handle_birth_mu(app_cost, totAppl, partsC)
                mu_appl += 1
            births += 1
            tot_births += 1         # <<<<<<<<<< Aggiorno il contatore globale
            alloc_events += 1
        # ------ MIGRAZIONE ------
        elif x1 < q + p + (nm * p) and total_apps > 0:
            idx = random.randrange(total_apps)
            mu_appl = handle_death(idx, app_cost, totAppl, mu_appl, partsC)
            # revive inverso
            if idx < (len(totAppl) - mu_appl):
                handle_birth_mu(app_cost, totAppl, partsC)
                mu_appl += 1
            else:
                handle_birth_lambda(app_cost, totAppl, partsC)
            migrations += 1
            tot_migrations += 1     # <<<<<<<<<< Aggiorno il contatore globale
            alloc_events += 1

        event_count += 1

        # ------ Epoca basata su ne eventi ------
        if event_count % ne == 0:
            epoch_num += 1
            pct = epoch_num / total_epochs * 100
            print(f"[Epoch {epoch_num}/{total_epochs} – {pct:.1f}%] "
                  f"events={event_count}/{timeHorizon} mu={mu_appl} apps={len(app_cost)}")

            # Registro le serie storiche
            history['ne'].append(event_count)
            history['alloc_events'].append(alloc_events)
            history['births'].append(births)
            history['deaths'].append(deaths)
            history['migrations'].append(migrations)

            # Reset contatori epoca
            births = deaths = migrations = 0

            # ------ Ricalcolo CENTRALIZED ------
            print(f"[Epoch {epoch_num}] → Inizio centralized_allocate")
            t0 = time.time()
            c_cost, _, new_parts = centralized_allocate(
                app_cost, totAppl,
                capacity_per_edge, service_rate_edge,
                num_edge, mu_appl
            )
            dt = time.time() - t0
            print(f"[Epoch {epoch_num}] ← Fine centralized in {dt:.2f}s; costo={c_cost}")

            # Conta quante allocazioni sono cambiate
            new_parts = [list(r) for r in new_parts]
            reloc = sum(1
                        for i in range(len(new_parts))
                        if partsC[i] != new_parts[i])
            history['relocations'].append(reloc)
            tot_relocations += reloc   # <<<<<<<<<< Aggiorno il contatore globale

            history['central_cost'].append(c_cost)
            partsC = new_parts

            # ------ Ricalcolo GREEDY (opzionale) ------
            if do_greedy:
                _, _, g_cost = greedy_allocate(
                    app_cost, totAppl,
                    capacity_per_edge.copy(),
                    service_rate_edge.copy(),
                    num_edge, mu_appl
                )
                history['greedy_cost'].append(g_cost)

    # ------ Alla fine, aggiungo i totali al history e restituisco ------
    history['total_births']      = tot_births
    history['total_deaths']      = tot_deaths
    history['total_migrations']  = tot_migrations
    history['total_relocations'] = tot_relocations

    return history

