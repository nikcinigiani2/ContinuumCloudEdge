import random
import math
import time
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt

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
    Esecuzione della simulazione basata su eventi con flussi bilanciati in regime stazionario.

    init_data: dict restituito da generate_data()
    ne: numero di eventi che formano un'epoca
    regime: 'scarsità' o 'abbondanza' (5 vs. 10 container per edge)
    do_greedy: se True, il matching greedy viene ricalcolato ogni epoca; altrimenti usa il valore iniziale
    """
    import random, math, time
    from allocation import centralized_allocate, greedy_allocate
    # Funzioni di utilità per nascita/morte
    from simulation import handle_birth_lambda, handle_birth_mu, handle_death

    # ---- inizializzazione ----
    app_cost          = [r.tolist() for r in init_data['app_cost']]
    totAppl           = list(init_data['totAppl'])
    service_rate_edge = init_data['service_rate_edge']
    num_edge          = init_data['num_edge']
    mu_appl           = init_data['mu_appl']
    lam_appl          = len(totAppl) - mu_appl

    # capacità per edge in base al regime
    containers = 5 if regime == 'scarsità' else 10
    capacity_per_edge = [containers * r for r in service_rate_edge]

    # orizzonte di eventi e numero di epoche
    timeHorizon  = math.ceil(5 * (lam_appl + mu_appl) / p) * ne
    total_epochs = math.ceil(timeHorizon / ne)
    print(f">>> Simulazione: timeHorizon={timeHorizon}, ne={ne} ⇒ epoche={total_epochs}")

    # ─── Calcolo tassi stazionari ───
    q_const = p * (1 + lam_appl + mu_appl) / (lam_appl + mu_appl)
    r_const = nm * p
    print(f">>> regime stazionario → q={q_const:.4f}, r={r_const:.4f}")

    # epoca 0: allocazione centralizzata iniziale
    _, _, partsC = centralized_allocate(
        app_cost, totAppl,
        capacity_per_edge, service_rate_edge,
        num_edge, mu_appl
    )
    partsC = [list(r) for r in partsC]

    # calcolo greedy iniziale (valore di riferimento)
    _, _, initial_g = greedy_allocate(
        app_cost, totAppl,
        capacity_per_edge.copy(),
        service_rate_edge.copy(),
        num_edge, mu_appl
    )

    # serie storiche
    history = {
        'ne': [],
        'relocations': [],
        'births': [],
        'deaths': [],
        'migrations': [],
        'central_cost': [],
        'greedy_cost': [],
        'num_apps': []
    }

    # contatori globali ed epoca
    tot_births = tot_deaths = tot_migrations = tot_relocations = 0
    births = deaths = migrations = 0
    event_count = epoch_num = 0

    # ---- loop sugli eventi ----
    while event_count < timeHorizon:
        x1, x2 = random.random(), random.random()
        total_apps = len(totAppl)
        lam_appl   = total_apps - mu_appl

        # --- MORTE (tasso stazionario) ---
        if x1 < q_const and total_apps > 0:
            idx     = random.randrange(total_apps)
            mu_appl = handle_death(idx, app_cost, totAppl, mu_appl, partsC)
            deaths += 1
            tot_deaths += 1

        # --- NASCITA ---
        elif x1 < q_const + p:
            if x2 < 0.5:
                handle_birth_lambda(app_cost, totAppl, partsC)
            else:
                handle_birth_mu(app_cost, totAppl, partsC)
                mu_appl += 1
            births += 1
            tot_births += 1

        # --- MIGRAZIONE (tasso stazionario) ---
        elif x1 < q_const + p + r_const and total_apps > 0:
            idx     = random.randrange(total_apps)
            mu_appl = handle_death(idx, app_cost, totAppl, mu_appl, partsC)
            # "inverse birth" per migrazione
            if idx < (len(totAppl) - mu_appl):
                handle_birth_mu(app_cost, totAppl, partsC)
                mu_appl += 1
            else:
                handle_birth_lambda(app_cost, totAppl, partsC)
            migrations += 1
            tot_migrations += 1

        event_count += 1

        # ---- aggiorna fine epoca ----
        if event_count % ne == 0:
            epoch_num += 1
            history['ne'].append(event_count)
            history['births'].append(births)
            history['deaths'].append(deaths)
            history['migrations'].append(migrations)
            history['num_apps'].append(len(totAppl))

            # riallocazione centralizzata
            t0 = time.time()
            c_cost, _, new_parts = centralized_allocate(
                app_cost, totAppl,
                capacity_per_edge, service_rate_edge,
                num_edge, mu_appl
            )
            new_parts = [list(r) for r in new_parts]
            reloc = sum(1 for i in range(len(new_parts)) if partsC[i] != new_parts[i])
            tot_relocations += reloc

            history['relocations'].append(reloc)
            history['central_cost'].append(c_cost)
            partsC = new_parts

            # ricalcolo greedy o uso iniziale
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

    # totali complessivi
    history['total_births']      = tot_births
    history['total_deaths']      = tot_deaths
    history['total_migrations']  = tot_migrations
    history['total_relocations'] = tot_relocations

    return history
if __name__ == "__main__":
    import matplotlib.pyplot as plt
    from dataGenerator import generate_data
    from simulation import run_simulation_event_based

    # --- parametri CLI-like ---
    ne        = 10            # eventi per epoca (corrisponde a un punto ogni 3000 eventi)
    regime    = 'abbondanza'    # 'scar­sità' o 'abbondanza'
    do_greedy = False           # se True ricalcola greedy ogni epoca

    # --- genera stato iniziale e lancia simulazione ---
    init_data = generate_data()
    history   = run_simulation_event_based(init_data, ne, regime, do_greedy)

    # --- calcola e stampa la media delle app attive ---
    apps       = history['num_apps']                 # vettore lunghezza #epoche
    avg_apps   = sum(apps) / len(apps)
    print(f"\nMedia applicazioni attive su tutto l'orizzonte: {avg_apps:.2f}\n")

    # --- (opzionale) ridisegna il grafico con la media orizzontale ---
    epochs = [i*ne for i in range(1, len(apps)+1)]
    plt.figure(figsize=(10,6))
    plt.plot(epochs, apps, marker='o', markersize=4, linestyle='-',
             label='# app attive per epoca')
    plt.axhline(avg_apps, linestyle='--', label=f"Media = {avg_apps:.2f}")
    plt.xlabel("Eventi cumulati")
    plt.ylabel("App attive")
    plt.title(f"App attive vs eventi (1 punto ogni {ne} ev.)\nMedia complessiva = {avg_apps:.2f}")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()
