import matplotlib.pyplot as plt
import numpy as np
from mma_prob_model import FighterStats, win_probability, DEFAULT_WEIGHTS


def round_adjusted_weights(round_num: int, f1: FighterStats = None, f2: FighterStats = None, base_weights: dict = None) -> dict:
    """
    Ajusta os pesos conforme a progressão da luta, considerando fadiga individual.
    - Rounds iniciais: mais peso para grappling/agressividade.
    - Rounds médios/finais: mais peso para durabilidade e volume.
    """
    if base_weights is None:
        base_weights = DEFAULT_WEIGHTS.copy()
    w = base_weights.copy()

    # Fatores de fadiga
    def fatigue_factor(fighter: FighterStats, round_num: int):
        # Quanto maior aft_minutes, mais resistente
        base_endurance = fighter.aft_minutes / 15  # normaliza para 5 rounds de 5 minutos
        decay = 1 - (round_num - 1) * 0.15 / base_endurance  # decremento progressivo
        return max(0.5, decay)  # nunca abaixo de 50%

    f1_fatigue = fatigue_factor(f1, round_num) if f1 else 1.0
    f2_fatigue = fatigue_factor(f2, round_num) if f2 else 1.0

    if round_num <= 2:
        w["td_control_delta"] *= 1.3 * f1_fatigue
        w["td_vs_tdd_interaction"] *= 1.3 * f1_fatigue
        w["sub_delta"] *= 1.3 * f1_fatigue
    elif round_num >= 3:
        w["durability_delta"] *= 1.5 * f1_fatigue
        w["strike_output_delta"] *= 1.3 * f1_fatigue
        w["strike_safety_delta"] *= 1.2 * f1_fatigue

    return w

def round_win_probs(f1: FighterStats, f2: FighterStats, total_rounds: int = 5):
    """
    Calcula a probabilidade de vitória de f1 contra f2 em cada round.
    """
    probs = []
    for r in range(1, total_rounds + 1):
        w = round_adjusted_weights(r, f1=f1, f2=f2)
        p, _ = win_probability(f1, f2, weights=w)
        probs.append(p)
    return probs

def plot_round_probs(f1_name, f2_name, probs):
    rounds = np.arange(1, len(probs)+1)
    plt.plot(rounds, [p*100 for p in probs], marker="o", label=f"{f1_name}")
    plt.plot(rounds, [100-p*100 for p in probs], marker="o", label=f"{f2_name}")
    plt.axhline(50, color="gray", linestyle="--")
    plt.title("Probabilidade de Vitória ao Longo dos Rounds")
    plt.xlabel("Round")
    plt.ylabel("Probabilidade (%)")
    plt.legend()
    plt.grid(True)
    plt.show()

# -------------------------------
# Exemplo: Chimaev vs Du Plessis
# -------------------------------
chimaev = FighterStats(
    slpm=5.36, sapm=3.25, strike_acc=0.59, strike_def=0.42,
    td_avg15=4.31, td_acc=0.47, td_def=1.00,
    sub_avg15=2.77, kd_avg=0.62, aft_minutes=6.05
)

dricus = FighterStats(
    slpm=6.12, sapm=4.90, strike_acc=0.49, strike_def=0.54,
    td_avg15=2.55, td_acc=0.50, td_def=0.50,
    sub_avg15=0.73, kd_avg=0.48, aft_minutes=13.75
)

probs = round_win_probs(chimaev, dricus, total_rounds=5)
plot_round_probs("Chimaev", "Du Plessis", probs)
