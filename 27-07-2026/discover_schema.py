"""
discover_schema.py

READ-ONLY schema discovery for existing Neo4j database.
This script only reads metadata and sample data.
It never creates, updates, or deletes anything.
"""

from neo4j import GraphDatabase


# Connection details
URI = "bolt+s://neo4j-bolt.ustpace.com:7687"
USERNAME = "neo4j"
PASSWORD = "password123"


class SchemaDiscovery:
    def __init__(self):
        self.driver = GraphDatabase.driver(
            URI,
            auth=(USERNAME, PASSWORD)
        )

        self.driver.verify_connectivity()

        print("[OK] Connected to Neo4j (READ-ONLY mode)")
        print()

    def close(self):
        self.driver.close()

    def read(self, query, params=None):
        """Execute a read-only query"""
        with self.driver.session(default_access_mode="READ") as session:
            result = session.run(query, params or {})
            return [record.data() for record in result]

    def discover_all(self):

        print("=" * 70)
        print("NEO4J SCHEMA DISCOVERY REPORT")
        print("=" * 70)

        #
        # 1. Node Labels
        #
        print("\nNODE LABELS (with counts)")
        print("-" * 70)

        node_counts = self.read("""
            MATCH (n)
            RETURN labels(n) AS labels,
                   count(*) AS count
            ORDER BY count DESC
        """)

        for row in node_counts:
            labels = ":".join(row["labels"])
            print(f"   {labels:40s} -> {row['count']:>10,} nodes")

        #
        # 2. Relationship Types
        #
        print("\nRELATIONSHIP TYPES (with counts)")
        print("-" * 70)

        rel_counts = self.read("""
            MATCH ()-[r]->()
            RETURN type(r) AS relationship,
                   count(*) AS count
            ORDER BY count DESC
        """)

        for row in rel_counts:
            print(
                f"   {row['relationship']:40s} -> {row['count']:>10,} rels"
            )

        #
        # 3. Labels
        #
        print("\nPROPERTIES OF EACH NODE TYPE")
        print("-" * 70)

        try:
            labels_result = self.read("""
                CALL db.labels()
                YIELD label
                RETURN label
                ORDER BY label
            """)
        except Exception:
            labels_result = self.read("""
                MATCH (n)
                UNWIND labels(n) AS label
                RETURN DISTINCT label
                ORDER BY label
            """)

        #
        # 4. Properties
        #
        for label_row in labels_result:

            label = label_row["label"]

            props = self.read(f"""
                MATCH (n:`{label}`)
                WITH n LIMIT 100
                UNWIND keys(n) AS key
                RETURN DISTINCT key
                ORDER BY key
            """)

            prop_list = [p["key"] for p in props]

            print(f"\n   {label}:")

            if prop_list:
                for prop in prop_list:
                    print(f"      - {prop}")
            else:
                print("      (no properties)")

        #
        # 5. Sample Nodes
        #
        print("\nSAMPLE NODE FROM EACH TYPE")
        print("-" * 70)

        for label_row in labels_result:

            label = label_row["label"]

            sample = self.read(f"""
                MATCH (n:`{label}`)
                RETURN n
                LIMIT 1
            """)

            print(f"\n   {label}:")

            if sample:
                node = dict(sample[0]["n"])

                for key, value in node.items():

                    value_str = str(value)

                    if len(value_str) > 80:
                        value_str = value_str[:80] + "..."

                    print(f"      {key}: {value_str}")

        #
        # 6. Relationship Patterns
        #
        print("\nRELATIONSHIP PATTERNS")
        print("-" * 70)

        patterns = self.read("""
            MATCH (a)-[r]->(b)
            RETURN labels(a) AS from_labels,
                   type(r) AS relationship,
                   labels(b) AS to_labels,
                   count(*) AS count
            ORDER BY count DESC
            LIMIT 50
        """)

        for row in patterns:

            from_lbl = ":".join(row["from_labels"])
            to_lbl = ":".join(row["to_labels"])

            print(
                f"   ({from_lbl}) "
                f"-[:{row['relationship']}]-> "
                f"({to_lbl}) = {row['count']:,}"
            )

        #
        # 7. Database Metadata
        #
        print("\nDATABASE METADATA")
        print("-" * 70)

        try:
            components = self.read("""
                CALL dbms.components()
                YIELD name, versions, edition
                RETURN name, versions, edition
            """)

            for component in components:
                print(
                    f"   {component['name']}: "
                    f"{component['versions']} "
                    f"({component['edition']})"
                )

        except Exception as e:
            print(f"   Error: {e}")

        #
        # 8. Constraints
        #
        print("\nCONSTRAINTS")
        print("-" * 70)

        try:
            constraints = self.read("SHOW CONSTRAINTS")

            if constraints:
                for c in constraints:
                    print(f"   {c}")
            else:
                print("   (No constraints found)")

        except Exception as e:
            print(f"   Error: {e}")

        #
        # 9. Indexes
        #
        print("\nINDEXES")
        print("-" * 70)

        try:
            indexes = self.read("SHOW INDEXES")

            if indexes:
                for idx in indexes:
                    print(f"   {idx}")
            else:
                print("   (No indexes found)")

        except Exception as e:
            print(f"   Error: {e}")

        print()
        print("=" * 70)
        print("DISCOVERY COMPLETE")
        print("=" * 70)


if __name__ == "__main__":

    discovery = None

    try:
        discovery = SchemaDiscovery()
        discovery.discover_all()

    except Exception as e:
        print(f"ERROR: {e}")
        raise

    finally:
        if discovery:
            discovery.close()