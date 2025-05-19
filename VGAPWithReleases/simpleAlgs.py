import random
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from .members import Machine, Client

class SimpleAlg:
    def __init__(self, machines: List['Machine'], clients:List['Client']):
        self._machines = machines
        self._clients = clients
        self._value = 0 

    def calc_value(self) -> int:
        for m in self._machines:
            m.clear()
        self._clients.sort(key=lambda c:c.assign_time)
        for c in self._clients:
            self.step(c)
        return self._value

class FirstFitAlg(SimpleAlg):
    def step(self, client: 'Client') -> None:
        for s in self._machines:
            s.flush(client)
            if s.check_feasible(client):
                s.assign(client)
                self._value += client.value
                return
    
class RandomOrderAlg(SimpleAlg):
    def step(self, client: 'Client') -> None:
        random_order_machines = self._machines.copy()
        random.shuffle(random_order_machines)
        for s in random_order_machines:
            s.flush(client)
            if s.check_feasible(client):
                s.assign(client)
                self._value += client.value
                return

class WorstFitAlg(SimpleAlg):
    def step(self, client: 'Client') -> None:
        max_residue = None
        fit_machine = None
        for s in self._machines:
            s.flush(client)
            if s.check_feasible(client):
                residue = s.calc_residue(client)
                if max_residue is None:
                    max_residue = residue
                    fit_machine = s
                else:
                    if max_residue < residue:
                        max_residue = residue
                        fit_machine = s
        if fit_machine is not None:
            fit_machine.assign(client)
            self._value += client.value

class BestFitAlg(SimpleAlg):
    def step(self, client: 'Client') -> None:
        min_residue = None
        fit_machine = None
        for s in self._machines:
            s.flush(client)
            if s.check_feasible(client):
                residue = s.calc_residue(client)
                if min_residue is None:
                    min_residue = residue
                    fit_machine = s
                else:
                    if min_residue > residue:
                        min_residue = residue
                        fit_machine = s
        if fit_machine is not None:
            fit_machine.assign(client)
            self._value += client.value
