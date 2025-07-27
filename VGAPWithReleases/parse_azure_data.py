import sqlite3
import pandas as pd
import random
from consts import *
from members import Client, TimeWindow
import numpy as np

# For now, use data from the 14 measurement days. I don't like using the previous data,
# As it's technically an ongoing request

AZURE_TIME_INTERVAL_DAYS = 14
AZURE_TIME_PARALLEL_DAYS = 7
AZURE_TIME_INTERVAL = 0.0001 # 0.0024 hours = 8.64 seconds
MIN_VALID_TIME_REQUEST = 0.001
DB_NAME = "packing_trace_zone_a_v1.sqlite"


def get_assignments_starting_between(db_path, t, l):
    # Compute window end
    t_end = t + l

    # Connect to the database
    conn = sqlite3.connect(db_path)

    # SQL query: get VMs that start in [t, t + l)
    query = f"""
    SELECT
        vm.starttime as start_time,
        vm.endtime as end_time,
        vt.core,
        vt.memory,
        vt.ssd,
        vt.nic
    FROM
        vm
    JOIN
        vmType vt ON vm.vmTypeId = vt.vmTypeId
    WHERE
        vm.starttime >= {t}
        AND vm.starttime < {t_end}
        AND vm.endtime IS NOT NULL
        AND vt.memory IS NOT NULL
        AND vt.ssd IS NOT NULL
        AND vt.nic IS NOT NULL
        AND vt.core IS NOT NULL
        AND vt.memory <= 0.5
        AND vt.ssd <= 0.5
        AND vt.nic <= 0.5
        AND vt.core <= 0.5;
    """

    # Execute query and return as DataFrame
    df = pd.read_sql_query(query, conn)
    conn.close()

    return df

def fix_times(values, time_interval):
    for value in values:
        value['end_time'] = int(value['end_time'] / AZURE_TIME_INTERVAL)
        value['start_time'] = int(value['start_time'] / AZURE_TIME_INTERVAL)
        if value['end_time'] - value['start_time'] > time_interval:
            value['end_time'] = value['start_time'] + time_interval


def give_value_by_theta(inst, theta, pareto_alpha):
    inst_d = inst['end_time'] - inst['start_time']
    if not pareto_alpha:
        # TODO: Random int? Why not random float?
        multiplier = random.randint(1, theta)
    else:
        multiplier = min((1 + np.random.pareto(pareto_alpha)), theta)
    inst["value"] = multiplier * (inst['memory'] + inst['ssd'] + inst['core'] + inst['nic']) * inst_d


def process_azure_data(theta, required_time, history_time, pareto_alpha, parallel_time=False):
    if parallel_time and history_time != required_time:
        raise ValueError("Parallel can't run with history time different than required time")
    original_required_time = required_time
    required_time *= AZURE_TIME_INTERVAL
    if parallel_time:
        base_time = AZURE_TIME_PARALLEL_DAYS / AZURE_TIME_INTERVAL
    else:
        base_time = AZURE_TIME_INTERVAL_DAYS / AZURE_TIME_INTERVAL
    max_query_interval = base_time - 2 * required_time - history_time
    current_query_time = random.uniform(1, max_query_interval) * AZURE_TIME_INTERVAL

    history_start = current_query_time
    history_end = history_start + required_time
    first_interval_values = get_assignments_starting_between(DB_NAME, current_query_time, history_time).to_dict(orient='records')

    if parallel_time:
        online_start = current_query_time + AZURE_TIME_PARALLEL_DAYS
        online_end = online_start + required_time
        second_interval_values = get_assignments_starting_between(DB_NAME, current_query_time + AZURE_TIME_PARALLEL_DAYS, required_time).to_dict(orient='records')
    else:
        online_start = current_query_time + required_time
        online_end = online_start + required_time
        second_interval_values = get_assignments_starting_between(DB_NAME, current_query_time + required_time, required_time).to_dict(orient='records')

    # third_interval_values = get_assignments_starting_between(DB_NAME, current_query_time + required_time * 2, required_time)

    # if len(first_interval_values) < MIN_SAMPLE_SIZE or len(second_interval_values) < MIN_SAMPLE_SIZE or len(third_interval_values) < MIN_SAMPLE_SIZE:
    #     return None, None, None

    if len(first_interval_values) < MIN_SAMPLE_SIZE or len(second_interval_values) < MIN_SAMPLE_SIZE:
        return None, None

    first_interval_values.sort(key=lambda x: int(x['start_time']))
    second_interval_values.sort(key=lambda x: int(x['start_time']))
    # third_interval_values.sort(key=lambda x: int(x['start_time']))

    fix_times(first_interval_values, original_required_time)
    fix_times(second_interval_values, original_required_time)
    # fix_max_end_time(third_interval_values, required_time)

    # history_set, online_set, test_set = first_interval_values, second_interval_values, third_interval_values
    history_set, online_set = first_interval_values, second_interval_values
    for inst in history_set:
        give_value_by_theta(inst, theta, pareto_alpha)

    for inst in online_set:
        give_value_by_theta(inst, theta, pareto_alpha)
    
    # for inst in test_set:
    #     give_value_by_theta(inst, theta, pareto_alpha)

    history = [Client.from_azure_entry(entry) for entry in history_set]
    clients = [Client.from_azure_entry(entry) for entry in online_set]
    # test_values = [Client.from_csv_entry(entry) for entry in test_set]

    return TimeWindow(history, history_start, history_end, 1), TimeWindow(clients, online_start, online_end, 1)
