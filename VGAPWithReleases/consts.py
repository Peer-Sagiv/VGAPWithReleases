HISTORY_FROM_CLUSTER_A = "history_cluster_a.csv"
CLIENTS_FROM_CLUSTER_A = "clients_cluster_a.csv"

A_RUNS = "runs_from_cluster_a.csv"
COMBINED_A_RUNS = "runs_from_cluster_a_combined_merged_full2.csv"
H_RUNS = "cluster_h_first10min.csv"
THETA = 50

MIN_SAMPLE_SIZE = 800
SECOND = 1_000

GOOGLE_CLUSTERS_TIME_INTERVAL = 1_000_000

QUERY_START_TIME = 1200_000_000
QUERY_END_TIME = 1800_000_000
# Allow an extra interval to be taken

# Alg names

VGAPWD_NAME = "VGAPWD"
VMKPSD_NAME = "VMKPSD"
BEST_FIT_NAME = "Best fit"
FIRST_FIT_NAME = "First fit"
WORST_FIT_NAME = "Worst fit"
RANDOM_ORDER_NAME = "Random order fit"
WCO_NAME ="WCO"
GREEDY_NAME = "Greedy"
DESIGN_1_NAME = "Design 1"
DESIGN_2_NAME = "Design 2"
DATA_DRIVEN_NAME = "Data driven"
GAMMA_OFFLINE_NAME = "Gamma offline"
OPT_NAME = "OPT"

ALGS_NAMES = [VGAPWD_NAME, VMKPSD_NAME, BEST_FIT_NAME, FIRST_FIT_NAME,
              WORST_FIT_NAME, RANDOM_ORDER_NAME, WCO_NAME,
              GREEDY_NAME, DESIGN_1_NAME, DESIGN_2_NAME, DATA_DRIVEN_NAME,
              GAMMA_OFFLINE_NAME, OPT_NAME]
