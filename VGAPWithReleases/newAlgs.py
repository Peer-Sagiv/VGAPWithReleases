import copy
import random
from typing import List
from pulp import *
from members import Machine, Client
from consts import *
from parse_raw_data import TimeWindow

SLOTS = 15000
class VGAPWD:
    def __init__(self, history_set, machines: List['Machine'], clients: List['Client'], alpha = None):
        self._slot_count = SLOTS
        self._clients: List['Client'] = copy.deepcopy(clients)
        self._history_set = copy.deepcopy(history_set)
        self._dimension = len(clients[0].demands)
        self._num_intervals = clients.length
        self._machines = machines
        self._current_assign_time = min(client.assign_time for client in self._clients) - 1
        self._value = 0
        if alpha:
            self._alpha = alpha
        else:
            self._alpha = self.default_alpha
        self._max_time = 2 * self._num_intervals * clients.unit_size
        self._current_index = 0
        self._current_random_index = 0
        self._pre_process_data()

    def _find_bottelneck_dimension(self, clients: List['Client']):
        total = [0.0] * len(clients[0].demands)
        for client in clients:
            for i, d in enumerate(client.demands):
                total[i] += d

        return max(range(len(total)), key=lambda i: total[i])

    # Should be changed for each class after test data
    @property
    def default_alpha(self):
        return 0.5

    def _pre_process_data(self):
        #self._history_set += [Client.unsatisfiable_client(self._dimension) for _ in range(self._slot_count * self._num_intervals - len(self._history_set))]
        self._number_of_dummies = self._slot_count * self._history_set.length - len(self._history_set)

    def _get_history_set(self):
        # print(f"History set size is {len(self._history_set)}")

        number_of_real = len(self._history_set)
        total = number_of_real + self._number_of_dummies
        sampled_indices = random.sample(range(total), self._num_intervals * self._slot_count)

        return [self._history_set[i] for i in sampled_indices if i < number_of_real]

    def _post_step(self, client):
        self._history_set += [client]

    def _pre_step_update_history(self, client: 'Client'):
        if client.assign_time > self._current_assign_time:
            self._current_assign_time = client.assign_time
            number_of_clients_in_interval = sum(1 for c in self._clients if c.assign_time == self._current_assign_time)
            self._random_sample_for_current_interval = random.sample(range(SLOTS), number_of_clients_in_interval)
            self._random_sample_for_current_interval.sort()
            self._current_index = 0
            self._current_random_index = 0

        prev_random_index = self._current_random_index
        self._current_random_index = self._random_sample_for_current_interval[self._current_index]
        self._current_index += 1
        number_of_dummies = self._current_random_index - prev_random_index
        self._number_of_dummies += number_of_dummies

    def _setup_step(self, client):
        self._pre_step_update_history(client)
        history_set: List['Client'] = self._get_history_set() + [client]
        for s in self._machines:
            s.flush(client)
        return history_set

    def step(self, client):
        history_set: List['Client'] = self._setup_step(client)
        prob = LpProblem("MultipleKnapsackWithDepartures", LpMaximize)

        x = LpVariable.dicts("x", ((c, s) for c in history_set for s in self._machines), lowBound=0, upBound=1)
        prob += lpSum(c.value * x[(c, s)] for c in history_set for s in self._machines)

        for c in history_set:
            prob += lpSum(x[(c, s)] for s in self._machines) <= 1
        for s in self._machines:
            for d in range(self._dimension):
                prob += lpSum(c.demands[d] * (c.departure_time - c.assign_time) * x[(c, s)] for c in history_set) <= self._max_time * s.capacity(d) * self._alpha

        prob.solve(PULP_CBC_CMD(msg=0))
        probs = [(s, x[(client, s)].varValue) for s in self._machines]
        total = sum(p for _, p in probs) if probs else 0
        if total == 0:
            assigned_machine = None
        else:
            normalized = [(s, p / total) for s, p in probs]
            slots, weights = zip(*normalized)
            assigned_machine = random.choices(slots, weights=weights)[0]

        if assigned_machine and assigned_machine.check_feasible(client):
            self._value += client.value
            assigned_machine.assign(client)

        self._post_step(client)

    def calc_value(self):
        for m in self._machines:
            m.clear()
        self._clients.sort(key=lambda c:c.assign_time)
        for i, c in enumerate(self._clients):
            self.step(c)
        return self._value


class VMKPSD(VGAPWD):
    def step(self, client):
        history_set: List['Client'] = self._setup_step(client)
        available = 0
        for s in self._machines:
            if s.check_feasible(client):
                available = 1

        if not available:
            return

        prob = LpProblem("VectorMultipleKnapsackWithDepartures", LpMaximize)

        x = LpVariable.dicts("y", ((c) for c in history_set), lowBound=0, upBound=1)
        prob += lpSum(c.value * x[(c)] for c in history_set)

        for d in range(self._dimension):
            prob += lpSum(c.demands[d] * (c.departure_time - c.assign_time) * x[(c)] for c in history_set) <= self._max_time * sum(s.capacity(d) for s in self._machines) * self._alpha

        prob.solve(PULP_CBC_CMD(msg=0))
        self._post_step(client)
        probability = x[(client)].varValue
        if probability < random.random():
            return
        for s in self._machines:
            if s.check_feasible(client):
                s.assign(client)
                self._value += client.value
                return


