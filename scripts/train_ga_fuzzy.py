import random
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from typing import Dict, List, Tuple

try:
    from deap import base, creator, tools, algorithms
except ImportError:
    print("Please install deap: pip install deap")
    sys.exit(1)

# Importamos la función de evaluación y las configuraciones base
from src.systems.orders import (
    evaluar_propina_difusa, 
    TIEMPO_FUZZY, 
    COMIDA_FUZZY, 
    LIMPIEZA_FUZZY, 
    PROPINA_FUZZY
)

# Diccionario objetivo para nuestro Dataset sintético
# (tiempo_segundos, comida_pts, limpieza_porcentaje) -> propina_esperada
DATASET_IDEAL = [
    # Caso peores (Servicio muy lento, mala comida, muy sucio)
    (300.0, 0.5, 95.0, 0.0),
    (200.0, 1.0, 80.0, 2.0),
    (180.0, 2.0, 60.0, 5.0),
    
    # Casos normales (Servicio normal, comida normal, limpio/sucio)
    (100.0, 3.0, 50.0, 10.0),
    (90.0, 3.5, 40.0, 12.0),
    (120.0, 3.0, 10.0, 11.0),
    
    # Casos perfectos (Rápido, comida sabrosa, impecable)
    (40.0, 4.8, 5.0, 18.0),
    (60.0, 4.5, 15.0, 16.0),
    (30.0, 5.0, 0.0, 20.0),
]

# Funciones de utilidad para convertir DICCs a Listas (Cromosomas) y viceversa
def extract_keys_and_lengths() -> Tuple[Dict, Dict, Dict, Dict]:
    return (
        {k: len(v) for k, v in TIEMPO_FUZZY.items()},
        {k: len(v) for k, v in COMIDA_FUZZY.items()},
        {k: len(v) for k, v in LIMPIEZA_FUZZY.items()},
        {k: len(v) for k, v in PROPINA_FUZZY.items()},
    )

def flatten_dicts() -> List[float]:
    chromosome = []
    for d in (TIEMPO_FUZZY, COMIDA_FUZZY, LIMPIEZA_FUZZY, PROPINA_FUZZY):
        for k, v in d.items():
            chromosome.extend(v)
    return chromosome

def rebuild_dicts(chromosome: List[float], keys_lengths) -> Tuple[Dict, Dict, Dict, Dict]:
    idx = 0
    t_f, c_f, l_f, p_f = {}, {}, {}, {}
    dicts_to_fill = [t_f, c_f, l_f, p_f]
    
    for i, kl in enumerate(keys_lengths):
        for k, length in kl.items():
            shape = chromosome[idx:idx+length]
            # Asegurar que los puntos estén ordenados a <= b <= c <= d
            shape_sorted = sorted(shape)
            dicts_to_fill[i][k] = tuple(shape_sorted)
            idx += length
            
    return t_f, c_f, l_f, p_f

EXPECTED_LENGTH = len(flatten_dicts())
KEYS_AND_LENGTHS = extract_keys_and_lengths()

# -----------------
# Configuración GA (DEAP)
# -----------------
# Buscamos MINIMIZAR el error (peso -1.0)
creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
creator.create("Individual", list, fitness=creator.FitnessMin)

toolbox = base.Toolbox()

# Mutación: alterar ligeramente un parámetro
def mutate_fuzzy(individual, indpb):
    for i in range(len(individual)):
        if random.random() < indpb:
            # Los valores tienen diferentes escalas (0-300, 0-5, 0-100, 0-20),
            # Una mutación gaussiana proporcional a su propio tamaño
            varianza = max(5.0, individual[i] * 0.1)
            individual[i] += random.gauss(0, varianza)
            
            # Clamp limits generales para no tener vértices imposibles
            if individual[i] < 0: individual[i] = 0.0
    return individual,

toolbox.register("mutate", mutate_fuzzy, indpb=0.15)
toolbox.register("mate", tools.cxBlend, alpha=0.5)
toolbox.register("select", tools.selTournament, tournsize=3)

# Función de Evaluación (Fitness)
def evaluate_individual(individual):
    t_f, c_f, l_f, p_f = rebuild_dicts(individual, KEYS_AND_LENGTHS)
    
    mse = 0.0
    for tiempo, comida, limpieza, esperado in DATASET_IDEAL:
        resultado = evaluar_propina_difusa(
            tiempo, comida, limpieza, 
            config_tiempo=t_f, config_comida=c_f, config_limpieza=l_f, config_propina=p_f
        )
        obtenido = resultado["propina"]
        error = obtenido - esperado
        mse += (error ** 2)
        
    mse = mse / len(DATASET_IDEAL)
    return (mse,)

toolbox.register("evaluate", evaluate_individual)

def init_individual(icls):
    # Comenzar con el original pero mutarlo aleatoriamente (Exploración)
    base_ind = flatten_dicts()
    return icls([b + random.gauss(0, max(2.0, b*0.1)) for b in base_ind])

toolbox.register("individual", init_individual, creator.Individual)
toolbox.register("population", tools.initRepeat, list, toolbox.individual)

def main():
    print(f"--- Entrenamiento de Sistema Difuso (DEAP) ---")
    print(f"Tamaño del cromosoma: {EXPECTED_LENGTH} genes")
    
    pop = toolbox.population(n=60) # 60 individuos
    hof = tools.HallOfFame(1)      # Guarda el mejor histórico
    
    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register("avg", lambda fit: sum(f[0] for f in fit)/len(fit))
    stats.register("min", lambda fit: min(f[0] for f in fit))

    # Iniciar GA
    generations = 50
    print(f"Iniciando {generations} generaciones poblacionales...")
    pop, log = algorithms.eaSimple(pop, toolbox, cxpb=0.7, mutpb=0.3, ngen=generations, 
                                   stats=stats, halloffame=hof, verbose=True)
                                   
    best_ind = hof[0]
    print(f"\n====================================")
    print(f" Entrenamiento Finalizado")
    print(f" Mejor MSE Encontrado: {best_ind.fitness.values[0]:.4f}")
    print(f"====================================\n")
    
    t_f, c_f, l_f, p_f = rebuild_dicts(best_ind, KEYS_AND_LENGTHS)
    
    import json
    import os
    out_path = os.path.join("src", "systems", "fuzzy_weights.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    
    with open(out_path, 'w') as f:
        json.dump({
            "TIEMPO_FUZZY": t_f,
            "COMIDA_FUZZY": c_f,
            "LIMPIEZA_FUZZY": l_f,
            "PROPINA_FUZZY": p_f
        }, f, indent=4)
        
    print("======================================================")
    print(f"[OK] Los nuevos diccionarios han sido guardados automáticamente en:")
    print(f" -> {out_path}")
    print("El archivo orders.py detectará y usará estos pesos de inmediato.")
    print("======================================================")

if __name__ == "__main__":
    main()
