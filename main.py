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
    # Parametri
    regimes = ['scarsità', 'abbondanza']
    ne_values = list(range(10, 101, 10))
    target_ne = 20  # valore di ne su cui fare l'istogramma

    # Genera un unico scenario
    base_init = generate_data()
    lam = len(base_init['totAppl']) - base_init['mu_appl']
    mu = base_init['mu_appl']
    ec=10
    timeHorizon = math.ceil((5 * (lam + mu) / p)) * ec
    init_data, events = generate_scenario(timeHorizon, base_init, p, nm)

    # Per ogni regime, usa lo stesso scenario
    for regime in regimes:
        print(f"Esecuzione per regime: {regime}, timeHorizon: {timeHorizon}")
        # 1) Simulazioni su tutti i ne per costo medio e rilocazioni
        costsC, costsCV, costsS, costsD = [], [], [], []
        relC, relCV, relS, relD = [], [], [], []

        for ne in ne_values:
            print(f"Esecuzione per ne: {ne}")
            sd_i, sd_e = deepcopy(init_data), deepcopy(events)
            mc, rc_C, *_, _ = run_centralized(sd_i, sd_e, regime, ne)
            sv_i, sv_e = deepcopy(init_data), deepcopy(events)
            mcv, rc_CV, *_, _ = run_centralized_mu_variant(sv_i, sv_e, regime, ne)
            ss_i, ss_e = deepcopy(init_data), deepcopy(events)
            ms, rc_S, *_, _ = run_matchingStatic(ss_i, ss_e, regime, ne)
            sd2_i, sd2_e = deepcopy(init_data), deepcopy(events)
            md, rc_D, *_, _ = run_matchingDynamic(sd2_i, sd2_e, regime, ne)

            costsC.append(mc);
            relC.append(rc_C)
            costsCV.append(mcv);
            relCV.append(rc_CV)
            costsS.append(ms);
            relS.append(rc_S)
            costsD.append(md);
            relD.append(rc_D)

        # 2) Tabella costo medio vs ne
        plt.figure(figsize=(10, 5))
        plt.plot(ne_values, costsC, 'o-', label='Centralized')
        plt.plot(ne_values, costsCV, '^-', label='Mu-Variante')
        plt.plot(ne_values, costsS, 's--', label='Matching Statico')
        plt.plot(ne_values, costsD, 'd-.', label='Matching Dinamico')
        plt.xlabel('ne')
        plt.ylabel('Costo medio')
        plt.title(f'Costo medio vs ne – {regime}')
        plt.legend()
        plt.grid(True)

        # 3) Tabella rilocazioni vs ne
        plt.figure(figsize=(10, 5))
        plt.plot(ne_values, relC, 'o-', label='Centralized')
        plt.plot(ne_values, relCV, '^-', label='Mu-Variante')
        plt.plot(ne_values, relS, 's--', label='Matching Statico')
        plt.plot(ne_values, relD, 'd-.', label='Matching Dinamico')
        plt.xlabel('ne')
        plt.ylabel('Numero di rilocazioni')
        plt.title(f'Rilocazioni vs ne – {regime}')
        plt.legend()
        plt.grid(True)

        # 4) Una sola simulazione con ne = target_ne per istogrammi costi slot
        sd_i, sd_e = deepcopy(init_data), deepcopy(events)
        _, _, _, _, costsC_slots = run_centralized(sd_i, sd_e, regime, target_ne)
        sv_i, sv_e = deepcopy(init_data), deepcopy(events)
        _, _, _, _, costsCV_slots = run_centralized_mu_variant(sv_i, sv_e, regime, target_ne)
        ss_i, ss_e = deepcopy(init_data), deepcopy(events)
        _, _, _, _, costsS_slots = run_matchingStatic(ss_i, ss_e, regime, target_ne)
        sd2_i, sd2_e = deepcopy(init_data), deepcopy(events)
        _, _, _, _, costsD_slots = run_matchingDynamic(sd2_i, sd2_e, regime, target_ne)

        plt.figure(figsize=(10, 5))
        plt.hist(costsS_slots, bins=50, alpha=0.5, label='Matching Statico')
        plt.hist(costsD_slots, bins=50, alpha=0.5, label='Matching Dinamico')
        plt.xlabel('Costo per slot')
        plt.ylabel('Frequenza (numero di occorrenze)')
        plt.title(f'Distribuzione costi per slot Matching (ne={target_ne}) – {regime}')
        plt.legend()
        plt.grid(True)

        plt.figure(figsize=(10, 5))
        plt.hist(costsC_slots, bins=50, alpha=0.5, label='Centralized')
        plt.hist(costsCV_slots, bins=50, alpha=0.5, label='Mu-Variante')
        plt.xlabel('Costo per slot')
        plt.ylabel('Frequenza (numero di occorrenze)')
        plt.title(f'Distribuzione costi per slot Centralized (ne={target_ne}) – {regime}')
        plt.legend()
        plt.grid(True)

    plt.show()


if __name__ == '__main__':
    main()
