CREATE TABLE IF NOT EXISTS badges (id TEXT PRIMARY KEY, holder TEXT, zone_access TEXT, active INTEGER);
INSERT OR IGNORE INTO badges VALUES
 ('B001','agent.martin','operations',1),
 ('B002','admin.durand','administration,operations',1),
 ('B003','douane.leroy','douane',1),
 ('B004','surete.petit','surete,operations,douane,administration',1),
 ('B005','ancien.employe','operations',0);
