import pyarrow.parquet as pq
import pandas as pd
from neo4j import GraphDatabase
import time
import csv
import os
class DataLoader:

    def __init__(self, uri, user, password):
        """
        Connect to the Neo4j database and other init steps

        Args:
            uri (str): URI of the Neo4j database
            user (str): Username of the Neo4j database
            password (str): Password of the Neo4j database
        """
        self.driver = GraphDatabase.driver(uri, auth=(user, password), encrypted=False)
        self.driver.verify_connectivity()


    def close(self):
        """
        Close the connection to the Neo4j database
        """
        self.driver.close()


    # Define a function to create nodes and relationships in the graph
    def load_transform_file(self, file_path):
        """
        Load the parquet file and transform it into a csv file
        Then load the csv file into neo4j

        Args:
            file_path (str): Path to the parquet file to be loaded
        """

        # Read the parquet file
        trips = pq.read_table(file_path)
        trips = trips.to_pandas()

        # Some data cleaning and filtering
        trips = trips[['tpep_pickup_datetime', 'tpep_dropoff_datetime', 'PULocationID', 'DOLocationID', 'trip_distance', 'fare_amount']]

        # Filter out trips that are not in bronx
        bronx = [3, 18, 20, 31, 32, 46, 47, 51, 58, 59, 60, 69, 78, 81, 94, 119, 126, 136, 147, 159, 167, 168, 169, 174, 182, 183, 184, 185, 199, 200, 208, 212, 213, 220, 235, 240, 241, 242, 247, 248, 250, 254, 259]
        trips = trips[trips.iloc[:, 2].isin(bronx) & trips.iloc[:, 3].isin(bronx)]
        trips = trips[trips['trip_distance'] > 0.1]
        trips = trips[trips['fare_amount'] > 2.5]

        trips['tpep_pickup_datetime'] = pd.to_datetime(trips['tpep_pickup_datetime']).dt.strftime('%Y-%m-%dT%H:%M:%S')
        trips['tpep_dropoff_datetime'] = pd.to_datetime(trips['tpep_dropoff_datetime']).dt.strftime('%Y-%m-%dT%H:%M:%S')

        # Convert to csv and store in the Neo4j import directory
        csv_file_name = file_path.split("/")[-1].replace(".parquet", ".csv")
        save_loc = f"../var/lib/neo4j/import/{csv_file_name}"
        os.makedirs(os.path.dirname(save_loc), exist_ok=True)
        trips.to_csv(save_loc, index=False,quoting=csv.QUOTE_NONE)

        # TODO: Your code here (Corrected Clearly Below)
        with self.driver.session() as session:
            session.run("""
                 LOAD CSV WITH HEADERS FROM $csv_url AS row
                MERGE (pickup:Location {name: toInteger(row.PULocationID)})
                MERGE (dropoff:Location {name: toInteger(row.DOLocationID)})
                CREATE (pickup)-[:TRIP {
                    distance: toFloat(row.trip_distance),
                    fare: toFloat(row.fare_amount),
                    pickup_dt: datetime(row.tpep_pickup_datetime),
                    dropoff_dt: datetime(row.tpep_dropoff_datetime)
                }]->(dropoff)
            """, {"csv_url": f"file:///{csv_file_name}"})

        print("Data successfully loaded into Neo4j from CSV!")

def main():

    total_attempts = 10
    attempt = 0

    # The database takes some time to startup!
    while attempt < total_attempts:
        try:
            data_loader = DataLoader("bolt://localhost:7687", "neo4j", "processingpipeline")
            data_loader.load_transform_file("/cse511/yellow_tripdata_2022-03.parquet")
            data_loader.close()

            attempt = total_attempts

        except Exception as e:
            print(f"(Attempt {attempt+1}/{total_attempts}) Error: ", e)
            attempt += 1
            time.sleep(10)


if __name__ == "__main__":
    main()