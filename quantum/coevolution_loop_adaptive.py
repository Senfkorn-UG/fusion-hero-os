import os
import csv
import numpy as np
import random
from pathlib import Path

os.makedirs("quantum", exist_ok=True)
os.makedirs("hero-archive", exist_ok=True)

if os.path.exists("quantum/qubo_learned.npy"):
    Q = np.load("quantum/qubo_learned.npy")
elif os.path.exists("quantum/qubo_base.npy"):
    Q = np.load("quantum/qubo_base.npy")
else:
    n = 8
    Q = np.zeros((n, n))
    for i in range(n):
        Q[i, i] = -1.0
    Q = (Q + Q.T) / 2.0
    np.save("quantum/qubo_base.npy", Q)

n = Q.shape[0]
archive_path = Path("hero-archive/experiences.csv")
log_path = Path("quantum/coevolution_log.md")

if not archive_path.exists():
    with archive_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "x_bits", "score"])

if not log_path.exists():
    with log_path.open("w", encoding="utf-8") as f:
        f.write("# Coevolutionärer QUBO-Loop (adaptiv)\n\n")
        f.write("| Generation | mean_score | mean_energy | cost (var_E) | mutation_rate |\n")
        f.write("|-----------:|-----------:|------------:|-------------:|--------------:|\n")

def energy(Q, x):
    x_vec = np.array(x, dtype=float)
    return float(x_vec.T @ Q @ x_vec)

def random_individual(n, p=0.5):
    return [1 if random.random() < p else 0 for _ in range(n)]

def mutate_bits(bits, p_mut=0.1):
    out = []
    for b in bits:
        if random.random() < p_mut:
            out.append(1 - b)
        else:
            out.append(b)
    return out

def bits_to_str(bits):
    return "".join("1" if b == 1 else "0" for b in bits)

def append_experiences(rows):
    with archive_path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        for r in rows:
            writer.writerow(r)

def autopoietic_update_from_archive(Q, alpha=0.05):
    with archive_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        experiences = []
        for row in reader:
            bits = row["x_bits"].strip()
            score = float(row["score"])
            if len(bits) != Q.shape[0]:
                continue
            x = np.array([1 if b == "1" else 0 for b in bits], dtype=float)
            experiences.append((x, score))

    if not experiences:
        return Q

    for x, score in experiences:
        outer = np.outer(x, x)
        Q += -alpha * score * outer

    Q = (Q + Q.T) / 2.0
    return Q

def relu(x):
    return x if x > 0 else 0.0

NUM_GENERATIONS = 5
POP_SIZE = 10

MUTATION_RATE = 0.15
MU_MIN = 0.05
MU_MAX = 0.5

TARGET_HEALTH = 0.0
TARGET_ENERGY = -5.0
TARGET_COST   = 0.0

W_H = 0.1
W_E = 0.05
W_C = 0.05

for gen in range(NUM_GENERATIONS):
    current_generation = gen + 1
    print(f"=== Generation {current_generation} ===")

    population = []

    for i in range(POP_SIZE):
        if gen == 0:
            bits = random_individual(n, p=0.5)
        else:
            parent = random.choice(population)[0]
            bits = mutate_bits(parent, p_mut=MUTATION_RATE)
        population.append((bits, None))

    energies = []
    scores = []
    scored_rows = []

    for idx, (bits, _) in enumerate(population):
        E = energy(Q, bits)
        energies.append(E)
        score = -E + random.gauss(0.0, 0.1)
        scores.append(score)
        exp_id = f"g{current_generation}_cand{idx}"
        scored_rows.append((exp_id, bits_to_str(bits), score))

    append_experiences(scored_rows)

    mean_score = sum(scores) / len(scores)
    mean_energy = sum(energies) / len(energies)
    mean_E = mean_energy
    var_energy = sum((E - mean_E)**2 for E in energies) / len(energies)
    cost = var_energy

    Q = autopoietic_update_from_archive(Q, alpha=0.05)

    delta_mu = (
        W_H * relu(TARGET_HEALTH - mean_score) +
        W_E * relu(mean_energy - TARGET_ENERGY) +
        W_C * relu(cost - TARGET_COST)
    )

    new_mutation_rate = MUTATION_RATE + delta_mu
    new_mutation_rate = max(MU_MIN, min(MU_MAX, new_mutation_rate))

    print(
        f"Gen {current_generation}: "
        f"mean_score={mean_score:.3f}, "
        f"mean_energy={mean_energy:.3f}, "
        f"cost={cost:.3f}, "
        f"mutation {MUTATION_RATE:.3f} -> {new_mutation_rate:.3f}"
    )

    with log_path.open("a", encoding="utf-8") as f:
        f.write(
            f"| {current_generation} | "
            f"{mean_score:.4f} | "
            f"{mean_energy:.4f} | "
            f"{cost:.4f} | "
            f"{new_mutation_rate:.4f} |\n"
        )

    MUTATION_RATE = new_mutation_rate

    np.save(f"quantum/qubo_gen{current_generation}.npy", Q)
    np.savetxt(f"quantum/qubo_gen{current_generation}.csv", Q, delimiter=",")

np.save("quantum/qubo_learned.npy", Q)
np.savetxt("quantum/qubo_learned.csv", Q, delimiter=",")

print("Adaptive coevolutionärer 5-Generationen-Lauf abgeschlossen.")
print("Finales Q shape:", Q.shape)
