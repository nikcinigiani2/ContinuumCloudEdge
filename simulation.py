import random
import math
import time

from allocation import centralized_allocate, greedy_allocate
from dataGenerator import generate_data

# Parametri fissi
nm = 6    # numero di nodi edge (usato per le migrazioni)
p  = 0.05 # probabilità base di nascita pura

def handle_birth_lambda(app_cost, totAppl, partsC):
    d = generate_data()
    new_cost = d['app_cost'][-1].tolist()
    app_cost.append(new_cost)
    new_tot = int(d['totAppl'][-1])
    totAppl.append(new_tot)
    num_cols = len(new_cost)
    row = [0]*num_cols
    row[-1] = new_tot
    partsC.append(row)

def handle_birth_mu(app_cost, totAppl, partsC):
    d = generate_data()
    new_cost = d['app_cost'][0].tolist()
    app_cost.append(new_cost)
    totAppl.append(1)
    num_cols = len(new_cost)
    row = [0]*num_cols
    row[-1] = 1
    partsC.append(row)

def handle_death(idx, app_cost, totAppl, mu_appl, partsC):
    if 0 <= idx < len(app_cost):
        del app_cost[idx]
        del totAppl[idx]
        if idx < len(partsC):
            del partsC[idx]
        if idx < mu_appl:
            mu_appl -= 1
    return mu_appl

def run_simulation_event_based(init_data, ne, regime, do_greedy=False):
    """
    init_data: dict da generate_data()
    ne: numero di eventi che formano un'epoca
    regime: 'scarsità' o 'abbondanza' (5 vs. 10 container per edge)
    do_greedy: se True, matching viene ricalcolato ogni epoca; altrimenti resta al valore iniziale
    """
    # ---- inizializzazione ----
    app_cost          = [r.tolist() for r in init_data['app_cost']]
    totAppl           = list(init_data['totAppl'])
    service_rate_edge = init_data['service_rate_edge']
    num_edge          = init_data['num_edge']
    mu_appl           = init_data['mu_appl']
    lam_appl          = len(totAppl) - mu_appl

    # capacità per edge in base al regime
    containers = 5 if regime=='scarsità' else 10
    capacity_per_edge = [containers * r for r in service_rate_edge]

    # orizzonte di eventi e numero epoche
    timeHorizon  = math.ceil(2*(lam_appl + mu_appl) / p) * ne
    total_epochs = math.ceil(timeHorizon / ne)
    print(f">>> Simulazione: timeHorizon={timeHorizon}, ne={ne} ⇒ epoche={total_epochs}")

    # epoca 0: calcolo partsC iniziale con centralized
    _, _, partsC = centralized_allocate(
        app_cost, totAppl,
        capacity_per_edge, service_rate_edge,
        num_edge, mu_appl
    )
    partsC = [list(r) for r in partsC]

    # calcolo greedy iniziale (sempre, anche se do_greedy=False)
    _, _, initial_g = greedy_allocate(
        app_cost, totAppl,
        capacity_per_edge.copy(),
        service_rate_edge.copy(),
        num_edge, mu_appl
    )

    # serie storiche
    history = {'ne': [], 'relocations': [], 'births': [], 'deaths': [], 'migrations': [], 'central_cost': [],
               'greedy_cost': [], 'num_apps': []}

    # contatori globali
    tot_births = tot_deaths = tot_migrations = tot_relocations = 0
    # contatori epoca
    births = deaths = migrations = 0
    event_count = epoch_num = 0

    # ---- loop sugli eventi ----
    while event_count < timeHorizon:
        x1, x2 = random.random(), random.random()
        total_apps = len(totAppl)
        lam_appl   = total_apps - mu_appl
        # tasso di morte Q
        q = p*(1+lam_appl+mu_appl)/(lam_appl+mu_appl) if (lam_appl+mu_appl)>0 else 0

        # --- MORTE ---
        if x1 < q and total_apps>0:
            idx     = random.randrange(total_apps)
            mu_appl = handle_death(idx, app_cost, totAppl, mu_appl, partsC)
            deaths += 1; tot_deaths += 1
        # --- NASCITA ---
        elif x1 < q + p:
            if x2 < 0.5:
                handle_birth_lambda(app_cost, totAppl, partsC)
            else:
                handle_birth_mu(app_cost, totAppl, partsC)
                mu_appl += 1
            births += 1; tot_births += 1
        # --- MIGRAZIONE ---
        elif x1 < q + p + (nm*p) and total_apps>0:
            idx     = random.randrange(total_apps)
            mu_appl = handle_death(idx, app_cost, totAppl, mu_appl, partsC)
            # “inverse birth”
            if idx < (len(totAppl)-mu_appl):
                handle_birth_mu(app_cost, totAppl, partsC)
                mu_appl += 1
            else:
                handle_birth_lambda(app_cost, totAppl, partsC)
            migrations += 1; tot_migrations += 1

        event_count += 1

        # ---- fine epoca su ne eventi ----
        if event_count % ne == 0:
            epoch_num += 1
            # registro contatori epoca
            history['ne'].append(event_count)
            history['births'].append(births)
            history['deaths'].append(deaths)
            history['migrations'].append(migrations)
            history['num_apps'].append(len(totAppl))

            # --- centralized recalculation ---
            t0 = time.time()
            c_cost, _, new_parts = centralized_allocate(
                app_cost, totAppl,
                capacity_per_edge, service_rate_edge,
                num_edge, mu_appl
            )
            # conto riallocazioni
            new_parts = [list(r) for r in new_parts]
            reloc = sum(1 for i in range(len(new_parts))
                        if partsC[i] != new_parts[i])
            tot_relocations += reloc

            history['relocations'].append(reloc)
            history['central_cost'].append(c_cost)
            partsC = new_parts

            # --- greedy recalculation o “fermo” iniziale ---
            if do_greedy:
                _, _, g_cost = greedy_allocate(
                    app_cost, totAppl,
                    capacity_per_edge.copy(),
                    service_rate_edge.copy(),
                    num_edge, mu_appl
                )
            else:
                g_cost = initial_g
            history['greedy_cost'].append(g_cost)

            # reset contatori epoca
            births = deaths = migrations = 0

    # alla fine aggiungo i totali
    history['total_births']      = tot_births
    history['total_deaths']      = tot_deaths
    history['total_migrations']  = tot_migrations
    history['total_relocations'] = tot_relocations

    return history
