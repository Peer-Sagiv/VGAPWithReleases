#!/bin/bash

TRIALS=10

# Time interval tests
for i in {10..100..10}; do
  for t in $(seq 1 $TRIALS); do
    srun -N1 -n1 --exclusive python test.py 50 $i $((i + 5)) False False "Time interval $i" $t &
  done
done

# Load tests
for i in {2..10}; do
  for t in $(seq 1 $TRIALS); do
    srun -N1 -n1 --exclusive python test.py 50 50 $i False False "Machine load $i machines" $t &
  done
done

# Theta tests
for i in 0.5 1.1 1.5 2 2.5 3 4 10; do
  for t in $(seq 1 $TRIALS); do
    srun -N1 -n1 --exclusive python test.py 50 50 5 False False "Pareto alpha $i" $t $i&
  done
done

wait
echo "All runs complete."