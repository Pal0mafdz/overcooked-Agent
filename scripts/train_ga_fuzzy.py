import json
import random
import sys
import os
from typing import Dict, List, Tuple

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from deap import base, creator, tools, algorithms
except ImportError:
    print("Please install deap: pip install deap")
    sys.exit(1)

from src.systems.orders import (
    evaluar_propina_difusa,
    DEFAULT_TIEMPO_FUZZY,
    DEFAULT_COMIDA_FUZZY,
    DEFAULT_LIMPIEZA_FUZZY,
    DEFAULT_PROPINA_FUZZY,
    REGLAS_PROPINA,
)

DATASET_IDEAL = [
    (300.0, 0.5, 95.0, 0.0),
    (200.0, 1.0, 80.0, 2.0),
    (180.0, 2.0, 60.0, 5.0),
    (120.0, 3.0, 10.0, 11.0),
    (100.0, 3.0, 50.0, 10.0),
    (90.0, 3.5, 40.0, 12.0),
    (60.0, 4.5, 15.0, 16.0),
    (40.0, 4.8, 5.0, 18.0),
    (30.0, 5.0, 0.0, 20.0),
]

BASE_CONFIGS = {
    "TIEMPO_FUZZY": DEFAULT_TIEMPO_FUZZY,
    "COMIDA_FUZZY": DEFAULT_COMIDA_FUZZY,
    "LIMPIEZA_FUZZY": DEFAULT_LIMPIEZA_FUZZY,
    "PROPINA_FUZZY": DEFAULT_PROPINA_FUZZY,
}

DOMAIN_LIMITS = {
    "TIEMPO_FUZZY": (0.0, 300.0),
    "COMIDA_FUZZY": (0.0, 5.0),
    "LIMPIEZA_FUZZY": (0.0, 100.0),
    "PROPINA_FUZZY": (0.0, 20.0),
}

NEUTRAL_LABELS = {
    "tiempo": "regular",
    "comida": "normal",
    "limpieza": "aceptable",
}

CONSEQUENT_TARGETS = {
    "nada": (0.0, 4.0),
    "poca": (2.0, 8.0),
    "normal": (7.0, 13.0),
    "suficiente": (11.0, 18.0),
    "mucha": (16.0, 20.0),
}


def clip_value(value: float, min_value: float, max_value: float) -> float:
    return max(min_value, min(max_value, float(value)))


SECTION_ORDER = list(BASE_CONFIGS.keys())
SECTION_META = []
for section_name in SECTION_ORDER:
    config = BASE_CONFIGS[section_name]
    min_value, max_value = DOMAIN_LIMITS[section_name]
    for label, shape in config.items():
        SECTION_META.append({
            "section": section_name,
            "label": label,
            "length": len(shape),
            "min": min_value,
            "max": max_value,
        })


def extract_keys_and_lengths() -> Tuple[Dict, Dict, Dict, Dict]:
    return tuple({k: len(v) for k, v in BASE_CONFIGS[section].items()} for section in SECTION_ORDER)


KEYS_AND_LENGTHS = extract_keys_and_lengths()


def flatten_dicts() -> List[float]:
    chromosome = []
    for section_name in SECTION_ORDER:
        for shape in BASE_CONFIGS[section_name].values():
            chromosome.extend(shape)
    return chromosome


EXPECTED_LENGTH = len(flatten_dicts())


def normalize_shape(shape: List[float], min_value: float, max_value: float) -> Tuple[float, ...]:
    clipped = [clip_value(value, min_value, max_value) for value in shape]
    clipped.sort()
    return tuple(clipped)


def rebuild_dicts(chromosome: List[float], keys_lengths) -> Tuple[Dict, Dict, Dict, Dict]:
    idx = 0
    dicts_to_fill = [{}, {}, {}, {}]

    for dict_index, (section_name, key_lengths) in enumerate(zip(SECTION_ORDER, keys_lengths)):
        min_value, max_value = DOMAIN_LIMITS[section_name]
        for label, length in key_lengths.items():
            shape = chromosome[idx:idx + length]
            dicts_to_fill[dict_index][label] = normalize_shape(shape, min_value, max_value)
            idx += length

    return tuple(dicts_to_fill)


BASE_CHROMOSOME = flatten_dicts()


def sanitize_individual(individual: List[float]) -> List[float]:
    idx = 0
    sanitized = []
    for meta in SECTION_META:
        length = meta["length"]
        shape = individual[idx:idx + length]
        sanitized.extend(normalize_shape(shape, meta["min"], meta["max"]))
        idx += length
    individual[:] = sanitized
    return individual


if not hasattr(creator, "FitnessMin"):
    creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
if not hasattr(creator, "Individual"):
    creator.create("Individual", list, fitness=creator.FitnessMin)

toolbox = base.Toolbox()


def mutate_fuzzy(individual, indpb):
    idx = 0
    for meta in SECTION_META:
        min_value = meta["min"]
        max_value = meta["max"]
        for gene_offset in range(meta["length"]):
            gene_index = idx + gene_offset
            if random.random() < indpb:
                span = max_value - min_value
                sigma = max(0.05 * span, abs(individual[gene_index]) * 0.08)
                individual[gene_index] += random.gauss(0, sigma)
                individual[gene_index] = clip_value(individual[gene_index], min_value, max_value)
        idx += meta["length"]
    sanitize_individual(individual)
    return individual,


