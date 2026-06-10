import math


def elimination_rate(half_life: float) -> float:
    return math.log(2) / float(half_life)


def exposure(t: float, k: float) -> float:
    return math.exp(-k * t)


def temporal_overlap(start1: float, start2: float, half_life1: float, half_life2: float, horizon: float = 48.0, step: float = 0.5) -> float:
    k1 = elimination_rate(half_life1)
    k2 = elimination_rate(half_life2)

    t = 0.0
    overlap = 0.0
    total = 0.0

    while t <= horizon:
        c1 = exposure(max(0.0, t - start1), k1) if t >= start1 else 0.0
        c2 = exposure(max(0.0, t - start2), k2) if t >= start2 else 0.0

        overlap += min(c1, c2) * step
        total += max(c1, c2) * step
        t += step

    return overlap / total if total > 0.0 else 0.0


if __name__ == "__main__":
    print(temporal_overlap(0, 2, 24, 24))
