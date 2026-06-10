from app.db import get_session
import pandas as pd

def export_graph():
    query = """
    MATCH (d:Drug)-[r]->(e)
    RETURN d.name AS source, type(r) AS relation, e.name AS target
    """
    with get_session() as session:
        result = session.run(query)
        data = [dict(r) for r in result]

    df = pd.DataFrame(data)
    df.to_csv("graph_edges.csv", index=False)
    print("Saved graph_edges.csv")

if __name__ == "__main__":
    export_graph()