def mate_and_sanitize(ind1, ind2):
    tools.cxBlend(ind1, ind2, alpha=0.25)
    sanitize_individual(ind1)
    sanitize_individual(ind2)
    return ind1, ind2


def representative_value(shape: Tuple[float, ...]) -> float:
    return sum(shape) / len(shape)


DEFAULT_REPRESENTATIVES = {
    "tiempo": {label: representative_value(shape) for label, shape in DEFAULT_TIEMPO_FUZZY.items()},
    "comida": {label: representative_value(shape) for label, shape in DEFAULT_COMIDA_FUZZY.items()},
    "limpieza": {label: representative_value(shape) for label, shape in DEFAULT_LIMPIEZA_FUZZY.items()},
}


def rule_penalty(t_f, c_f, l_f, p_f) -> float:
    penalty = 0.0
    for antecedente, consecuente in REGLAS_PROPINA:
        tiempo = DEFAULT_REPRESENTATIVES["tiempo"][NEUTRAL_LABELS["tiempo"]]
        comida = DEFAULT_REPRESENTATIVES["comida"][NEUTRAL_LABELS["comida"]]
        limpieza = DEFAULT_REPRESENTATIVES["limpieza"][NEUTRAL_LABELS["limpieza"]]

        if "tiempo" in antecedente:
            tiempo = DEFAULT_REPRESENTATIVES["tiempo"][antecedente["tiempo"]]
        if "comida" in antecedente:
            comida = DEFAULT_REPRESENTATIVES["comida"][antecedente["comida"]]
        if "limpieza" in antecedente:
            limpieza = DEFAULT_REPRESENTATIVES["limpieza"][antecedente["limpieza"]]

        obtained = evaluar_propina_difusa(
            tiempo,
            comida,
            limpieza,
            config_tiempo=t_f,
            config_comida=c_f,
            config_limpieza=l_f,
            config_propina=p_f,
        )["propina"]

        expected_min, expected_max = CONSEQUENT_TARGETS[consecuente]
        if obtained < expected_min:
            penalty += (expected_min - obtained) ** 2
        elif obtained > expected_max:
            penalty += (obtained - expected_max) ** 2
    return penalty / len(REGLAS_PROPINA)


def evaluate_individual(individual):
    sanitize_individual(individual)
    t_f, c_f, l_f, p_f = rebuild_dicts(individual, KEYS_AND_LENGTHS)

    mse = 0.0
    for tiempo, comida, limpieza, esperado in DATASET_IDEAL:
        obtenido = evaluar_propina_difusa(
            tiempo,
            comida,
            limpieza,
            config_tiempo=t_f,
            config_comida=c_f,
            config_limpieza=l_f,
            config_propina=p_f,
        )["propina"]
        mse += (obtenido - esperado) ** 2

    mse /= len(DATASET_IDEAL)
    penalty = rule_penalty(t_f, c_f, l_f, p_f)
    total_error = mse + (4.0 * penalty)
    return (total_error,)


def init_individual(icls):
    noisy = []
    idx = 0
    for meta in SECTION_META:
        span = meta["max"] - meta["min"]
        for _ in range(meta["length"]):
            base_value = BASE_CHROMOSOME[idx]
            noisy_value = base_value + random.gauss(0, span * 0.03)
            noisy.append(clip_value(noisy_value, meta["min"], meta["max"]))
            idx += 1
    individual = icls(noisy)
    sanitize_individual(individual)
    return individual


toolbox.register("mutate", mutate_fuzzy, indpb=0.15)
toolbox.register("mate", mate_and_sanitize)
toolbox.register("select", tools.selTournament, tournsize=3)
toolbox.register("evaluate", evaluate_individual)
toolbox.register("individual", init_individual, creator.Individual)
toolbox.register("population", tools.initRepeat, list, toolbox.individual)


def main():
    print("--- Entrenamiento de Sistema Difuso (DEAP) ---")
    print(f"Tamaño del cromosoma: {EXPECTED_LENGTH} genes")

    pop = toolbox.population(n=60)
    hof = tools.HallOfFame(1)

    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register("avg", lambda fit: sum(f[0] for f in fit) / len(fit))
    stats.register("min", lambda fit: min(f[0] for f in fit))

    generations = 50
    print(f"Iniciando {generations} generaciones poblacionales...")
    pop, log = algorithms.eaSimple(
        pop,
        toolbox,
        cxpb=0.7,
        mutpb=0.3,
        ngen=generations,
        stats=stats,
        halloffame=hof,
        verbose=True,
    )

    best_ind = hof[0]
    sanitize_individual(best_ind)
    print("\n====================================")
    print(" Entrenamiento Finalizado")
    print(f" Mejor Fitness Encontrado: {best_ind.fitness.values[0]:.4f}")
    print("====================================\n")

    t_f, c_f, l_f, p_f = rebuild_dicts(best_ind, KEYS_AND_LENGTHS)

    out_path = os.path.join("src", "systems", "fuzzy_weights.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "TIEMPO_FUZZY": t_f,
                "COMIDA_FUZZY": c_f,
                "LIMPIEZA_FUZZY": l_f,
                "PROPINA_FUZZY": p_f,
            },
            f,
            indent=4,
        )

    print("======================================================")
    print("[OK] Los nuevos diccionarios han sido guardados automáticamente en:")
    print(f" -> {out_path}")
    print("El archivo orders.py detectará y usará estos pesos de inmediato.")
    print("======================================================")


if __name__ == "__main__":
    main()