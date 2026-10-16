// ==============================================================================
// FraudLens - Core Cypher Queries for Fraud Detection (FalkorDB)
// ==============================================================================

// 1. Create Constraints / Indexes (Speed up lookups)
CREATE INDEX FOR (u:User) ON (u.id);
CREATE INDEX FOR (a:Account) ON (a.id);
CREATE INDEX FOR (d:Device) ON (d.id);
CREATE INDEX FOR (ip:IPAddress) ON (ip.id);

// 2. Fetch Graph Overview Stats
MATCH (n)
RETURN labels(n) AS entity_type, count(n) AS count;

// 3. Detect Circular Money Routing (Money Muling Rings: 3 to 5 hops)
// Finds cycles where money flows from Account A -> B -> C -> A
MATCH path = (a1:Account)-[:TRANSFERRED_TO*3..5]->(a1:Account)
RETURN [n in nodes(path) | n.id] AS cycle_accounts,
       length(path) AS hop_count;

// 4. Detect Device Sharing Rings (Synthetic Identity / Account Takeover)
// Finds multiple distinct users logging in from the exact same physical device
MATCH (u1:User)-[:USED_DEVICE]->(d:Device)<-[:USED_DEVICE]-(u2:User)
WHERE u1.id < u2.id
RETURN d.id AS shared_device_id,
       d.device_type AS device_type,
       collect(DISTINCT u1.id) + collect(DISTINCT u2.id) AS associated_users,
       count(DISTINCT u1) + count(DISTINCT u2) AS user_count;

// 5. Detect IP Clustering (Multiple accounts routing from the same suspicious IP)
MATCH (u:User)-[:LOGGED_IN_FROM]->(ip:IPAddress)
WITH ip, collect(u.id) AS users, count(u) AS total_users
WHERE total_users > 1
RETURN ip.ip_address AS suspicious_ip,
       ip.is_vpn AS is_vpn,
       users,
       total_users
ORDER BY total_users DESC;

// 6. Inspect 360-degree Entity Graph for a Specific Account or User
MATCH (u:User {id: $user_id})-[r]-(connected)
RETURN u, r, connected;
