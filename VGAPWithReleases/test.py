import json
import csv
from collections import namedtuple

from newAlgs import VGAPWD
from members import Machine, Client
from OKPDAlgs import WCOAlg, GreedyAlg, Design1Alg, Design2Alg
from simpleAlgs import FirstFitAlg, BestFitAlg, RandomOrderAlg, WorstFitAlg
from optAlg import OPTAlg

GOOGLE_CLUSTERS_TIME_INTERVAL = 1000000
LOAD_RANDOM_DEMANDS = False

# with open("clean_1000_rounds_valued.json") as f:
#     rounds = json.load(f)
#     CLIENTS = [Client.from_json_entry(entry) for entry in rounds] 

# with open("clean_1000_history_valued.json") as f:
#     rounds = json.load(f)
#     HISTORY_SET = [Client.from_json_entry(entry) for entry in rounds] 

with open("first_five_minutes.csv") as f:
    raw_data = csv.DictReader(f)
    CLIENTS = [Client.from_csv_entry(entry, random_demands=LOAD_RANDOM_DEMANDS) for entry in raw_data]

with open("second_five_minutes.csv") as f:
    raw_data = csv.DictReader(f)
    HISTORY_SET = [Client.from_csv_entry(entry, random_demands=LOAD_RANDOM_DEMANDS) for entry in raw_data]

MACHINES = [Machine([1, 1]) for _ in range(1)]

ALG = namedtuple('ALG', ['instance', 'name'])



alg = VGAPWD(HISTORY_SET, MACHINES, CLIENTS)


first_fit = FirstFitAlg(MACHINES, CLIENTS)
best_fit = BestFitAlg(MACHINES, CLIENTS)
worst_fit = WorstFitAlg(MACHINES, CLIENTS)
random_order = RandomOrderAlg(MACHINES, CLIENTS)
opt_alg = OPTAlg(MACHINES, CLIENTS)


wco = WCOAlg(MACHINES, CLIENTS, GOOGLE_CLUSTERS_TIME_INTERVAL)
greedy = GreedyAlg(MACHINES, CLIENTS, 1)
design1 = Design1Alg(MACHINES, CLIENTS, 1)
design2 = Design2Alg(MACHINES, CLIENTS, 1)
opt_alg = OPTAlg(MACHINES, CLIENTS, GOOGLE_CLUSTERS_TIME_INTERVAL)

alg_res = alg.calc_value()
best_fit_res = best_fit.calc_value()
first_fit_res = first_fit.calc_value()
worst_fit_res = worst_fit.calc_value()
random_res = random_order.calc_value()

wco_res = wco.calc_value()
greedy_res = greedy.calc_value()
design_1_res = design1.calc_value()
design_2_res = design2.calc_value()

opt_res = opt_alg.calc_value()

print(f"OUR - {alg_res}. BEST FIT - {best_fit_res}. FIRST FIT - {first_fit_res}. WORST FIT - {worst_fit_res}. RANOM ORDER - {random_res}. WCO - {wco_res}. GREEDY - {greedy_res}. DESIGN 1 - {design_1_res}. DESIGN 2 - {design_2_res}. OPT - {opt_res}")