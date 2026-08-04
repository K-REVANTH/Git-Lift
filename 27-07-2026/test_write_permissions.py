from neo4j import GraphDatabase

driver = GraphDatabase.driver(
    "bolt+s://neo4j-bolt.ustpace.com:7687",
    auth=("neo4j", "password123")
)

try:
    with driver.session() as session:
        # Try to create ONE test node with unique label
        session.run("""
            CREATE (t:GitLift_PermissionTest {
                name: 'delete_me',
                created: datetime()
            })
        """)
        print("✅ WRITE PERMISSIONS: YES")

        # Immediately delete it
        session.run("""
            MATCH (t:GitLift_PermissionTest)
            DELETE t
        """)
        print("✅ DELETE PERMISSIONS: YES")

except Exception as e:
    print(f"❌ NO WRITE ACCESS: {e}")
    print("You'll need to use Neo4j Desktop locally instead.")

finally:
    driver.close()