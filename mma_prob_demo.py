
from mma_prob_model import FighterStats, win_probability, explain, bootstrap_probability

# Khamzat Chimaev (from user's image)
chimaev = FighterStats(
    slpm=5.36,
    sapm=3.25,
    strike_acc=0.59,
    strike_def=0.42,
    td_avg15=4.31,
    td_acc=0.47,
    td_def=1.00,
    sub_avg15=2.77,
    kd_avg=0.62,
    aft_minutes=6.05,
)

# Dricus du Plessis (from user's image)
dricus = FighterStats(
    slpm=6.12,
    sapm=4.90,
    strike_acc=0.49,
    strike_def=0.54,
    td_avg15=2.55,
    td_acc=0.50,
    td_def=0.50,
    sub_avg15=0.73,
    kd_avg=0.48,
    aft_minutes=13.75,  # 13:45 -> 13.75
)

p, contrib = win_probability(chimaev, dricus)
mean_p, (lo, hi) = bootstrap_probability(chimaev, dricus, iters=400, noise=0.03)

print(f"P(Chimaev vence Du Plessis) = {p*100:.1f}%  |  CI~90%: [{lo*100:.1f}%, {hi*100:.1f}%]")
print("Contribuições (termo do modelo):")
for k, v in sorted(contrib.items(), key=lambda kv: -abs(kv[1])):
    print(f"  {k:25s} -> {v:+.3f}")
