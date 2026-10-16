import os
from dotenv import load_dotenv
from falkordb import FalkorDB

# Load connection settings from .env file
load_dotenv()

def main():
    # Read cloud connection details from .env
    host = os.getenv("FALKORDB_HOST")
    port = int(os.getenv("FALKORDB_PORT", "6379"))
    password = os.getenv("FALKORDB_PASSWORD")
    username = os.getenv("FALKORDB_USERNAME")

    print(f"Connecting to FalkorDB Cloud at {host}:{port}...")

    try:
        # Step 1: Connect to your FalkorDB Cloud instance
        db = FalkorDB(
            host=host,
            port=port,
            password=password if password else None,
            username=username if username else None
        )

        # Step 2: Select the graph named 'fraudlens_test'
        graph = db.select_graph('fraudlens_test')

        # Step 3: Create a test node with label 'TestUser'
        create_query = "CREATE (u:TestUser {name: 'Alice', status: 'Active', created_at: '2026-10-17'})"
        graph.query(create_query)
        print(" Successfully created test node (Alice) in FalkorDB Cloud!")

        # Step 4: Query the graph to find Alice
        match_query = "MATCH (u:TestUser {name: 'Alice'}) RETURN u.name, u.status, u.created_at"
        result = graph.query(match_query)

        # Step 5: Print the returned result from the cloud
        print("\nQuery Results from 'fraudlens_test':")
        for record in result.result_set:
            print(f"-> Found TestUser: Name = {record[0]}, Status = {record[1]}, Created = {record[2]}")

    except Exception as error:
        # Step 6: Catch any errors
        print("\n[CONNECTION ERROR] Could not connect to FalkorDB Cloud.")
        print(f"Error details: {error}")

if __name__ == "__main__":
    main()
