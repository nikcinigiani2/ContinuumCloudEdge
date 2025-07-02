import string

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



def sanitize_filename(title: str) -> str:
    # Rimuove caratteri non file-friendly e sostituisce spazi con underscore
    valid = "-_.() %s%s" % (string.ascii_letters, string.digits)
    cleaned = "".join(c if c in valid else "_" for c in title)
    return cleaned.replace(" ", "_")

def save_current_fig(title: str):
    fname = sanitize_filename(title) + ".png"
    plt.savefig(fname, bbox_inches="tight")
    print(f"Salvata figura: {fname}")


def main():
    # Configurazione generale
    time_horizon = 30000         # Numero di slot della simulazione
    regimes      = ['scarsità', 'abbondanza']
    ne_vals      = list(range(10, 101, 10))
    target_ne    = 50            # Valore di ne per l'istogramma

    # Generazione dei dati base
    base_init = generate_data()

    for regime in regimes:
        # Liste per i grafici costo medio e rilocazioni
        mean_cost_c  = []
        mean_cost_cv = []
        mean_cost_ms = []
        mean_cost_md = []
        reloc_c      = []
        reloc_cv     = []
        reloc_ms     = []
        reloc_md     = []

        # Buffer per i cost_per_slot a ne = target_ne
        vectCostC_target  = None
        vectCostCV_target = None
        vectCostMS_target = None
        vectCostMD_target = None

        # Creo lo scenario (stesso per tutti i ne)
        init_data, events = generate_scenario(time_horizon, deepcopy(base_init), p, nm)

        for ne in ne_vals:
            print(f"Regime: {regime}, ne: {ne}")
            # Centralized
            c,  rc_c,  _, _, vectC  = run_centralized(init_data, events, regime, ne)
            # Mu-variante
            cv, rc_cv, _, _, vectCV = run_centralized_mu_variant(init_data, events, regime, ne)
            # Matching statico
            ms, rc_ms, _, _, vectMS = run_matchingStatic(init_data, events, regime, ne)
            # Matching dinamico
            md, rc_md, _, _, vectMD = run_matchingDynamic(init_data, events, regime, ne)

            # Raccogli medie e rilocazioni
            mean_cost_c.append(c)
            reloc_c.append(rc_c)
            mean_cost_cv.append(cv)
            reloc_cv.append(rc_cv)
            mean_cost_ms.append(ms)
            reloc_ms.append(rc_ms)
            mean_cost_md.append(md)
            reloc_md.append(rc_md)

            # Se è il target_ne, salvo i vettori cost_per_slot
            if ne == target_ne:
                if vectCostC_target is None:
                    vectCostC_target  = vectC
                    vectCostCV_target = vectCV
                    vectCostMS_target = vectMS
                    vectCostMD_target = vectMD
                else:
                    raise RuntimeError(f"Vectori già assegnati per ne={target_ne}")

        # Verifica di aver catturato i vettori target
        assert vectCostC_target is not None, f"target_ne={target_ne} non trovato"
        # Plot 1: costo medio vs ne

        title1 = (f'Costo medio per simulazione – regime {regime} - time_horizon={time_horizon}')
        plt.figure(figsize=(10, 5))
        plt.plot(ne_vals, mean_cost_c,  marker='o', label='Centralized')
        plt.plot(ne_vals, mean_cost_cv, marker='o', label='Mu-Variante')
        plt.plot(ne_vals, mean_cost_ms, marker='o', label='Matching statico')
        plt.plot(ne_vals, mean_cost_md, marker='o', label='Matching dinamico')
        plt.xlabel('ne ')
        plt.ylabel('Costo medio ')
        plt.title(title1)
        plt.legend()
        plt.grid(True)
        save_current_fig(title1)

        # Plot 2: rilocazioni vs ne
        title2 = (f'Numero di rilocazioni per simulazione – regime {regime} ')
        plt.figure(figsize=(10, 5))
        plt.plot(ne_vals, reloc_c,  marker='o', label='Centralized')
        plt.plot(ne_vals, reloc_cv, marker='o', label='Mu-Variante')
        plt.plot(ne_vals, reloc_ms, marker='o', label='Matching statico')
        plt.plot(ne_vals, reloc_md, marker='o', label='Matching dinamico')
        plt.xlabel('ne ')
        plt.ylabel('Numero di rilocazioni')
        plt.title(title2)
        plt.legend()
        plt.grid(True)
        save_current_fig(title2)

        # Plot 3: istogramma costi per slot per ne = target_ne Centralized

        title3 = (f'Distribuzione costi Centralized per slot (ne={target_ne}) – regime {regime}')
        plt.figure(figsize=(10, 5))
        plt.hist(vectCostC_target,  bins=50, alpha=0.5, label='Centralized')
        plt.hist(vectCostCV_target, bins=50, alpha=0.5, label='Mu-Variante')
        plt.xlabel('Costo per slot')
        plt.ylabel('Frequenza (numero di occorrenze)')
        plt.title(title3)
        plt.legend()
        plt.grid(True)
        save_current_fig(title3)

        # Plot 4: istogramma costi per slot per ne = target_ne Matching

        title4 = (f'Distribuzione costi Matching per slot (ne={target_ne}) – regime {regime}')
        plt.figure(figsize=(10, 5))
        plt.hist(vectCostMS_target, bins=50, alpha=0.5, label='Matching statico')
        plt.hist(vectCostMD_target, bins=50, alpha=0.5, label='Matching dinamico')
        plt.xlabel('Costo per slot')
        plt.ylabel('Frequenza (numero di occorrenze)')
        plt.title(title4)
        plt.legend()
        plt.grid(True)
        save_current_fig(title4)

    plt.show()

if __name__ == '__main__':
    main()
