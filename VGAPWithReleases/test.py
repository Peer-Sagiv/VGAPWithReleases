import json
from collections import namedtuple

from newAlgs import VGAPWD
from members import Machine, Client
from OKPDAlgs import WCOAlg, GreedyAlg, Design1Alg, Design2Alg
from simpleAlgs import FirstFitAlg, BestFitAlg, RandomOrderAlg, WorstFitAlg
from optAlg import OPTAlg

with open("clean_1000_rounds_valued.json") as f:
    rounds = json.load(f)
    CLIENTS = [Client.from_json_entry(entry) for entry in rounds] 

with open("clean_1000_history_valued.json") as f:
    rounds = json.load(f)
    HISTORY_SET = [Client.from_json_entry(entry) for entry in rounds] 

MACHINES = [Machine([1, 1]) for _ in range(1)]
CLIENTS = [Client(0, 10, [1, 1], 1), Client(1, 10, [1, 1], 300)]
HISTORY_SET = [Client(0, 10, [1, 1], 1), Client(0, 10, [1, 1], 200)]

ALG = namedtuple('ALG', ['instance', 'name'])



alg = VGAPWD(HISTORY_SET, MACHINES, CLIENTS)


first_fit = FirstFitAlg(MACHINES, CLIENTS)
best_fit = BestFitAlg(MACHINES, CLIENTS)
worst_fit = WorstFitAlg(MACHINES, CLIENTS)
random_order = RandomOrderAlg(MACHINES, CLIENTS)
opt_alg = OPTAlg(MACHINES, CLIENTS)


wco = WCOAlg(MACHINES, CLIENTS, 1)
greedy = GreedyAlg(MACHINES, CLIENTS, 1)
design1 = Design1Alg(MACHINES, CLIENTS, 1)
design2 = Design2Alg(MACHINES, CLIENTS, 1)
opt_alg = OPTAlg(MACHINES, CLIENTS)

print(alg.calc_value())
print(best_fit.calc_value())
print(first_fit.calc_value())
print(worst_fit.calc_value())
print(random_order.calc_value())

print(wco.calc_value())
print(greedy.calc_value())
print(design1.calc_value())
print(design2.calc_value())


print(opt_alg.calc_value())