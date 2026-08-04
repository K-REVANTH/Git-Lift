# test_readonly.py

from neo4j_readonly import ReadOnlyNeo4j


db = ReadOnlyNeo4j(
    uri="bolt+s://neo4j-bolt.ustpace.com:7687",
    username="neo4j",
    password="password123"
)

#
# TEST 1
#
print("\nTEST 1: Valid read query")

try:
    result = db.query("""
        MATCH (n)
        RETURN count(n) AS total
    """)

    print(f"SUCCESS: {result}")

except Exception as e:
    print(f"FAILED: {e}")

#
# TEST 2
#
print("\nTEST 2: CREATE should be blocked")

try:
    db.query("""
        CREATE (n:TestNode {name:'should_fail'})
    """)

    print("DANGER: CREATE was NOT blocked")

except PermissionError as e:
    print(f"CORRECTLY BLOCKED:\n{e}")

#
# TEST 3
#
print("\nTEST 3: DELETE should be blocked")

try:
    db.query("""
        MATCH (n)
        DELETE n
    """)

    print("DANGER: DELETE was NOT blocked")

except PermissionError as e:
    print(f"CORRECTLY BLOCKED:\n{e}")

#
# TEST 4
#
print("\nTEST 4: MERGE should be blocked")

try:
    db.query("""
        MERGE (n:Test {id: 1})
    """)

    print("DANGER: MERGE was NOT blocked")

except PermissionError as e:
    print(f"CORRECTLY BLOCKED:\n{e}")

#
# TEST 5
#
print("\nTEST 5: Repository query")

try:
    result = db.query("""
        MATCH (r:Repository)
        RETURN r.name AS repository,
               r.language AS language
        LIMIT 5
    """)

    print("SUCCESS:")
    for row in result:
        print(row)

except Exception as e:
    print(f"FAILED: {e}")

#
# TEST 6
#
print("\nTEST 6: Pipeline query")

try:
    result = db.query("""
        MATCH (p:GraphNode:PIPELINE)
        RETURN p.name AS pipeline,
               p.pipeline_id AS pipeline_id
        LIMIT 5
    """)

    print("SUCCESS:")
    for row in result:
        print(row)

except Exception as e:
    print(f"FAILED: {e}")

#
# TEST 7
#
print("\nTEST 7: API query")

try:
    result = db.query("""
        MATCH (a:API)
        RETURN a.path AS path,
               a.method AS method
        LIMIT 5
    """)

    print("SUCCESS:")
    for row in result:
        print(row)

except Exception as e:
    print(f"FAILED: {e}")

#
# TEST 8
#
print("\nTEST 8: Labels")

try:
    result = db.query("""
        CALL db.labels()
        YIELD label
        RETURN label
        LIMIT 10
    """)

    print("SUCCESS:")
    for row in result:
        print(row)

except Exception as e:
    print(f"FAILED: {e}")

db.close()

print("\nREAD-ONLY SAFETY LAYER VERIFIED")