class VMKPSDWH:
    def __init__(self, larger_history, history_set, machines, clients):
        self._larger_history = larger_history
        self._history_set = history_set
        self._machines = machines
        self._clients = clients
        self._num_intervals = clients.length
        self._alphas = [0.125, 0.25, 0.5, 1]

    #def calc_value(self):
    #    best_alpha, best_val = None, -1
    #    for alpha in self._alphas:
    #        inst = VMKPSD(self._older_history_set, self._machines, self._history_set, alpha)
    #        val = inst.calc_value()
    #        if val > best_val:
    #            best_alpha = alpha
    #    inst = VMKPSD(self._history_set, self._machines, self._clients, best_alpha)
    #    return inst.calc_value()

    def calc_value(self):
        k = self._history_set.length  # window size

        alpha_values = {alpha: [] for alpha in self._alphas}


        n_trials = 0

        for win1, win2 in self._larger_history.iter_window_pairs(k):
            #print("tiral", n_trials)
            n_trials += 1
            for alpha in self._alphas:
                inst = VMKPSD(win1, self._machines, win2, alpha)
                val = inst.calc_value()
                alpha_values[alpha].append(val)
            #print(alpha_values)
        # Count wins per alpha by seeing which alpha has the highest val per window
        wins_count = {alpha: 0 for alpha in self._alphas}

        for i in range(n_trials):
            vals_at_i = [(alpha, alpha_values[alpha][i]) for alpha in self._alphas]
            max_val = max(v[1] for v in vals_at_i)
            winners = [alpha for alpha, val in vals_at_i if val == max_val]
            winner_alpha = max(winners)  # tie-break by largest alpha
            wins_count[winner_alpha] += 1

        max_wins = max(wins_count.values())
        candidates = [alpha for alpha, count in wins_count.items() if count == max_wins]
        best_alpha = max(candidates)

        inst = VMKPSD(self._history_set, self._machines, self._clients, best_alpha)
        return inst.calc_value()


class GreedyVGAPWD(VGAPWD):
    def step(self, client):
        history_set: List['Client'] = self._setup_step(client)
        prob = LpProblem("MultipleKnapsackWithDeparturesGreedyVGAP", LpMaximize)

        # We assume the capacity of each machine at each dimension is 1. Otherwise the model becomes undefined.
        working_machines = [Machine([m.capacity(0)]) for m in self._machines]
        x = LpVariable.dicts("x", ((c, s) for c in history_set for s in working_machines), lowBound=0, upBound=1)
        prob += lpSum(c.value * x[(c, s)] for c in history_set for s in working_machines)

        for c in history_set:
            prob += lpSum(x[(c, s)] for s in working_machines) <= 1

        releveant_dim = 0
        for s in working_machines:
            prob += lpSum(max(c.demands) * (c.departure_time - c.assign_time) * x[(c, s)] for c in history_set) <= self._max_time * s.capacity(releveant_dim) * self._alpha

        prob.solve(PULP_CBC_CMD(msg=0))
        probs = [(s, x[(client, s)].varValue) for s in working_machines]
        total = sum(p for _, p in probs) if probs else 0
        if total == 0:
            assigned_machine = None
        else:
            normalized = [(s, p / total) for s, p in probs]
            slots, weights = zip(*normalized)
            assigned_machine = random.choices(slots, weights=weights)[0]

        if assigned_machine:
            real_machine = self._machines[working_machines.index(assigned_machine)]
            if real_machine.check_feasible(client):
                self._value += client.value
                real_machine.assign(client)
        self._post_step(client)

class GreedyVMKPSD(VGAPWD):
    def _check_curr_round(self, client):
        history_set: List['Client'] = self._setup_step(client)
        releveant_dim = 0
        free_capacity = self._max_time * sum(s.capacity(releveant_dim) for s in self._machines) * self._alpha
        history_set.sort(key=self._sort_func,reverse=True)
        for c in history_set:
            if free_capacity > 0:
                if free_capacity >= max(c.demands) * (c.departure_time - c.assign_time):
                    if c is client:
                        return 1.0
                    free_capacity -= max(c.demands) * (c.departure_time - c.assign_time)
                    continue
                if c is client:
                    return self._partial_capacity_prob(c, free_capacity)
            else:
                return 0.0
        return 0.0

    def step(self, client):
        probability = self._check_curr_round(client)
        self._post_step(client)
        if probability < random.random():
            return
        for s in self._machines:
            if s.check_feasible(client):
                s.assign(client)
                self._value += client.value
                return

    def _sort_func(self, client: 'Client'):
        return client.value / (max(client.demands) * (client.departure_time - client.assign_time))

    def _partial_capacity_prob(self, client: 'Client', free_capacity):
        return free_capacity / (max(client.demands) * (client.departure_time - client.assign_time))


class GreedyVMKPSDNoInfo(GreedyVMKPSD):
    def _pre_process_data(self):
        releveant_dim = 0
        free_capacity = self._max_time * sum(s.capacity(releveant_dim) for s in self._machines)
        self._history_set.sort(key=self._sort_func,reverse=True)
        self._rate_threshold = 0
        for c in self._history_set:

            demand = c.one_dim_reduction_demand_over_time()
            if free_capacity - demand > 0:
                free_capacity -= demand
            else:
                self._rate_threshold = c.one_dim_reduction_rate()
                return

    def step(self, client):
        if client.one_dim_reduction_rate() > self._rate_threshold:
            for s in self._machines:
                if s.check_feasible(client):
                    s.assign(client)
                    self._value += client.value
                    return

