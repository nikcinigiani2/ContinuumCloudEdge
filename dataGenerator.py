import numpy as np

def generate_data():
    mu_up_min = 1   # uplink minimo per mu
    mu_up_max = 2   # uplink massimo per mu
    le_up_min = 1    # uplink minimo per lambda su edge
    le_up_max = 2   # uplink massimo per lambda su edge
    lc_up_min = 1    # costo lambda minimo su cloud
    lc_up_max = 2   # costo lambda massimo su cloud
    container_min = 15
    container_max = 15
    rate_max = 1
    rate_min = 1
    cost_min = rate_min * 2
    cost_max = rate_max * 2
    edge = 6
    numAppl = 30
    mu_appl = 15  # N applicazioni  μ
    l_appl = numAppl - mu_appl  # N applicazioni λ
    cc = 6 # Costo aggiuntivo  cloud, la prof aveva messo 6

    # matrice dei costi per tutte le applicazioni
    app_cost = (np.random.random([numAppl, edge+1]) * mu_up_max) + mu_up_min

    # generazione costi per applicazioni λ (ddiverso dalle μ)
    le_cost = (np.random.random([l_appl, edge+1]) * le_up_max) + le_up_min
    lc_cost = (np.random.random([l_appl, edge+1]) * lc_up_max) + lc_up_min
    l_cost = lc_cost + le_cost
    app_cost[mu_appl:mu_appl + l_appl, :] = l_cost[0:l_appl, :]

    # costo aggiuntivo per il cloud
    app_cost[:, edge] += cc

    # capacità di ogni nodo edge
    container_edge = (np.random.random([edge]) * container_max) + container_min
    service_rate_edge = (np.random.random([edge]) * rate_max) + rate_min
    capacity_per_edge = np.array(container_edge) * np.array(service_rate_edge)




    # simulo domanda di servizio per ogni applicazione
    totAppl = (np.random.random([numAppl]) * cost_max) + cost_min
    totAppl = totAppl.astype(int)
    totAppl[0:mu_appl] = 1  # imposto 1 per le applicazioni di tipo μ

    return {
        'app_cost': app_cost,
        'totAppl': totAppl,
        'capacity_per_edge': capacity_per_edge.tolist(),
        'num_edge': edge,
        'numAppl': numAppl,
        'mu_appl': mu_appl,
        'l_appl': l_appl
    }

if __name__ == '__main__':
    data = generate_data()
    for key, value in data.items():
        print(f"{key}: {value}")