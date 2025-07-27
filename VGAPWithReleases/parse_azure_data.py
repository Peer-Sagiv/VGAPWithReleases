import sqlite3
import pandas as pd
import random
from consts import *
from members import Client
import numpy as np

# For now, use data from the 14 measurement days. I don't like using the previous data,
# As it's technically an ongoing request

AZURE_TIME_INTERVAL_DAYS = 14
AZURE_TIME_PARALLEL_DAYS = 7
AZURE_TIME_INTERVAL = 0.0001
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
        AND vm.endtime IS NOT NULL;
    """

    # Execute query and return as DataFrame
    df = pd.read_sql_query(query, conn)
    conn.close()

    filtered_df = df[
    df['memory'].notnull() &
    df['ssd'].notnull() &
    df['nic'].notnull() &
    df['core'].notnull() &
    (df['memory'] <= 0.5) &
    (df['ssd'] <= 0.5) &
    (df['core'] <= 0.5) &
    (df['nic'] <= 0.5)]

    return filtered_df

def fix_max_end_time(values, time_interval):
    for value in values:
        if int(value['end_time']) - int(value['start_time']) > time_interval:
            value['end_time'] = int(value['start_time']) + time_interval


def give_value_by_theta(inst, theta, pareto_alpha):
    inst_d = (int(inst['end_time']) - int(inst['start_time'])) / AZURE_TIME_INTERVAL
    if not pareto_alpha:
        # TODO: Random int? Why not random float?
        multiplier = random.randint(1, theta)
    else:
        multiplier = min((1 + np.random.pareto(pareto_alpha)), theta)
    inst["value"] = multiplier * (inst['memory'] + inst['ssd'] + inst['core'] + inst['nic']) * inst_d


def process_azure_data(theta, required_time, pareto_alpha, parallel_time=False):
    if parallel_time:
        base_time = AZURE_TIME_PARALLEL_DAYS / AZURE_TIME_INTERVAL
    else:
        base_time = AZURE_TIME_INTERVAL_DAYS / AZURE_TIME_INTERVAL
    max_query_interval = base_time - 4 * required_time
    current_query_time = random.uniform(1, max_query_interval) * AZURE_TIME_INTERVAL


    first_interval_values = get_assignments_starting_between(DB_NAME, current_query_time, required_time).to_dict(orient='records')
    if parallel_time:
        second_interval_values = get_assignments_starting_between(DB_NAME, current_query_time + AZURE_TIME_PARALLEL_DAYS, required_time).to_dict(orient='records')
    else:
        second_interval_values = get_assignments_starting_between(DB_NAME, current_query_time + required_time, required_time).to_dict(orient='records')

    # third_interval_values = get_assignments_starting_between(DB_NAME, current_query_time + required_time * 2, required_time)

    # if len(first_interval_values) < MIN_SAMPLE_SIZE or len(second_interval_values) < MIN_SAMPLE_SIZE or len(third_interval_values) < MIN_SAMPLE_SIZE:
    #     return None, None, None

    if len(first_interval_values) < MIN_SAMPLE_SIZE or len(second_interval_values) < MIN_SAMPLE_SIZE:
        return None, None

    first_interval_values.sort(key=lambda x: int(x['start_time']))
    second_interval_values.sort(key=lambda x: int(x['start_time']))
    # third_interval_values.sort(key=lambda x: int(x['start_time']))

    fix_max_end_time(first_interval_values, required_time)
    fix_max_end_time(second_interval_values, required_time)
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

    return history, clients
    