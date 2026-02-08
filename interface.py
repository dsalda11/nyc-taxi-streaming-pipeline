from neo4j import GraphDatabase

class Interface:
    def __init__(self, uri, user, password):
        self._driver = GraphDatabase.driver(uri, auth=(user, password), encrypted=False)
        self._driver.verify_connectivity()

    def close(self):
        self._driver.close()

    def _run_query(self, query, parameters=None):
        with self._driver.session() as session:
            return session.run(query, parameters or {}).data()

    def _drop_graph_if_exists(self):
        query = "CALL gds.graph.exists('myGraph') YIELD exists"
        result = self._run_query(query)
        if result and result[0]["exists"]:
            self._run_query("CALL gds.graph.drop('myGraph') YIELD graphName")

    def _ensure_graph_projected(self):
        set_weight_query = """
        MATCH ()-[r:TRIP]->()
        WHERE r.distance IS NOT NULL AND r.distance > 0
        SET r.weight = 1.0 / r.distance
        """
        self._run_query(set_weight_query)

        drop_query = """
        CALL gds.graph.exists('myGraph') YIELD exists
        WITH exists
        WHERE exists
        CALL gds.graph.drop('myGraph') YIELD graphName
        RETURN graphName
        """
        self._run_query(drop_query)

        project_query = """
        CALL gds.graph.project(
            'myGraph',
            'Location',
            {
                TRIP: {
                    properties: ['distance']
                }
            }
        )
        """
        self._run_query(project_query)

    def bfs(self, start_node, last_node=None):
        if last_node is None:
            raise ValueError("You must provide both start and end nodes for BFS.")

        query = """
        MATCH path = shortestPath(
            (start:Location {name: $start_name})-[*]-(end:Location {name: $end_name})
        )
        RETURN [node IN nodes(path) | { name: node.name }] AS path
        """
        result = self._run_query(query, {
            "start_name": int(start_node),
            "end_name": int(last_node)
        })

        if not result:
            return []
        return result

    def pagerank(self, max_iterations=20, weight_property="distance"):
        self._ensure_graph_projected()

        if weight_property:
            query = """
            CALL gds.pageRank.stream('myGraph', {
                maxIterations: $max_iterations,
                relationshipWeightProperty: $weight_property
            })
            YIELD nodeId, score
            WITH nodeId, score
            MATCH (n) WHERE id(n) = nodeId
            RETURN n.name AS name, score
            ORDER BY score DESC
            """
            parameters = {
                "max_iterations": max_iterations,
                "weight_property": weight_property
            }
        else:
            query = """
            CALL gds.pageRank.stream('myGraph', {
                maxIterations: $max_iterations
            })
            YIELD nodeId, score
            WITH nodeId, score
            MATCH (n) WHERE id(n) = nodeId
            RETURN n.name AS name, score
            ORDER BY score DESC
            """
            parameters = {
                "max_iterations": max_iterations
            }

        result = self._run_query(query, parameters)

        if not result:
            return []

        return [result[0], result[-1]]

if __name__ == "__main__":
    uri = "bolt://localhost:7687"
    user = "neo4j"
    password = "processingpipeline"

    interface = Interface(uri, user, password)

    print("Running PageRank...")
    pr_result = interface.pagerank(20)
    for row in pr_result:
        print(row)
    print("\nRunning BFS from node A:")
    bfs_path = interface.bfs(159, 212)
    print("Path:", bfs_path)

    interface.close()
