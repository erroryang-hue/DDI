from app.db import get_session

def init_graph():
    with get_session() as session:
        session.run("""
        MERGE (e:Enzyme {name: 'CYP3A4'})
        MERGE (d1:Drug {name: 'DrugA'})
        MERGE (d2:Drug {name: 'DrugB'})

        MERGE (d1)-[:INHIBITS]->(e)
        MERGE (d2)-[:METABOLIZED_BY]->(e)
        """)

if __name__ == "__main__":
    init_graph()