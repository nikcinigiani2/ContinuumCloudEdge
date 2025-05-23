import random
import math
import time
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt

from allocation import centralized_allocate, greedy_allocate
from dataGenerator import generate_data

# Parametri fissi
nm = 6    # numero di nodi edge (per il tasso di migrazione)
p  = 0.05 # probabilità base di nascita pura

def handle_birth_lambda(app_cost, totAppl, partsC, partsG):
    """Gestisce la nascita di una λ-app: aggiorna costi, domanda e partizioni C/G."""
    d = generate_data()
    new_cost = d['app_cost'][-1].tolist()
    app_cost.append(new_cost)
    new_tot = int(d['totAppl'][-1])
    totAppl.append(new_tot)

    num_cols = len(new_cost)
    # nuova riga in partsC: tutta sul cloud
    rowC = [0]*num_cols
    rowC[-1] = new_tot
    partsC.append(rowC)

    # nuova riga in partsG: nessuna migrazione finché non ricalcolo
    partsG.append([0]*num_cols)

def handle_birth_mu(app_cost, totAppl, partsC, partsG):
    """Gestisce la nascita di una µ-app: aggiorna costi, domanda e partizioni C/G."""
    d = generate_data()
    new_cost = d['app_cost'][0].tolist()
    app_cost.append(new_cost)
    totAppl.append(1)

    num_cols = len(new_cost)
    rowC = [0]*num_cols
    rowC[-1] = 1
    partsC.append(rowC)

    partsG.append([0]*num_cols)

def handle_death(idx, app_cost, totAppl, partsC, partsG, mu_appl):
    """Rimuove un'applicazione morta da tutte le strutture."""
    if 0 <= idx < len(app_cost):
        del app_cost[idx]
        del totAppl[idx]
        if idx < len(partsC):
            del partsC[idx]
        if idx < len(partsG):
            del partsG[idx]
        if idx < mu_appl:
            mu_appl -= 1
    return mu_appl
"""
def run_simulation_event_based(init_data, ne, regime, do_greedy=False):
    
    Esegue la simulazione evento-based.
    init_data: dict da generate_data()
    ne: numero di eventi per epoca
    regime: 'scarsità' (5 container) o 'abbondanza' (10 container)
    do_greedy: se True ricalcola matching ogni epoca, altrimenti lo mantiene fisso
    
    # --- inizializzazione stato ---
    app_cost          = [row.tolist() for row in init_data['app_cost']]
    totAppl           = list(init_data['totAppl'])
    service_rate_edge = init_data['service_rate_edge']
    num_edge          = init_data['num_edge']
    mu_appl           = init_data['mu_appl']

    lam_appl = len(totAppl) - mu_appl
    containers = 5 if regime=='scarsità' else 10
    capacity_per_edge = [containers * r for r in service_rate_edge]

    # calcolo orizzonte e epoche
    #timeHorizon  = math.ceil(5*(lam_appl + mu_appl)/p) * ne
    timeHorizon = 30000
    total_epochs = math.ceil(timeHorizon / ne)
    print(f">>> Simulazione: timeHorizon={timeHorizon}, ne={ne} ⇒ epoche={total_epochs}")
    print(f">>> regime stazionario → q={(p*(1+lam_appl+mu_appl)/(lam_appl+mu_appl)):.4f}, r={(nm*p):.4f}")

    # --- epoca 0: allocate iniziali ---
    _, _, partsC = centralized_allocate(
        app_cost, totAppl,
        capacity_per_edge, service_rate_edge,
        num_edge, mu_appl
    )
    partsC = [list(r) for r in partsC]

    _, partsG, initial_g = greedy_allocate(
        app_cost, totAppl,
        capacity_per_edge.copy(),
        service_rate_edge.copy(),
        num_edge, mu_appl
    )
    partsG = [list(r) for r in partsG]

    # --- storici ---
    history = {
        'ne':                 [],
        'births':             [],
        'deaths':             [],
        'migrations':         [],
        'num_apps':           [],
        'relocations':        [],
        'relocations_greedy': [],
        'central_cost':       [],
        'greedy_cost':        [],
    }

    tot_births = tot_deaths = tot_migrations = tot_relocations = 0
    births = deaths = migrations = 0
    event_count = epoch_num = 0

    # --- loop eventi ---
    while event_count < timeHorizon:
        x1, x2 = random.random(), random.random()
        total_apps = len(totAppl)
        lam_appl   = total_apps - mu_appl
        q = p*(1+lam_appl+mu_appl)/(lam_appl+mu_appl) if (lam_appl+mu_appl)>0 else 0
        r = nm*p

        # morte
        if x1 < q and total_apps>0:
            idx = random.randrange(total_apps)
            mu_appl = handle_death(idx, app_cost, totAppl, partsC, partsG, mu_appl)
            deaths += 1; tot_deaths += 1

        # nascita
        elif x1 < q + p:
            if x2 < 0.5:
                handle_birth_lambda(app_cost, totAppl, partsC, partsG)
            else:
                handle_birth_mu(app_cost, totAppl, partsC, partsG)
                mu_appl += 1
            births += 1; tot_births += 1

        # migrazione
        elif x1 < q + p + r and total_apps>0:
            idx = random.randrange(total_apps)
            mu_appl = handle_death(idx, app_cost, totAppl, partsC, partsG, mu_appl)
            # inverse birth
            if idx < (len(totAppl)-mu_appl):
                handle_birth_mu(app_cost, totAppl, partsC, partsG)
                mu_appl += 1
            else:
                handle_birth_lambda(app_cost, totAppl, partsC, partsG)
            migrations += 1; tot_migrations += 1

        event_count += 1

        # fine epoca
        if event_count % ne == 0:
            epoch_num += 1
            history['ne'].append(event_count)
            history['births'].append(births)
            history['deaths'].append(deaths)
            history['migrations'].append(migrations)
            history['num_apps'].append(len(totAppl))

            # centralized recalc
            t0 = time.time()
            c_cost, _, newC = centralized_allocate(
                app_cost, totAppl,
                capacity_per_edge, service_rate_edge,
                num_edge, mu_appl
            )
            newC = [list(r) for r in newC]
            relocC = sum(1 for i in range(len(newC)) if partsC[i]!=newC[i])
            tot_relocations += relocC
            history['relocations'].append(relocC)
            history['central_cost'].append(c_cost)
            partsC = newC

            # matching recalc o fermo
            oldG = [row.copy() for row in partsG]
            if do_greedy:
                _, newG, g_cost = greedy_allocate(
                    app_cost, totAppl,
                    capacity_per_edge.copy(),
                    service_rate_edge.copy(),
                    num_edge, mu_appl
                )
                newG = [list(r) for r in newG]
            else:
                newG = partsG
                g_cost = initial_g

            relocG = sum(1 for i in range(len(newG)) if oldG[i]!=newG[i])
            history['relocations_greedy'].append(relocG)
            history['greedy_cost'].append(g_cost)
            partsG = newG

            births = deaths = migrations = 0

    # totali
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
"""