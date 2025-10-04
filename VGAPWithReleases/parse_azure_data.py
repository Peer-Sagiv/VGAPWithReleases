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
AZURE_TIME_INTERVAL = 0.00001 # 0.0024 hours = 8.64 seconds
DB_NAME = "packing_trace_zone_a_v1.sqlite"


def get_assignments_starting_between(db_path, t, l):
    # Compute window end
    #print(t)
    #print(l)
    #print(t + l)
    t_end = t + l

    conn = sqlite3.connect(db_path)

    query = """
    SELECT
        v.starttime AS start_time,
        v.endtime AS end_time,
        vt.core,
        vt.memory,
        vt.ssd,
        vt.nic
    FROM
        vm AS v
    JOIN
        vmType AS vt ON v.vmTypeId = vt.vmTypeId
    WHERE
        v.starttime >= ?
        AND v.starttime < ?
        AND v.endtime IS NOT NULL
        AND vt.memory IS NOT NULL
        AND vt.ssd IS NOT NULL
        AND vt.nic IS NOT NULL
        AND vt.core IS NOT NULL
        AND vt.memory <= 0.5
        AND vt.ssd <= 0.5
        AND vt.nic <= 0.5
        AND vt.core <= 0.5
        AND v.endtime > v.starttime + ?
    ORDER BY
        v.starttime ASC
    """

    #print("executing")
    df = pd.read_sql_query(query, conn, params=(t, t_end, AZURE_TIME_INTERVAL))

    #print("after executing")
    conn.close()

    return df

def post_process_entry(values, time_interval, theta, pareto_alpha):
    clients = []
    for value in values:
        value['end_time'] = int(value['end_time'] / AZURE_TIME_INTERVAL)
        value['start_time'] = int(value['start_time'] / AZURE_TIME_INTERVAL)
        if value['end_time'] - value['start_time'] > time_interval:
            value['end_time'] = value['start_time'] + time_interval
        give_value_by_theta(value, theta, pareto_alpha)
        clients.append(Client.from_azure_entry(value))
    return clients


def give_value_by_theta(inst, theta, pareto_alpha):
    inst_d = inst['end_time'] - inst['start_time']
    if not pareto_alpha:
        # TODO: Random int? Why not random float?
        multiplier = random.randint(1, theta)
    else:
        multiplier = min((1 + np.random.pareto(pareto_alpha)), theta)
    inst["value"] = multiplier * (inst['memory'] + inst['ssd'] + inst['core'] + inst['nic']) * inst_d


def process_azure_data(theta, required_time, history_time, pareto_alpha, parallel_time=False, arbitrary_start_azure_time=1.5):
    #if parallel_time and history_time != required_time:
    #    raise ValueError("Parallel can't run with history time different than required time")
    original_required_time = required_time
    original_history_time = history_time

    history_time *= AZURE_TIME_INTERVAL
    required_time *= AZURE_TIME_INTERVAL
    if parallel_time:
        base_time = AZURE_TIME_PARALLEL_DAYS / AZURE_TIME_INTERVAL
    else:
        base_time = AZURE_TIME_INTERVAL_DAYS / AZURE_TIME_INTERVAL

    three_hours_azure_time = 3 / 24.0

    arbitrary_start_in_intervals = arbitrary_start_azure_time / AZURE_TIME_INTERVAL
    three_hours_in_intervals = three_hours_azure_time / AZURE_TIME_INTERVAL

    end_time_in_intervals = arbitrary_start_in_intervals + three_hours_in_intervals

    max_query_interval = end_time_in_intervals - 2 * original_required_time - original_history_time
    current_query_time = random.uniform(arbitrary_start_in_intervals, max_query_interval) * AZURE_TIME_INTERVAL

    #max_query_interval = base_time - 2 * original_required_time - original_history_time

    #current_query_time = random.uniform(original_history_time, max_query_interval) * AZURE_TIME_INTERVAL



    if parallel_time:
        online_start = current_query_time + AZURE_TIME_PARALLEL_DAYS
        online_end = online_start + required_time

        history_end = current_query_time + required_time
        history_start = history_end - history_time
    else:
        history_start = current_query_time
        history_end = history_start + history_time

        online_start = history_end
        online_end = online_start + required_time

    first_interval_values = get_assignments_starting_between(DB_NAME, history_start, history_time).to_dict(orient='records')
    second_interval_values = get_assignments_starting_between(DB_NAME, online_start, required_time).to_dict(orient='records')

    if len(first_interval_values) < MIN_SAMPLE_SIZE or len(second_interval_values) < MIN_SAMPLE_SIZE:
        print(len(first_interval_values))
        print(len(second_interval_values))
        return None, None

    history = post_process_entry(first_interval_values, original_required_time, theta, pareto_alpha)
    clients = post_process_entry(second_interval_values, original_required_time, theta, pareto_alpha)

    return TimeWindow(history, history_start // AZURE_TIME_INTERVAL, history_end // AZURE_TIME_INTERVAL, 1), TimeWindow(clients, online_start // AZURE_TIME_INTERVAL, online_end // AZURE_TIME_INTERVAL, 1)


def process_azure_data_for_learning(theta, required_time, history_time):
    return process_azure_data(theta, required_time, history_time, arbitrary_start_azure_time=5)
