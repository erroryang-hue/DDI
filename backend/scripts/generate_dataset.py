import random
import pandas as pd
from app.services.ddi_service import analyze_ddi
from app.models import DDIRequest

DRUGS = ["DrugA", "DrugB"]

def random_patient():
    return {
        "age": random.randint(18, 90),
        "weight": round(random.uniform(40, 100), 2),
        "dose1": round(random.uniform(50, 500), 2),
        "dose2": round(random.uniform(50, 500), 2),
        "start1": round(random.uniform(0, 12), 2),
        "start2": round(random.uniform(0, 12), 2),
        "interval1": random.choice([8, 12, 24]),
        "interval2": random.choice([8, 12, 24]),
        "half_life1": round(random.uniform(4, 24), 2),
        "half_life2": round(random.uniform(4, 24), 2),
        "poor_metabolizer": random.choice([True, False])
    }

def generate_sample():
    d1, d2 = random.sample(DRUGS, 2)
    patient = random_patient()

    req = DDIRequest(
        drug1=d1,
        drug2=d2,
        **patient
    )

    result = analyze_ddi(req)

    return {
        **patient,
        "drug1": d1,
        "drug2": d2,
        "risk_score": result["risk_score"],
        "severity": result["severity"]
    }

def generate_dataset(n=2000):
    data = [generate_sample() for _ in range(n)]
    df = pd.DataFrame(data)
    df.to_csv("ddi_dataset.csv", index=False)
    print("Dataset saved: ddi_dataset.csv")

if __name__ == "__main__":
    generate_dataset()