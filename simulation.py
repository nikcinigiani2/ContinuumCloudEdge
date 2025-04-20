
import random
import numpy as np
from allocation import centralized_allocate, greedy_allocate
from dataGenerator import generate_data

# Parametri di processo
nm = 6              # numero di possibili migrazioni “peso”
p = 0.05            # tasso di nascita generale
r = nm * p          # tasso di migrazione

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
    initial_state = init_data
    app_cost = [row.tolist() for row in initial_state['app_cost']]
    totAppl = list(initial_state['totAppl'])
    capacity_per_edge = initial_state['capacity_per_edge']
    service_rate_edge = initial_state['service_rate_edge']
    num_edge = initial_state['num_edge']
    mu_appl = initial_state['mu_appl']

    lam_appl = len(totAppl) - mu_appl
    q = p * (1 + lam_appl + mu_appl) / (lam_appl + mu_appl)

    history = {
        'central_cost': [], 'greedy_cost': [],
        'num_mu': [],     'num_lambda': []
    }

    for slot in range(num_slots):
        x1 = np.random.uniform(0, q + p + r)
        x2 = np.random.random()

        if x1 < q:
            if totAppl:
                idx = random.randrange(len(totAppl))
                mu_appl = handle_death(idx, app_cost, totAppl, mu_appl)

        elif x1 < q + p:
            if x2 < 0.5:
                handle_birth_lambda(app_cost, totAppl)
            else:
                handle_birth_mu(app_cost, totAppl)

        else:
            if totAppl:
                idx = random.randrange(len(totAppl))
                was_mu = (idx < mu_appl)
                mu_appl = handle_death(idx, app_cost, totAppl, mu_appl)
                if was_mu:
                    handle_birth_lambda(app_cost, totAppl)
                else:
                    handle_birth_mu(app_cost, totAppl)

        allocG, partsG, costG = greedy_allocate(
            app_cost, totAppl,
            capacity_per_edge.copy(),
            service_rate_edge.copy(),
            num_edge, mu_appl
        )

        if slot % slots_per_epoch == 0:
            costC, allocC, partsC = centralized_allocate(
                app_cost, totAppl,
                capacity_per_edge, service_rate_edge,
                num_edge, mu_appl
            )
            _, _, costG = greedy_allocate(
                app_cost, totAppl,
                capacity_per_edge.copy(),
                service_rate_edge.copy(),
                num_edge, mu_appl
            )
        else:
            costC = history['central_cost'][-1] if history['central_cost'] else costG

        history['central_cost'].append(costC)
        history['greedy_cost'].append(costG)
        history['num_mu'].append(mu_appl)
        history['num_lambda'].append(len(totAppl) - mu_appl)

    return history
