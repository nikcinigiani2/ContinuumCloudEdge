import numpy as np
import copy
import random

from centralizedAllocation import centralized_allocation
from iterativeAllocation import matchingAlg

def calcolo_costo(partitions, app_cost):
    mat1 = np.array(partitions, dtype=np.float64)
    mat2 = np.array(app_cost,   dtype=np.float64)
    return np.sum(mat1 * mat2)

### SCENARIO ###
mu_up_min, mu_up_max = 1, 2
le_up_min, le_up_max = 1, 2
lc_up_min, lc_up_max = 1, 2
container_min, container_max = 5, 15
rate_min, rate_max = 1, 1
edge = 6
numAppl = 30
mu_appl = 15
l_appl = numAppl - mu_appl
cc = 6

# 1) Costi di deploy
app_cost = np.zeros((numAppl, edge + 1), dtype=int)
for i in range(numAppl):
    n_min = edge // 3
    n_max = edge // 3
    n_uni = edge - n_min - n_max
    vec = [mu_up_min]*n_min + [mu_up_max]*n_max + \
          list(np.random.uniform(mu_up_min, mu_up_max, size=n_uni))
    random.shuffle(vec)
    app_cost[i, :edge] = vec
# cloud
app_cost[:, edge] += cc

# override lambda-app costs
le_cost = (np.random.random((l_appl, edge+1)) * le_up_max) + le_up_min
lc_cost = (np.random.random((l_appl, edge+1)) * lc_up_max) + lc_up_min
l_cost  = le_cost + lc_cost
app_cost[mu_appl: , :edge] = l_cost[:, :edge]
app_cost[mu_appl: , edge] = l_cost[:, edge] + cc

# 2) Capacità edge
container_edge     = ((np.random.random(edge) * container_max) + container_min).astype(int)
service_rate_edge  = ((np.random.random(edge) * rate_max)     + rate_min).astype(int)
capacity_per_edge  = (container_edge * service_rate_edge).tolist()
service_rate_edge  = service_rate_edge.tolist()

# 3) Domanda di risorse
totAppl = ((np.random.random(numAppl) * (rate_max*2)) + (rate_min*2)).astype(int)
totAppl[:mu_appl] = 1

### MATCHING ALLOCATION ###
# copio i dati per non inquinarli
totM   = copy.deepcopy(totAppl)
capM   = copy.deepcopy(capacity_per_edge)
srvM   = copy.deepcopy(service_rate_edge)
costM  = copy.deepcopy(app_cost)

allocM, partM = matchingAlg(totM, capM, srvM, costM, edge, numAppl, mu_appl)
costoM = calcolo_costo(partM, app_cost)

print("=== MATCHING ALLOCATION ===")
print("Binary allocation (app x nodo):")
print(np.array(allocM))
print("Partitions (app x nodo):")
print(np.array(partM))
print(f"Costo MATCHING: {costoM}\n")

### CENTRALIZED ALLOCATION ###
totalC, allocC, partC, cost_mu, cost_lambda = centralized_allocation(
    app_cost,
    totAppl,
    capacity_per_edge,
    edge,
    mu_appl
)

print("=== CENTRALIZED ALLOCATION ===")
print("Binary allocation (app x nodo):")
print(allocC)
print("Partitions (app x nodo):")
print(partC)
print(f"Costo totale CENTRALIZED: {totalC}")
print(f"  - µ‑apps cost:     {cost_mu}")
print(f"  - λ‑apps cost:     {cost_lambda}")

#Riassunto costi totali
print(f"Costo totale MATCHING: {costoM}")
print(f"Costo totale CENTRALIZED: {totalC}")
#container domande
print(f"matrice dei costi: {app_cost}")