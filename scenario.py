# scenario.py
import random
from dataGenerator import generate_data



# Parametri fissi
p  = 0.05  # probabilità base di nascita pura
nm = 6     # numero di nodi edge (per il tasso di migrazione)

def generate_scenario(timeHorizon, base_init, p, nm):
    """
    Genera uno scenario per ogni slot fino a timeHorizon, includendo anche i no-op:
    - timeHorizon: numero di slot totali
    - base_init: stato iniziale (da generate_data)
    - p, nm: parametri di probabilità per eventi
    Restituisce (init_data, events) dove events è una lista di lunghezza timeHorizon
    e ogni tupla è ('death', idx), ('birth_lambda', d), ('birth_mu', d),
    ('migration', idx, new_type, d) o ('noop',).
    """
    # Copia dello stato per calcolare le probabilità
    app_cost = [r.tolist() for r in base_init['app_cost']]
    totAppl  = list(base_init['totAppl'])
    mu_appl  = base_init['mu_appl']

    events = []
    for _ in range(timeHorizon):
        lam_appl = len(totAppl) - mu_appl
        qi = p * (1 + lam_appl + mu_appl) / (lam_appl + mu_appl) if (lam_appl + mu_appl) > 0 else 0
        ri = nm * p
        x1, x2 = random.random(), random.random()
        N = len(totAppl)

        if x1 < qi and N > 0:
            # morte
            idx = random.randrange(N)
            events.append(('death', idx))
            # aggiorno stato clone
            del app_cost[idx]
            del totAppl[idx]
            if idx < mu_appl:
                mu_appl -= 1

        elif x1 < qi + p:
            # nascita
            d = generate_data()
            if x2 < 0.5:
                events.append(('birth_lambda', d))
            else:
                events.append(('birth_mu', d))
                mu_appl += 1
            app_cost.append(d['app_cost'][-1].tolist())
            totAppl.append(int(d['totAppl'][-1]))

        elif x1 < qi + p + ri and N > 0:
            # migrazione (death + birth)
            idx = random.randrange(N)
            new_d = generate_data()
            # decidi tipo nuovo
            prob_mu = lam_appl / (lam_appl + mu_appl) if (lam_appl + mu_appl) > 0 else 0
            new_type = 'mu' if x2 >= prob_mu else 'lambda'
            events.append(('migration', idx, new_type, new_d))
            # aggiorno clone
            del app_cost[idx]
            del totAppl[idx]
            if idx < mu_appl:
                mu_appl -= 1
            app_cost.append(new_d['app_cost'][-1].tolist())
            totAppl.append(int(new_d['totAppl'][-1]))
            if new_type == 'mu':
                mu_appl += 1

        else:
            # no-op: nessun evento in questo slot
            events.append(('noop',))

    return base_init, events
