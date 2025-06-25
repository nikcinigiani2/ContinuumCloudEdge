import math
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt

from dataGenerator import generate_data
from scenario import generate_scenario, p, nm
from centralizedScenario import run_centralized
from centralizedScenario_muVariant import run_centralized_mu_variant
from matchingStaticoScenario import run_matchingStatic
from matchingDinamicoScenario import run_matchingDynamic
from copy import deepcopy


def main():
    # Definizioni dei regimi e dei valori di ne
    regimes   = ['scarsità', 'abbondanza']
    ne_values = list(range(10, 101, 10))

    # Genera lo stato iniziale
    base_init = generate_data()
    lam = len(base_init['totAppl']) - base_init['mu_appl']
    mu  = base_init['mu_appl']

    # Calcolo del timeHorizon
    ec = 1
   # timeHorizon = math.ceil((5 * (lam + mu) / p)) * ec
    timeHorizon = 1000  # Impostazione fissa per il timeHorizon

    # Generazione dello scenario con no-op inclusi
    init_data, events = generate_scenario(timeHorizon, base_init, p, nm)

    # Loop sui regimi
    for regime in regimes:
        # Liste per raccogliere risultati principali
        costsC, costsCV, costsS, costsD = [], [], [], []
        relC,    relCV,    relS,    relD    = [], [], [], []

        # Loop sui periodi di ricalcolo ne
        for ne in ne_values:
            # Centralized standard
            sd_init, sd_events = deepcopy(init_data), deepcopy(events)
            mc, relC_i, effC, cycC, _ = run_centralized(sd_init, sd_events, regime, ne)
            costsC.append(mc)
            relC.append(relC_i)

            # Centralized Mu-Variante
            smv_init, smv_events = deepcopy(init_data), deepcopy(events)
            mcv, relCV_i, effCV, cycCV, _ = run_centralized_mu_variant(smv_init, smv_events, regime, ne)
            costsCV.append(mcv)
            relCV.append(relCV_i)

            # Matching Statico
            ss_init, ss_events = deepcopy(init_data), deepcopy(events)
            ms, relS_i, effS, cycS, _ = run_matchingStatic(ss_init, ss_events, regime, ne)
            costsS.append(ms)
            relS.append(relS_i)

            # Matching Dinamico
            sd2_init, sd2_events = deepcopy(init_data), deepcopy(events)
            md, relD_i, effD, cycD, _ = run_matchingDynamic(sd2_init, sd2_events, regime, ne)
            costsD.append(md)
            relD.append(relD_i)

        # Plot dei costi medi
        plt.figure(figsize=(10,5))
        plt.plot(ne_values, costsC,  'o-', label='Centralized')
        plt.plot(ne_values, costsCV,'^-', label='Centralized Mu-Variante')
        plt.plot(ne_values, costsS, 's--', label='Matching Statico')
        plt.plot(ne_values, costsD,'d-.', label='Matching Dinamico')
        plt.xlabel('ne')
        plt.ylabel('Costo medio')
        plt.title(f"Costo medio vs ne – {regime}")
        plt.legend()
        plt.grid(True)

        # Plot delle rilocazioni totali
        plt.figure(figsize=(10,5))
        plt.plot(ne_values, relC,   'o-',  label='Rilocazioni Centralized')
        plt.plot(ne_values, relCV, '^-',  label='Rilocazioni Mu-Variante')
        plt.plot(ne_values, relS,  's--', label='Rilocazioni Statico')
        plt.plot(ne_values, relD,  'd-.', label='Rilocazioni Dinamico')
        plt.xlabel('ne')
        plt.ylabel('Numero totale di rilocazioni')
        plt.title(f"Rilocazioni vs ne – {regime}")
        plt.legend()
        plt.grid(True)

        # Distribuzione dei costi per slot per un ne specifico
        target_ne = 50  # valore di ne da esaminare
        # Esegui una sola simulazione per ciascun algoritmo per raccogliere i costi per slot
        sd_i, sd_e = deepcopy(init_data), deepcopy(events)
        _, _, _, _, costsC_slots = run_centralized(sd_i, sd_e, regime, target_ne)

        sv_i, sv_e = deepcopy(init_data), deepcopy(events)
        _, _, _, _, costsCV_slots = run_centralized_mu_variant(sv_i, sv_e, regime, target_ne)

        ss_i, ss_e = deepcopy(init_data), deepcopy(events)
        _, _, _, _, costsS_slots = run_matchingStatic(ss_i, ss_e, regime, target_ne)

        sd2_i, sd2_e = deepcopy(init_data), deepcopy(events)
        _, _, _, _, costsD_slots = run_matchingDynamic(sd2_i, sd2_e, regime, target_ne)

        # Istogramma della distribuzione dei costi per slot
        plt.figure(figsize=(10,5))
        plt.hist(costsC_slots,   bins=30, density=True, alpha=0.5, label='Centralized')
        plt.hist(costsCV_slots, bins=30, density=True, alpha=0.5, label='MU-Variante')
        plt.xlabel('Costo per slot')
        plt.ylabel('Densità di probabilità')
        plt.title(f"Distribuzione costi per slot (ne={target_ne}) – {regime}")
        plt.legend()
        plt.grid(True)

        plt.figure(figsize=(10, 5))
        plt.hist(costsS_slots, bins=30, density=True, alpha=0.5, label='Statico')
        plt.hist(costsD_slots, bins=30, density=True, alpha=0.5, label='Dinamico')
        plt.xlabel('Costo per slot')
        plt.ylabel('Densità di probabilità')
        plt.title(f"Distribuzione costi per slot (ne={target_ne}) – {regime}")
        plt.legend()
        plt.grid(True)

    plt.show()


if __name__ == '__main__':
    main()
