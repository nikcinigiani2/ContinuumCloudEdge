import pickle
import math
import argparse
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from copy import deepcopy

from dataGenerator import generate_data
from scenario import generate_scenario, p, nm
from centralizedScenario import run_centralized
from centralizedScenario_muVariant import run_centralized_mu_variant
from matchingStaticoScenario import run_matchingStatic
from matchingDinamicoScenario import run_matchingDynamic


"""
Uso:
  python main.py --save-pkl ScenariPickle/<nome_scenario>.pkl   # Genera uno scenario e lo salva in un file pickle nella cartella ScenariPickle, poi esci
  python main.py --use-pkl ScenariPickle/<nome_scenario>.pkl    # Carica uno scenario esistente da file pickle e avvia le simulazioni
  python main.py                                              # Genera un nuovo scenario al volo ed esegue le simulazioni

 """

def save_scenario_pkl(time_horizon, base_init, filename):
    """
    Genera uno scenario e lo salva in formato pickle.
    """
    init_data, events = generate_scenario(time_horizon, deepcopy(base_init), p, nm)
    with open(filename, 'wb') as f:
        pickle.dump((init_data, events), f)
    print(f"Scenario salvato in pickle: {filename}")


def load_scenario_pkl(filename):
    """
    Carica uno scenario da file pickle e restituisce init_data, events.
    """
    with open(filename, 'rb') as f:
        init_data, events = pickle.load(f)
    return init_data, events


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--save-pkl', type=str,
                        help='Salva scenario in pickle e termina')
    parser.add_argument('--use-pkl', type=str,
                        help='Carica scenario da file pickle')
    args = parser.parse_args()

    # Prepara base_init e time_horizon
    base_init = generate_data()
    lam = len(base_init['totAppl']) - base_init['mu_appl']
    mu  = base_init['mu_appl']
    ec  = 10
    time_horizon = math.ceil((5 * (lam + mu) / p)) * ec

    # Salvataggio scenario su pickle
    if args.save_pkl:
        save_scenario_pkl(time_horizon, base_init, args.save_pkl)
        return

    # Caricamento scenario da pickle o generazione on-the-fly
    if args.use_pkl:
        init_data, events = load_scenario_pkl(args.use_pkl)
    else:
        init_data, events = generate_scenario(time_horizon, base_init, p, nm)

    regimes  = ['scarsità', 'abbondanza']
    ne_vals  = list(range(10, 101, 10))
    target_ne = 20

    for regime in regimes:
        mean_cost_c  = []
        mean_cost_cv = []
        mean_cost_ms = []
        mean_cost_md = []
        reloc_c      = []
        reloc_cv     = []
        reloc_ms     = []
        reloc_md     = []
        vectC = vectCV = vectMS = vectMD = None

        for ne in ne_vals:
            # Esegui simulazioni
            print(f"Regime: {regime}, ne: {ne}")
            sd_i, sd_e = deepcopy(init_data), deepcopy(events)
            c, rc_c, *_ , vC = run_centralized(sd_i, sd_e, regime, ne)
            sv_i, sv_e = deepcopy(init_data), deepcopy(events)
            cv, rc_cv, *_, vCV = run_centralized_mu_variant(sv_i, sv_e, regime, ne)
            ss_i, ss_e = deepcopy(init_data), deepcopy(events)
            ms, rc_ms, *_, vMS = run_matchingStatic(ss_i, ss_e, regime, ne)
            sd2_i, sd2_e = deepcopy(init_data), deepcopy(events)
            md, rc_md, *_, vMD = run_matchingDynamic(sd2_i, sd2_e, regime, ne)

            # Raccogli medie e rilocazioni
            mean_cost_c.append(c);  reloc_c.append(rc_c)
            mean_cost_cv.append(cv); reloc_cv.append(rc_cv)
            mean_cost_ms.append(ms); reloc_ms.append(rc_ms)
            mean_cost_md.append(md); reloc_md.append(rc_md)

            # Salva vettori cost_per_slot per target_ne
            if ne == target_ne and vectC is None:
                vectC  = vC
                vectCV = vCV
                vectMS = vMS
                vectMD = vMD

        assert vectC is not None, f"target_ne={target_ne} non trovato"

        # Plot 1: costo medio vs ne
        plt.figure(figsize=(10, 5))
        plt.plot(ne_vals, mean_cost_c,  marker='o', label='Centralized')
        plt.plot(ne_vals, mean_cost_cv, marker='o', label='Mu-Variante')
        plt.plot(ne_vals, mean_cost_ms, marker='o', label='Matching statico')
        plt.plot(ne_vals, mean_cost_md, marker='o', label='Matching dinamico')
        plt.xlabel('ne')
        plt.ylabel('Costo medio')
        plt.title(f'Costo medio per simulazione – regime {regime} - time_horizon={time_horizon}')
        plt.legend(); plt.grid(True)

        # Plot 2: rilocazioni vs ne
        plt.figure(figsize=(10, 5))
        plt.plot(ne_vals, reloc_c,  marker='o', label='Centralized')
        plt.plot(ne_vals, reloc_cv, marker='o', label='Mu-Variante')
        plt.plot(ne_vals, reloc_ms, marker='o', label='Matching statico')
        plt.plot(ne_vals, reloc_md, marker='o', label='Matching dinamico')
        plt.xlabel('ne')
        plt.ylabel('Numero di rilocazioni')
        plt.title(f'Numero di rilocazioni vs ne – regime {regime}')
        plt.legend(); plt.grid(True)

        # Plot 3: istogramma costi Centralized & Mu-Variante
        plt.figure(figsize=(10, 5))
        plt.hist(vectC,  bins=50, alpha=0.5, label='Centralized')
        plt.hist(vectCV, bins=50, alpha=0.5, label='Mu-Variante')
        plt.xlabel('Costo per slot')
        plt.ylabel('Frequenza (numero di occorrenze)')
        plt.title(f'Distribuzione costi Centralized (ne={target_ne}) – regime {regime}')
        plt.legend(); plt.grid(True)

        # Plot 4: istogramma costi Matching statico & dinamico
        plt.figure(figsize=(10, 5))
        plt.hist(vectMS, bins=50, alpha=0.5, label='Matching statico')
        plt.hist(vectMD, bins=50, alpha=0.5, label='Matching dinamico')
        plt.xlabel('Costo per slot')
        plt.ylabel('Frequenza (numero di occorrenze)')
        plt.title(f'Distribuzione costi Matching (ne={target_ne}) – regime {regime}')
        plt.legend(); plt.grid(True)

    plt.show()

if __name__ == '__main__':
    main()
