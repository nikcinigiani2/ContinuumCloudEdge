import random
from allocation import centralized_allocate, greedy_allocate
from dataGenerator import generate_data

# Parametri di processo (fissi)
nm = 6
p  = 0.05
r  = nm * p

def handle_birth_lambda(app_cost, totAppl, partsC):
    d = generate_data()
    # aggiungi i nuovi costi e domanda
    app_cost.append(d['app_cost'][-1].tolist())
    totAppl.append(int(d['totAppl'][-1]))
    # crea nuova riga partsC di lunghezza corretta (edge+1)
    num_cols = len(partsC[0])
    new_row  = [0] * num_cols
    new_row[-1] = totAppl[-1]   # tutta sul cloud
    partsC.append(new_row)

def handle_birth_mu(app_cost, totAppl, partsC):
    d = generate_data()
    app_cost.append(d['app_cost'][0].tolist())
    totAppl.append(1)
    num_cols = len(partsC[0])
    new_row  = [0] * num_cols
    new_row[-1] = 1             # tutta sul cloud
    partsC.append(new_row)

def handle_death(idx, app_cost, totAppl, mu_appl, partsC):
    del app_cost[idx]
    del totAppl[idx]
    del partsC[idx]
    if idx < mu_appl:
        mu_appl -= 1
    return mu_appl

def recompute_central_cost(app_cost, partsC):
    total = 0
    for i, part in enumerate(partsC):
        cost_row = app_cost[i]
        for j, qty in enumerate(part):
            total += qty * cost_row[j]
    return total

def run_simulation(num_slots, slots_per_epoch, init_data):

    #  inizializzazione stato
    data = init_data
    app_cost          = [row.tolist() for row in data['app_cost']]
    totAppl           = list(data['totAppl'])
    capacity_per_edge = data['capacity_per_edge']
    service_rate_edge = data['service_rate_edge']
    num_edge          = data['num_edge']
    mu_appl           = data['mu_appl']
    lam_appl          = len(totAppl) - mu_appl

    # tasso di morte (q) fisso per tutta l’epoca
    q = p * (1 + lam_appl + mu_appl) / (lam_appl + mu_appl)

    # --- epoca 0: full centralized ---
    print(f"[EPOCA 0] slot=0 → full centralized allocation", flush=True)
    print(f"  nascite: μ=0 λ=0, morti: μ=0 λ=0, migrazioni=0\n", flush=True)
    current_c_cost, allocC, partsC = centralized_allocate(
        app_cost, totAppl,
        capacity_per_edge, service_rate_edge,
        num_edge, mu_appl
    )
    # partsC è una lista di liste
    partsC = [list(row) for row in partsC]

    # storico anche degli eventi per epoca
    history = {
        'central_cost':  [current_c_cost],
        'greedy_cost':   [],
        'num_mu':        [mu_appl],
        'num_lambda':    [lam_appl],
        'births_mu':     [0],
        'births_lambda': [0],
        'deaths_mu':     [0],
        'deaths_lambda': [0],
        'migrations':    [0],
    }

    # contatori per l’epoca corrente
    births_mu = births_lambda = 0
    deaths_mu = deaths_lambda = migrations = 0

    for slot in range(1, num_slots):
        # estrae evento con probabilità q, p, r, 1−(q+p+r)
        x1 = random.random()
        x2 = random.random()
        total  = mu_appl + lam_appl

        # MORTE
        if x1 < q and total > 0:
            idx = random.randrange(total)
            old_tot  = totAppl[idx]
            old_cost = app_cost[idx][num_edge]
            mu_appl = handle_death(idx, app_cost, totAppl, mu_appl, partsC)
            lam_appl = len(totAppl) - mu_appl
            # conto morti
            if idx < lam_appl:
                deaths_lambda += 1
            else:
                deaths_mu += 1

        # NASCITA
        elif x1 < q + p:
            if x2 < 0.5:
                handle_birth_lambda(app_cost, totAppl, partsC)
                lam_appl += 1
                births_lambda += 1
            else:
                handle_birth_mu(app_cost, totAppl, partsC)
                mu_appl  += 1
                births_mu += 1

        #MIGRAZIONE
        elif x1 < q + p + r and total > 0:
            migrations += 1
            idx = random.randrange(total)
            # morte
            mu_appl = handle_death(idx, app_cost, totAppl, mu_appl, partsC)
            lam_appl = len(totAppl) - mu_appl
            # nascita  (no incremento births/deaths)
            if idx < lam_appl:
                handle_birth_mu(app_cost, totAppl, partsC)
                mu_appl += 1
            else:
                handle_birth_lambda(app_cost, totAppl, partsC)
                lam_appl += 1

        #  greedy
        _, _, costG = greedy_allocate(
            app_cost, totAppl,
            capacity_per_edge.copy(),
            service_rate_edge.copy(),
            num_edge, mu_appl
        )

        # ricalcolo centralized inizio epoca
        if slot % slots_per_epoch == 0:
            ep = slot // slots_per_epoch
            print(f"[EPOCA {ep}] slot={slot} → full centralized allocation", flush=True)
            print(f"  nascite: μ={births_mu} λ={births_lambda}, "
                  f"morti: μ={deaths_mu} λ={deaths_lambda}, "
                  f"migrazioni={migrations}\n", flush=True)

            # registro contatori per questa epoca
            history['births_mu'].append(births_mu)
            history['births_lambda'].append(births_lambda)
            history['deaths_mu'].append(deaths_mu)
            history['deaths_lambda'].append(deaths_lambda)
            history['migrations'].append(migrations)

            # reset contatori
            births_mu = births_lambda = 0
            deaths_mu = deaths_lambda = migrations = 0

            # full centralized
            current_c_cost, allocC, partsC = centralized_allocate(
                app_cost, totAppl,
                capacity_per_edge, service_rate_edge,
                num_edge, mu_appl
            )
            partsC = [list(row) for row in partsC]  # di nuovo lista di liste

        #  ricalcolo ESATTO costo centralizzato da partsC
        else:
            current_c_cost = recompute_central_cost(app_cost, partsC)

        # aggiorno storico costi e numeri
        history['central_cost'].append(current_c_cost)
        history['greedy_cost'].append(costG)
        history['num_mu'].append(mu_appl)
        history['num_lambda'].append(lam_appl)

    return history
