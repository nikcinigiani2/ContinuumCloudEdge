# main.py
import math
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt

from dataGenerator import generate_data
from scenario import generate_scenario, p, nm
from centralizedScenario import run_centralized
from matchingStaticoScenario import run_matchingStatic
from matchingDinamicoScenario import run_matchingDynamic
from copy import deepcopy

def main():
    regimes   = ['scarsità', 'abbondanza']
    ne_values = list(range(10, 101, 10))

    base_init = generate_data()
    lam = len(base_init['totAppl']) - base_init['mu_appl']
    mu  = base_init['mu_appl']

    ec = 100
    timeHorizon = math.ceil((5 * (lam + mu) / p)) * ec

    # genero scenario (init_data invariato) e lista eventi
    init_data, events = generate_scenario(timeHorizon, base_init, p, nm)

    for regime in regimes:
        mc, ms, md = [], [], []
        relC, relS, relD = [], [], []

        for ne in ne_values:
            # centralized
            sd_init, sd_events = deepcopy(init_data), deepcopy(events)
            mc_i, relC_i, effC, cycC = run_centralized(sd_init, sd_events, regime, ne)
            mc.append(mc_i); relC.append(relC_i)

            # statico
            ss_init, ss_events = deepcopy(init_data), deepcopy(events)
            ms_i, relS_i, effS, cycS = run_matchingStatic(ss_init, ss_events, regime, ne)
            ms.append(ms_i); relS.append(relS_i)

            # dinamico
            sd2_init, sd2_events = deepcopy(init_data), deepcopy(events)
            md_i, relD_i, effD, cycD = run_matchingDynamic(sd2_init, sd2_events, regime, ne)
            md.append(md_i); relD.append(relD_i)

        # plot costi
        plt.figure(figsize=(10,5))
        plt.plot(ne_values, mc,  'o-', label='Centralized')
        plt.plot(ne_values, ms, 's--', label='Matching Statico')
        plt.plot(ne_values, md, 'd-.', label='Matching Dinamico')
        plt.xlabel('ne')
        plt.ylabel('Costo medio')
        plt.title(f"Costo medio vs ne – {regime}")
        plt.legend(); plt.grid(True)

        # plot rilocazioni
        plt.figure(figsize=(10,5))
        plt.plot(ne_values, relC,  'o-', label='Rilocazioni Centralized')
        plt.plot(ne_values, relS, 's--', label='Rilocazioni Statico')
        plt.plot(ne_values, relD, 'd-.', label='Rilocazioni Dinamico')
        plt.xlabel('ne')
        plt.ylabel('Numero totale di rilocazioni')
        plt.title(f"Rilocazioni vs ne – {regime}")
        plt.legend(); plt.grid(True)

    plt.show()

if __name__ == '__main__':
    main()
