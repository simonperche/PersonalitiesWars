"""
Singleton classes representing databases.

These classes provide functions to access to data in personalities and member database.
"""

import sqlite3


class DatabasePersonality:
    __instance = None

    @staticmethod
    def get():
        if DatabasePersonality.__instance is None:
            DatabasePersonality()
        return DatabasePersonality.__instance

    def __init__(self):
        """Virtually private constructor."""
        if DatabasePersonality.__instance is None:
            DatabasePersonality.__instance = self
            self.db = sqlite3.connect('./database_personality.db')

    def connect(self, filename):
        if self.db:
            self.db.close()
        self.db = sqlite3.connect(filename)

    def get_perso_ids_containing_name(self, name):
        c = self.db.cursor()
        c.execute('''SELECT P.id FROM Personality AS P WHERE P.name LIKE ? COLLATE NOCASE''', (f'%{name}%',))
        results = c.fetchall()
        c.close()

        ids = [r[0] for r in results]

        return ids

    def get_perso_id(self, name):
        c = self.db.cursor()
        c.execute('''SELECT P.id FROM Personality AS P WHERE P.name = ? COLLATE NOCASE''', (name,))
        results = c.fetchone()
        c.close()

        return results[0] if results else None

    def get_perso_images_count(self, id_perso):
        """Get images count of an personality."""
        c = self.db.cursor()
        c.execute('''SELECT COUNT(url) FROM Image
                    WHERE id_perso = ?''', (id_perso,))
        images_count = c.fetchone()[0]
        c.close()
        return images_count

    def get_perso_group_id(self, name, group):
        """Return the personality with name and group or None otherwise."""
        c = self.db.cursor()
        c.execute('''SELECT P.id FROM Personality AS P
                     JOIN PersoGroups AS PG ON PG.id_perso = P.id 
                     JOIN Groups AS G ON PG.id_groups = G.id
                     WHERE G.name = ? COLLATE NOCASE
                     AND P.name = ? COLLATE NOCASE''', (group, name))
        id_perso = c.fetchone()
        c.close()

        return id_perso[0] if id_perso else None

    def get_all_groups(self):
        """Return all groups."""
        c = self.db.cursor()
        c.execute('''SELECT G.name
                     FROM Groups AS G
                     ORDER BY G.name ASC''')
        results = c.fetchall()
        c.close()

        group = [r[0].title() for r in results]

        return group

    def get_group_members(self, group_name):
        """Return all group members with dict {name, members=[]}."""
        c = self.db.cursor()
        c.execute('''SELECT G.name, P.name FROM Personality AS P
                     JOIN PersoGroups AS PG ON PG.id_perso = P.id 
                     JOIN Groups AS G ON PG.id_groups = G.id
                     WHERE G.name LIKE ? COLLATE NOCASE
                     ORDER BY P.name ASC''', (f'%{group_name}%',))
        results = c.fetchall()
        c.close()

        group = {}

        if results:
            # Name is used to get the right case of the group
            group['name'] = results[0][0]
            group['members'] = [r[1] for r in results]

        return group

    def get_random_perso_id(self):
        """Return random personality id."""
        c = self.db.cursor()
        c.execute('''SELECT Personality.id
                     FROM Personality
                     ORDER BY RANDOM() LIMIT 1''')
        random_perso = c.fetchall()
        c.close()

        # first [0] for the number of result (here only 1 because LIMIT)
        # second [0] for the column in result (here only 1 -> Personality.id)
        return random_perso[0][0]

    def get_perso_information(self, id_perso, current_image):
        """Return personality information with dict {name, group, image} format."""
        c = self.db.cursor()
        c.execute('''SELECT P.id, P.name, G.name, Image.url
                     FROM Personality AS P
                     JOIN PersoGroups AS PG ON PG.id_perso = P.id
                     JOIN Groups AS G ON PG.id_groups = G.id
                     JOIN Image ON Image.id_perso = P.id
                     WHERE P.id = ?''', (id_perso,))
        perso = c.fetchall()
        c.close()

        if not perso:
            return None

        return {'id': perso[current_image][0], 'name': perso[current_image][1],
                'group': perso[current_image][2], 'image': perso[current_image][3]}

    def get_multiple_perso_information(self, ids_perso):
        """Return personalities information with dict {name, group} format."""
        c = self.db.cursor()
        c.execute(f'''SELECT P.id, P.name, G.name
                             FROM Personality AS P
                             JOIN PersoGroups AS PG ON PG.id_perso = P.id
                             JOIN Groups AS G ON PG.id_groups = G.id
                             WHERE P.id IN ({', '.join(['?' for _ in ids_perso])})''', ids_perso)
        personalities = c.fetchall()
        c.close()

        if not personalities:
            return None

        return [{'id': perso[0], 'name': perso[1],
                'group': perso[2]} for perso in personalities]

    def add_image(self, id_perso, url):
        c = self.db.cursor()
        c.execute(''' INSERT OR IGNORE INTO Image(url, id_perso) VALUES (?, ?) ''', (url, id_perso,))
        self.db.commit()
        c.close()

    def remove_image(self, id_perso, url):
        c = self.db.cursor()
        c.execute(''' DELETE FROM Image WHERE url = ? AND id_perso = ? ''', (url, id_perso,))
        self.db.commit()
        c.close()


