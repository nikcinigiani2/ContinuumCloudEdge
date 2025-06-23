# scenario.py
import random
from dataGenerator import generate_data



# Parametri fissi
p  = 0.05  # probabilità base di nascita pura
nm = 6     # numero di nodi edge (per il tasso di migrazione)

def generate_scenario(timeHorizon, base_init, p, nm):
    """
    Genera uno scenario: lista di eventi (‘death’, ‘birth_lambda’, ‘birth_mu’, ‘migration’).
    Ritorna init_data (uguale a base_init) e events.
    """
    # copi localmente solo per tenere traccia dello stato e generare eventi
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
            # aggiorno solo il clone
            del app_cost[idx]
            del totAppl[idx]
            if idx < mu_appl:
                mu_appl -= 1

        elif x1 < qi + p:
            # nascita
            d = generate_data()
            if x2 < 0.5:
                events.append(('birth_lambda', d))
                app_cost.append(d['app_cost'][-1].tolist())
                totAppl.append(int(d['totAppl'][-1]))
            else:
                events.append(('birth_mu', d))
                app_cost.append(d['app_cost'][-1].tolist())
                totAppl.append(int(d['totAppl'][-1]))
                mu_appl += 1

        elif x1 < qi + p + ri and N > 0:
            # migrazione
            idx = random.randrange(N)
            d = generate_data()
            if x2 < (lam_appl / (lam_appl + mu_appl) if (lam_appl + mu_appl) > 0 else 0):
                new_type = 'lambda'
            else:
                new_type = 'mu'
                mu_appl += 1
            events.append(('migration', idx, new_type, d))
            # aggiorno clone: rimozione e aggiunta app
            del app_cost[idx]
            del totAppl[idx]
            app_cost.append(d['app_cost'][-1].tolist())
            totAppl.append(int(d['totAppl'][-1]))

        else:
            # nessun evento in questo slot
            pass

    # scenario identico per tutti gli algoritmi
    return base_init, events
