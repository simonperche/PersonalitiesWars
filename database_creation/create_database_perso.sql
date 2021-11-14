CREATE TABLE Idol (
id INTEGER PRIMARY KEY,
url TEXT UNIQUE,
name TEXT);

-- 'Group' is a reserved name
CREATE TABLE Groups (
id INTEGER PRIMARY KEY,
name TEXT UNIQUE);

CREATE TABLE IdolGroups (
id_groups INTEGER,
id_idol INTEGER,
FOREIGN KEY (id_groups) REFERENCES Groups(id),
FOREIGN KEY (id_idol) REFERENCES Idol(id),
PRIMARY KEY (id_groups, id_idol));

CREATE TABLE Image (
url TEXT PRIMARY KEY,
id_idol INTEGER,
FOREIGN KEY (id_idol) REFERENCES Idol(id));