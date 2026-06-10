from neo4j import GraphDatabase
import os

URI = "bolt://localhost:7687"
USER = "neo4j"
PASSWORD = "password"

driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

def get_session():
    return driver.session()