class DatabaseDeck:
    __instance = None

    @staticmethod
    def get():
        if DatabaseDeck.__instance is None:
            DatabaseDeck()
        return DatabaseDeck.__instance

    def __init__(self):
        """Virtually private constructor."""
        if DatabaseDeck.__instance is None:
            DatabaseDeck.__instance = self
            self.db = sqlite3.connect('./database_deck.db')
            self.create_if_not_exist()

    def create_if_not_exist(self):
        c = self.db.cursor()
        # Query to check if the schema exists
        c.execute('''SELECT count(name) FROM sqlite_master WHERE type='table' AND name='Server' ''')

        if c.fetchone()[0] != 1:
            with open('create_database_deck.sql', 'r') as f:
                print("Creating database deck schema...")
                query = f.read()

                c = self.db.cursor()
                c.executescript(query)
                self.db.commit()
                c.close()

    def connect(self, filename):
        if self.db:
            self.db.close()
        self.db = sqlite3.connect(filename)

    def add_to_deck(self, id_server, id_perso, id_member):
        self.create_server_if_not_exist(id_server)
        self.create_member_if_not_exist(id_member)
        c = self.db.cursor()
        c.execute('''UPDATE Deck SET id_member = ? WHERE id_server = ? AND id_perso = ? ''',
                  (id_member, id_server, id_perso))
        # c.execute('''INSERT INTO Deck(id_server, id_perso, id_member)
        #             VALUES(?, ?, ?)''', (id_server, id_perso, id_member))
        self.db.commit()
        c.close()

        self.update_last_claim(id_server, id_member)

    def update_last_claim(self, id_server, id_member):
        c = self.db.cursor()
        c.execute('''INSERT OR IGNORE INTO MemberInformation(id_server, id_member)
                     VALUES (?, ?)''', (id_server, id_member))
        c.execute('''UPDATE MemberInformation
                     SET last_claim = datetime('now', 'localtime')
                     WHERE id_server = ? AND id_member = ?''', (id_server, id_member))
        self.db.commit()
        c.close()

    def get_server_configuration(self, id_server):
        self.create_server_if_not_exist(id_server)
        c = self.db.cursor()
        c.execute('''SELECT claim_interval, time_to_claim, rolls_per_hour FROM Server WHERE id = ?''', (id_server,))
        config = c.fetchone()
        c.close()

        return {'claim_interval': config[0], 'time_to_claim': config[1], 'rolls_per_hour': config[2]}

    def get_last_claim(self, id_server, id_member):
        """Return last claim date or -1 otherwise."""
        c = self.db.cursor()
        c.execute('''SELECT last_claim
                     FROM MemberInformation
                     WHERE id_server = ? AND id_member = ?''', (id_server, id_member))
        last_claim = c.fetchone()
        c.close()

        if not last_claim:
            return None

        return last_claim[0]

    def create_server_if_not_exist(self, id_server):
        c = self.db.cursor()
        c.execute('''INSERT OR IGNORE INTO Server(id) VALUES (?)''', (id_server,))
        self.db.commit()
        c.close()

    def create_member_if_not_exist(self, id_member):
        c = self.db.cursor()
        c.execute('''INSERT OR IGNORE INTO Member(id) VALUES (?)''', (id_member,))
        self.db.commit()
        c.close()

    def create_active_image_if_not_exist(self, id_server, id_perso):
        c = self.db.cursor()
        c.execute('''INSERT OR IGNORE INTO Deck(id_server, id_perso, current_image)
                     VALUES (?, ?, ?)''', (id_server, id_perso, 0))
        self.db.commit()
        c.close()

    def create_member_information_if_not_exist(self, id_server, id_member):
        c = self.db.cursor()
        c.execute('''INSERT OR IGNORE INTO MemberInformation(id_server, id_member)
                     VALUES (?, ?)''', (id_server, id_member))
        self.db.commit()
        c.close()

    def set_claiming_interval(self, id_server, interval):
        self.create_server_if_not_exist(id_server)
        c = self.db.cursor()
        c.execute('''UPDATE Server
                     SET claim_interval = ?
                     WHERE id = ?''', (interval, id_server))
        self.db.commit()
        c.close()

    def set_nb_rolls_per_hour(self, id_server, nb_rolls):
        self.create_server_if_not_exist(id_server)
        c = self.db.cursor()
        c.execute('''UPDATE Server
                     SET rolls_per_hour = ?
                     WHERE id = ?''', (nb_rolls, id_server))
        self.db.commit()
        c.close()

    def set_time_to_claim(self, id_server, time_to_claim):
        self.create_server_if_not_exist(id_server)
        c = self.db.cursor()
        c.execute('''UPDATE Server
                     SET time_to_claim = ?
                     WHERE id = ?''', (time_to_claim, id_server))
        self.db.commit()
        c.close()

    def set_max_wish(self, id_server, id_member, max_wish):
        c = self.db.cursor()
        self.create_member_information_if_not_exist(id_server, id_member)
        c.execute('''UPDATE MemberInformation
                     SET max_wish = ?
                     WHERE id_server = ? AND id_member = ?''', (max_wish, id_server, id_member))
        self.db.commit()
        c.close()

    def get_user_deck(self, id_server, id_member):
        """Return a list of personality ids."""
        c = self.db.cursor()
        c.execute('''SELECT id_perso
                     FROM Deck
                     WHERE id_server = ? AND id_member = ?''', (id_server, id_member))
        ids = c.fetchall()
        c.close()
        return [id_perso[0] for id_perso in ids]

    def get_last_roll(self, id_server, id_member):
        """Return last roll date or None otherwise."""
        c = self.db.cursor()
        c.execute('''SELECT last_roll
                     FROM MemberInformation
                     WHERE id_server = ? AND id_member = ?''', (id_server, id_member))
        last_roll = c.fetchone()
        c.close()

        if not last_roll:
            return None

        return last_roll[0]

    def update_last_roll(self, id_server, id_member):
        c = self.db.cursor()
        self.create_member_information_if_not_exist(id_server, id_member)
        c.execute('''UPDATE MemberInformation
                     SET last_roll = datetime('now', 'localtime')
                     WHERE id_server = ? AND id_member = ?''', (id_server, id_member))
        self.db.commit()
        c.close()

    def get_nb_rolls(self, id_server, id_member):
        c = self.db.cursor()
        c.execute('''SELECT nb_rolls
                     FROM MemberInformation
                     WHERE id_server = ? AND id_member = ?''', (id_server, id_member))
        nb_rolls = c.fetchone()
        c.close()

        if not nb_rolls:
            return 0

        return nb_rolls[0]

    def set_nb_rolls(self, id_server, id_member, value):
        c = self.db.cursor()
        self.create_member_information_if_not_exist(id_server, id_member)
        c.execute('''UPDATE MemberInformation
                     SET nb_rolls = ?
                     WHERE id_server = ? AND id_member = ?''', (value, id_server, id_member))
        self.db.commit()
        c.close()

    def get_rolls_per_hour(self, id_server):
        self.create_server_if_not_exist(id_server)
        c = self.db.cursor()
        c.execute('''SELECT rolls_per_hour FROM Server WHERE id = ?''', (id_server,))
        rolls_per_hour = c.fetchone()
        c.close()

        return rolls_per_hour[0]

    def get_time_to_claim(self, id_server):
        self.create_server_if_not_exist(id_server)
        c = self.db.cursor()
        c.execute('''SELECT time_to_claim FROM Server WHERE id = ?''', (id_server,))
        time_to_claim = c.fetchone()
        c.close()

        return time_to_claim[0]

    def perso_belongs_to(self, id_server, id_perso):
        """Return the owner of the personality or None otherwise."""
        c = self.db.cursor()
        c.execute('''SELECT id_member FROM Deck WHERE id_server = ? AND id_perso = ?''', (id_server, id_perso))
        owner = c.fetchone()
        c.close()

        if owner:
            owner = owner[0]

        return owner

    def add_to_wishlist(self, id_server, id_perso, id_member):
        """Return true if success, false otherwise."""
        c = self.db.cursor()
        is_success = True

        try:
            c.execute('''INSERT
                         INTO Wishlist(id_server, id_perso, id_member) 
                         VALUES (?,?,?)''', (id_server, id_perso, id_member))
        except sqlite3.IntegrityError:
            is_success = False
        self.db.commit()
        c.close()

        return is_success

    def remove_from_wishlist(self, id_server, id_perso, id_member):
        """Return true if success, false otherwise."""
        c = self.db.cursor()

        # If the personality is not in wish list
        c.execute('''SELECT COUNT(*) FROM Wishlist
                     WHERE id_server = ?
                     AND id_perso = ?
                     AND id_member = ?''', (id_server, id_perso, id_member))
        if c.fetchone()[0] == 0:
            c.close()
            return False

        c.execute('''DELETE FROM Wishlist
                     WHERE id_server = ?
                     AND id_perso = ?
                     AND id_member = ?''', (id_server, id_perso, id_member))

        self.db.commit()
        c.close()

        return True

    def get_max_wish(self, id_server, id_member):
        self.create_member_information_if_not_exist(id_server, id_member)
        c = self.db.cursor()
        c.execute('''SELECT max_wish
                     FROM MemberInformation
                     WHERE id_server = ? AND id_member = ?''', (id_server, id_member))
        max_wish = c.fetchone()[0]
        c.close()

        return max_wish

    def get_nb_wish(self, id_server, id_member):
        c = self.db.cursor()
        c.execute('''SELECT COUNT(id_perso)
                     FROM Wishlist
                     WHERE id_server = ? AND id_member = ?''', (id_server, id_member))
        nb_wish = c.fetchone()[0]
        c.close()

        return nb_wish

    def get_wishlist(self, id_server, id_member):
        """Return wish list of personalities as ids array, or [] otherwise."""
        c = self.db.cursor()
        c.execute('''SELECT id_perso
                     FROM Wishlist
                     WHERE id_server = ? AND id_member = ?''', (id_server, id_member))
        wishlist = c.fetchall()
        c.close()

        wishlist = [is_perso[0] for is_perso in wishlist]

        return wishlist

    def get_wished_by(self, id_server, id_perso):
        """Return wish list of users as ids array, or [] otherwise."""
        c = self.db.cursor()
        c.execute('''SELECT id_member
                     FROM Wishlist
                     WHERE id_server = ? AND id_perso = ?''', (id_server, id_perso))
        members = c.fetchall()
        c.close()

        members = [id_member[0] for id_member in members]

        return members

    def give_to(self, id_server, id_perso, id_giver, id_receiver):
        """Give an personality to another player."""
        c = self.db.cursor()
        c.execute('''UPDATE Deck
                     SET id_member = ?
                     WHERE id_server = ? AND
                           id_perso = ? AND
                           id_member = ?''', (id_receiver, id_server, id_perso, id_giver))
        self.db.commit()
        c.close()

    def update_perso_current_image(self, id_server, id_perso, current_image):
        c = self.db.cursor()
        c.execute('''UPDATE Deck
                     SET current_image = ?
                     WHERE id_server = ? AND id_perso = ?''', (current_image, id_server, id_perso))
        self.db.commit()
        c.close()

    def decrement_perso_current_image(self, id_server, id_perso):
        """Try to decrement the current image number."""
        self.create_active_image_if_not_exist(id_server, id_perso)
        current_image = self.get_perso_current_image(id_server, id_perso)
        if current_image > 0:
            current_image = current_image - 1
        else:
            image_count = DatabasePersonality.get().get_perso_images_count(id_perso)
            current_image = (image_count-1)

        self.update_perso_current_image(id_server, id_perso, current_image)
        return current_image

    def increment_perso_current_image(self, id_server, id_perso):
        """Try to increment the current image number."""
        self.create_active_image_if_not_exist(id_server, id_perso)
        current_image = self.get_perso_current_image(id_server, id_perso)
        image_count = DatabasePersonality.get().get_perso_images_count(id_perso)

        if current_image < (image_count-1):
            current_image = current_image + 1
        else:
            current_image = 0

        self.update_perso_current_image(id_server, id_perso, current_image)

        return current_image

    def get_perso_current_image(self, id_server, id_perso):
        """Get the current image associated to the personality."""
        self.create_active_image_if_not_exist(id_server, id_perso)
        c = self.db.cursor()
        c.execute('''SELECT current_image
                     FROM Deck
                     WHERE id_server = ? AND id_perso = ?''', (id_server, id_perso))
        current_image = c.fetchone()
        c.close()

        return current_image[0]
