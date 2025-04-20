# simulation.py

import random
import numpy as np
from allocation import centralized_allocate, greedy_allocate
from dataGenerator import generate_data

# Parametri di processo (fissi)
nm = 6
p  = 0.05
r  = nm * p

def handle_birth_lambda(app_cost, totAppl):
    d = generate_data()
    app_cost.append(d['app_cost'][-1].tolist())
    totAppl.append(int(d['totAppl'][-1]))

def handle_birth_mu(app_cost, totAppl):
    d = generate_data()
    app_cost.append(d['app_cost'][0].tolist())
    totAppl.append(1)

def handle_death(idx, app_cost, totAppl, mu_appl):
    del app_cost[idx]
    del totAppl[idx]
    if idx < mu_appl:
        mu_appl -= 1
    return mu_appl

def run_simulation(num_slots, slots_per_epoch, init_data):
    """
    num_slots: numero totale di slot temporali
    slots_per_epoch: lunghezza di un’epoca (in slot)
    init_data: dict da generate_data()
    """
    # Stato iniziale
    state = init_data
    app_cost           = [row.tolist() for row in state['app_cost']]
    totAppl            = list(state['totAppl'])
    capacity_per_edge  = state['capacity_per_edge']
    service_rate_edge  = state['service_rate_edge']
    num_edge           = state['num_edge']
    mu_appl            = state['mu_appl']
    lam_appl           = len(totAppl) - mu_appl

    # q fisso da inizio epoca
    q = p * (1 + lam_appl + mu_appl) / (lam_appl + mu_appl)

    # primo calcolo centralized
    current_c_cost, allocC, partsC = centralized_allocate(
        app_cost, totAppl,
        capacity_per_edge, service_rate_edge,
        num_edge, mu_appl
    )

    history = {
        'central_cost': [current_c_cost],
        'greedy_cost':  [],
        'num_mu':      [mu_appl],
        'num_lambda':  [lam_appl]
    }

    for slot in range(1, num_slots):
        # Evento casuale
        x1 = np.random.uniform(0, q + p + r)
        x2 = np.random.random()

        # Prepara variabili per delta centralized
        deltaC = 0

        # --- inizio blocco evento aggiornato ---
        total = lam_appl + mu_appl

        if x1 < q:
            # MORTE
            if total > 0:
                idx = random.randrange(total)
                old_tot  = totAppl[idx]
                old_cost = app_cost[idx][num_edge]
                mu_appl  = handle_death(idx, app_cost, totAppl, mu_appl)
                lam_appl = len(totAppl) - mu_appl
                deltaC  -= old_tot * old_cost

        elif x1 < q + p:
            # NASCITA
            if x2 < 0.5:
                handle_birth_lambda(app_cost, totAppl)
                lam_appl += 1
            else:
                handle_birth_mu(app_cost, totAppl)
                mu_appl  += 1

            new_idx  = len(totAppl) - 1
            new_tot  = totAppl[new_idx]
            new_cost = app_cost[new_idx][num_edge]
            deltaC  += new_tot * new_cost

        else:
            # MIGRAZIONE = MORTE + NASCITA
            if total > 0:
                idx     = random.randrange(total)
                was_mu  = (idx < mu_appl)

                # rimozione
                old_tot  = totAppl[idx]
                old_cost = app_cost[idx][num_edge]
                mu_appl  = handle_death(idx, app_cost, totAppl, mu_appl)
                lam_appl = len(totAppl) - mu_appl
                deltaC  -= old_tot * old_cost

                # nuova nascita inversa
                if was_mu:
                    handle_birth_lambda(app_cost, totAppl)
                    lam_appl += 1
                else:
                    handle_birth_mu(app_cost, totAppl)
                    mu_appl  += 1

                new_idx  = len(totAppl) - 1
                new_tot  = totAppl[new_idx]
                new_cost = app_cost[new_idx][num_edge]
                deltaC  += new_tot * new_cost
        # --- fine blocco evento aggiornato ---

        # Allocazione greedy immediata
        allocG, partsG, costG = greedy_allocate(
            app_cost, totAppl,
            capacity_per_edge.copy(),
            service_rate_edge.copy(),
            num_edge, mu_appl
        )

        # Ricalcolo centralized a inizio epoca
        if slot % slots_per_epoch == 0:
            current_c_cost, allocC, partsC = centralized_allocate(
                app_cost, totAppl,
                capacity_per_edge, service_rate_edge,
                num_edge, mu_appl
            )
            lam_appl = len(totAppl) - mu_appl  # aggiorna anche lam_appl
        else:
            current_c_cost += deltaC

        # Registra storico
        history['central_cost'].append(current_c_cost)
        history['greedy_cost'].append(costG)
        history['num_mu'].append(mu_appl)
        history['num_lambda'].append(lam_appl)

    return history
