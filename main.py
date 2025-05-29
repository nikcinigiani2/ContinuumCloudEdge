import math
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt

from dataGenerator     import generate_data
from scenario          import generate_scenario, replay_scenario

#TODO: ricontrolla costo matching statico =0

"""def compute_time_horizon(init_data):
    lam = len(init_data['totAppl']) - init_data['mu_appl']
    return math.ceil(5 * (lam + init_data['mu_appl']) / 0.05) * 100
"""
timeHorizon =3000
TH = timeHorizon

def main():
    regimes   = ['scarsità', 'abbondanza']
    ne_values = list(range(10, 101, 10))

    for regime in regimes:
        # 1) Genero lo scenario *una sola volta* per questo regime
        base_init = generate_data()
        #TH        = compute_time_horizon(base_init)
        init_data, events = generate_scenario(TH, base_init)

        # 2) Per ogni ne faccio il replay sullo stesso scenario e raccolgo le medie
        mc, mgs, mgd = [], [], []
        for ne in ne_values:
            mean_c, mean_gs, mean_gd = replay_scenario(init_data, events, regime, ne)
            mc.append(mean_c)
            mgs.append(mean_gs)
            mgd.append(mean_gd)

        # 3) Grafico comparativo
        plt.figure()
        plt.plot(ne_values, mc,  'o-', label='Centralized')
        plt.plot(ne_values, mgs, 'x--', label='Greedy static')
        plt.plot(ne_values, mgd, 's-.', label='Greedy dynamic')
        plt.xlabel('ne (eventi tra ricalcolo)')
        plt.ylabel('Costo medio totale')
        plt.title(f"Costo medio vs ne – {regime}")
        plt.legend()
        plt.grid(True)

    plt.show()

if __name__ == '__main__':
    main()
