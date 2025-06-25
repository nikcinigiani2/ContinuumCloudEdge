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
    #timeHorizon = math.ceil((5 * (lam + mu) / p)) * ec
    timeHorizon = 30000

    # Generazione dello scenario con no-op inclusi
    init_data, events = generate_scenario(timeHorizon, base_init, p, nm)

    # Loop sui regimi
    for regime in regimes:
        # Liste per raccogliere risultati
        costsC, costsCV, costsS, costsD = [], [], [], []
        relC,    relCV,    relS,    relD    = [], [], [], []

        # Loop sui periodi di ricalcolo ne
        for ne in ne_values:
            # Centralized standard
            sd_init, sd_events = deepcopy(init_data), deepcopy(events)
            mc,   relC_i,  _,  _ = run_centralized(sd_init, sd_events, regime, ne)
            costsC.append(mc)
            relC.append(relC_i)

            # Centralized Mu-Variante
            smv_init, smv_events = deepcopy(init_data), deepcopy(events)
            mcv,  relCV_i, _, _ = run_centralized_mu_variant(smv_init, smv_events, regime, ne)
            costsCV.append(mcv)
            relCV.append(relCV_i)

            # Matching Statico
            ss_init, ss_events = deepcopy(init_data), deepcopy(events)
            ms,   relS_i, _,  _ = run_matchingStatic(ss_init, ss_events, regime, ne)
            costsS.append(ms)
            relS.append(relS_i)

            # Matching Dinamico
            sd2_init, sd2_events = deepcopy(init_data), deepcopy(events)
            md,   relD_i, _,  _ = run_matchingDynamic(sd2_init, sd2_events, regime, ne)
            costsD.append(md)
            relD.append(relD_i)

        # Plot dei costi medi
        plt.figure(figsize=(10,5))
        plt.plot(ne_values, costsC,  'o-', label='Centralized')
        plt.plot(ne_values, costsCV,'^-', label='Centralized Mu-Variante')
        plt.plot(ne_values, costsS, 's--',label='Matching Statico')
        plt.plot(ne_values, costsD,'d-.',label='Matching Dinamico')
        plt.xlabel('ne')
        plt.ylabel('Costo medio')
        plt.title(f"Costo medio vs ne – {regime}")
        plt.legend()
        plt.grid(True)

        # Plot delle rilocazioni totali
        plt.figure(figsize=(10,5))
        plt.plot(ne_values, relC,  'o-',  label='Rilocazioni Centralized')
        plt.plot(ne_values, relCV,'^-', label='Rilocazioni Mu-Variante')
        plt.plot(ne_values, relS, 's--',label='Rilocazioni Statico')
        plt.plot(ne_values, relD,'d-.',label='Rilocazioni Dinamico')
        plt.xlabel('ne')
        plt.ylabel('Numero totale di rilocazioni')
        plt.title(f"Rilocazioni vs ne – {regime}")
        plt.legend()
        plt.grid(True)

    plt.show()


if __name__ == '__main__':
    main()
