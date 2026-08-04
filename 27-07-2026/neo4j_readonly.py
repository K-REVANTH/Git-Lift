# neo4j_readonly.py

"""
READ-ONLY Neo4j connection wrapper.
Prevents any accidental writes to the database.
"""

import re
from neo4j import GraphDatabase


# Cypher keywords that MODIFY data — these are BANNED
FORBIDDEN_KEYWORDS = [
    r"\bCREATE\b",
    r"\bDELETE\b",
    r"\bDETACH\s+DELETE\b",
    r"\bMERGE\b",
    r"\bSET\b",
    r"\bREMOVE\b",
    r"\bDROP\b",
    r"\bLOAD\s+CSV\b",
    r"\bFOREACH\b",
    r"\bINSERT\b",

    # Schema changes
    r"\bCREATE\s+INDEX\b",
    r"\bDROP\s+INDEX\b",
    r"\bCREATE\s+CONSTRAINT\b",
    r"\bDROP\s+CONSTRAINT\b",

    # APOC write procedures
    r"\bCALL\s+APOC\..*CREATE\b",
    r"\bCALL\s+APOC\..*MERGE\b",
    r"\bCALL\s+APOC\..*DELETE\b",
    r"\bCALL\s+APOC\..*REMOVE\b",

    # Generic write procedures
    r"\bCALL\s+.*\.(CREATE|DELETE|MERGE|WRITE)\b",
]


class ReadOnlyNeo4j:
    """
    Safety wrapper around the Neo4j driver.
    Only allows read-only queries.
    """

    def __init__(self, uri, username, password):
        self.driver = GraphDatabase.driver(
            uri,
            auth=(username, password)
        )

        self.driver.verify_connectivity()

        print(f"[OK] Connected to Neo4j @ {uri} (READ-ONLY)")

    def close(self):
        self.driver.close()

    def _validate_query(self, query: str):
        """
        Reject any query containing write keywords.
        """

        query_upper = query.upper()

        for pattern in FORBIDDEN_KEYWORDS:
            if re.search(pattern, query_upper, re.IGNORECASE):
                raise PermissionError(
                    "\nWRITE OPERATION BLOCKED!\n"
                    f"Forbidden pattern: {pattern}\n"
                    f"Query: {query[:200]}"
                )

        return True

    def query(self, cypher: str, params: dict = None):
        """
        Execute a READ-ONLY Cypher query.
        """

        self._validate_query(cypher)

        with self.driver.session(
            default_access_mode="READ"
        ) as session:

            result = session.run(
                cypher,
                params or {}
            )

            return [record.data() for record in result]