"""
Singleton classes representing databases.

These classes provide functions to access to data in personalities and member database.
"""

from __future__ import annotations

import sqlite3
from collections import defaultdict


class DatabasePersonality:
    __instance = None

    @staticmethod
    def get() -> DatabasePersonality:
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

    def get_all_personalities(self):
        """Return all personalities with [0] = name and [1] = group."""
        c = self.db.cursor()
        c.execute(f'''SELECT P.name, G.name
                             FROM Personality AS P
                             JOIN PersoGroups AS PG ON PG.id_perso = P.id
                             JOIN Groups AS G ON PG.id_groups = G.id''')
        personalities = c.fetchall()
        c.close()

        if not personalities:
            return None

        return [{'name': perso[0], 'group': perso[1]} for perso in personalities]

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

    def get_group_id(self, name):
        c = self.db.cursor()
        c.execute('''SELECT G.id FROM Groups AS G WHERE G.name = ? COLLATE NOCASE''', (name,))
        results = c.fetchone()
        c.close()

        return results[0] if results else None

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

    def get_perso_information(self, id_perso):
        """Return personality information with dict {name, group, image} format."""
        c = self.db.cursor()
        c.execute('''SELECT P.id, P.name, G.name
                     FROM Personality AS P
                     JOIN PersoGroups AS PG ON PG.id_perso = P.id
                     JOIN Groups AS G ON PG.id_groups = G.id
                     WHERE P.id = ?''', (id_perso,))
        perso = c.fetchone()
        c.close()

        if not perso:
            return None

        return {'id': perso[0], 'name': perso[1], 'group': perso[2]}

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

    def get_perso_all_images(self, id_perso):
        c = self.db.cursor()
        c.execute('''SELECT url
                     FROM Image
                     WHERE id_perso = ?''', (id_perso,))
        urls = c.fetchall()
        c.close()
        urls = [url[0] for url in urls]
        return sorted(urls)

    def add_personality(self, name, id_group, url):
        c = self.db.cursor()
        c.execute(''' INSERT OR IGNORE INTO Personality(name) VALUES (?) ''', (name,))
        id_perso = self.get_perso_id(name)
        c.execute(''' INSERT OR IGNORE INTO PersoGroups(id_groups, id_perso) VALUES (?, ?) ''',
                  (id_group, id_perso,))
        self.add_image(id_perso, url)
        self.db.commit()
        c.close()

    def remove_personality(self, id_perso):
        c = self.db.cursor()
        c.execute(''' DELETE FROM Personality WHERE id = ? ''', (id_perso,))
        c.execute(''' DELETE FROM PersoGroups WHERE id_perso = ? ''', (id_perso,))
        c.execute(''' DELETE FROM Image WHERE id_perso = ? ''', (id_perso,))
        self.db.commit()
        c.close()

        # TODO:  <<!! WARNING !!>> This does not handle multiple server <<!! WARNING !!>>
        # Quick dirty hack to not create multiple functions in DatabaseDeck
        c = DatabaseDeck.get().db.cursor()
        c.execute(''' DELETE FROM Deck WHERE id_perso = ? ''', (id_perso,))
        c.execute(''' DELETE FROM Wishlist WHERE id_perso = ? ''', (id_perso,))
        c.execute(''' DELETE FROM ShoppingList WHERE id_perso = ? ''', (id_perso,))
        c.execute(''' DELETE FROM BadgePerso WHERE id_perso = ? ''', (id_perso,))
        DatabaseDeck.get().db.commit()
        c.close()

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
    def get() -> DatabaseDeck:
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

    def get_servers_with_info_and_claims_channels(self):
        c = self.db.cursor()
        c.execute('''SELECT id, information_channel, claims_channel FROM Server 
                    WHERE information_channel IS NOT NULL and claims_channel IS NOT NULL''')
        res = c.fetchall()
        c.close()
        servers = []
        for server in res:
            servers.append({'id': server[0], 'information_channel': server[1], 'claims_channel': server[2]})

        return servers

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

    def set_information_channel(self, id_server, id_channel):
        self.create_server_if_not_exist(id_server)
        c = self.db.cursor()
        c.execute('''UPDATE Server
                     SET information_channel = ?
                     WHERE id = ?''', (id_channel, id_server))
        self.db.commit()
        c.close()

    def set_claims_channel(self, id_server, id_channel):
        self.create_server_if_not_exist(id_server)
        c = self.db.cursor()
        c.execute('''UPDATE Server
                     SET claims_channel = ?
                     WHERE id = ?''', (id_channel, id_server))
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

    def get_all_member(self, id_server):
        """Return a list of member."""
        c = self.db.cursor()
        c.execute('''SELECT id_member
                     FROM MemberInformation
                     WHERE id_server = ?''', (id_server,))
        ids = c.fetchall()
        c.close()
        return [id_member[0] for id_member in ids]

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

    def get_id_perso_profile(self, id_server, id_member):
        c = self.db.cursor()
        c.execute('''SELECT id_perso_profile
                     FROM MemberInformation
                     WHERE id_server = ? AND id_member = ?''', (id_server, id_member))
        id_perso_profile = c.fetchone()
        c.close()

        if not id_perso_profile:
            return None

        return id_perso_profile[0]

    def set_id_perso_profile(self, id_server, id_member, value):
        c = self.db.cursor()
        self.create_member_information_if_not_exist(id_server, id_member)
        c.execute('''UPDATE MemberInformation
                     SET id_perso_profile = ?
                     WHERE id_server = ? AND id_member = ?''', (value, id_server, id_member))
        self.db.commit()
        c.close()

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

    def add_to_shopping_list(self, id_server, id_perso, id_member):
        """Return true if success, false otherwise."""
        c = self.db.cursor()
        is_success = True

        try:
            c.execute('''INSERT
                         INTO ShoppingList(id_server, id_perso, id_member) 
                         VALUES (?,?,?)''', (id_server, id_perso, id_member))
        except sqlite3.IntegrityError:
            is_success = False
        self.db.commit()
        c.close()

        return is_success

    def remove_from_shopping_list(self, id_server, id_perso, id_member):
        """Return true if success, false otherwise."""
        c = self.db.cursor()

        # If the personality is not in wish list
        c.execute('''SELECT COUNT(*) FROM ShoppingList
                     WHERE id_server = ?
                     AND id_perso = ?
                     AND id_member = ?''', (id_server, id_perso, id_member))
        if c.fetchone()[0] == 0:
            c.close()
            return False

        c.execute('''DELETE FROM ShoppingList
                     WHERE id_server = ?
                     AND id_perso = ?
                     AND id_member = ?''', (id_server, id_perso, id_member))

        self.db.commit()
        c.close()

        return True

    def get_shopping_list(self, id_server, id_member):
        """Return wish list of personalities as ids array, or [] otherwise."""
        c = self.db.cursor()
        c.execute('''SELECT id_perso
                     FROM ShoppingList
                     WHERE id_server = ? AND id_member = ?''', (id_server, id_member))
        shopping_list = c.fetchall()
        c.close()

        shopping_list = [id_perso[0] for id_perso in shopping_list]

        return shopping_list

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

    def get_perso_current_image(self, id_server, id_perso):
        """Get the current url image associated to the personality (or the last one if bigger) or None if no images."""
        self.create_active_image_if_not_exist(id_server, id_perso)
        c = self.db.cursor()
        c.execute('''SELECT current_image
                     FROM Deck
                     WHERE id_server = ? AND id_perso = ?''', (id_server, id_perso))
        current_image = c.fetchone()[0]
        c.close()

        images = DatabasePersonality.get().get_perso_all_images(id_perso)
        if not images:
            return None

        current_image = min(len(images), current_image)

        return images[current_image]

    def add_badge(self, id_server, name, description=''):
        """Add a new badge to the server and return if the operation was successful"""
        try:
            c = self.db.cursor()
            c.execute(''' INSERT INTO Badge(id_server, name, description) 
                          VALUES (?, ?, ?) ''', (id_server, name, description,))
            self.db.commit()
            c.close()
        except sqlite3.IntegrityError as e:
            return False

        return True

    def remove_badge(self, id_badge):
        c = self.db.cursor()
        c.execute(''' DELETE FROM BadgePerso WHERE id_badge = ? ''', (id_badge,))
        c.execute(''' DELETE FROM Badge WHERE id = ? ''', (id_badge,))
        self.db.commit()
        c.close()

    def set_badge_description(self, id_badge, description):
        c = self.db.cursor()
        c.execute(''' UPDATE Badge SET description = ? WHERE id = ? ''', (description, id_badge,))
        self.db.commit()
        c.close()

    def set_badge_name(self, id_badge, new_name):
        c = self.db.cursor()
        c.execute(''' UPDATE Badge SET name = ? WHERE id = ? ''', (new_name, id_badge,))
        self.db.commit()
        c.close()

    def get_all_badges(self, id_server):
        c = self.db.cursor()
        c.execute('''SELECT id, name, description
                     FROM Badge
                     WHERE id_server = ?''', (id_server,))
        res = c.fetchall()
        c.close()

        badges = []
        for badge in res:
            badges.append({'id': badge[0], 'name': badge[1], 'description': badge[2]})

        return badges

    def get_all_badges_with_perso(self, id_server):
        c = self.db.cursor()
        c.execute('''SELECT B.name, BP.id_perso
                     FROM Badge as B
                     JOIN BadgePerso as BP ON BP.id_badge = B.id
                     WHERE B.id_server = ?''', (id_server,))
        res = c.fetchall()
        c.close()

        badges = defaultdict(list)
        for badge in res:
            badges[badge[0]].append(badge[1])

        return badges

    def get_id_badge(self, id_server, name):
        c = self.db.cursor()
        c.execute('''SELECT id
                     FROM Badge
                     WHERE id_server = ? AND name = ?''', (id_server, name,))
        badge = c.fetchone()
        c.close()

        if not badge:
            return None

        return badge[0]

    def get_badge_information(self, id_badge):
        c = self.db.cursor()
        c.execute('''SELECT name, description
                     FROM Badge
                     WHERE id = ?''', (id_badge,))
        badge = c.fetchone()
        c.close()

        if not badge:
            return None

        badge = {'name': badge[0], 'description': badge[1]}

        return badge

    def add_perso_to_badge(self, id_badge, id_perso):
        c = self.db.cursor()
        c.execute(''' INSERT OR IGNORE INTO BadgePerso(id_badge, id_perso) 
                              VALUES (?, ?) ''', (id_badge, id_perso,))
        self.db.commit()
        c.close()

    def remove_perso_from_badge(self, id_badge, id_perso):
        c = self.db.cursor()
        c.execute(''' DELETE FROM BadgePerso WHERE id_badge = ? AND id_perso = ? ''', (id_badge, id_perso,))
        self.db.commit()
        c.close()

    def get_badges_with(self, id_server, id_perso):
        c = self.db.cursor()
        c.execute('''SELECT B.id, B.name, B.description
                     FROM Badge as B
                     JOIN BadgePerso as BP ON BP.id_badge = B.id
                     WHERE B.id_server = ? AND BP.id_perso = ?''', (id_server, id_perso,))
        res = c.fetchall()
        c.close()

        badges = []
        for badge in res:
            badges.append({'id': badge[0], 'name': badge[1], 'description': badge[2]})

        return badges

    def get_perso_in_badge(self, id_badge):
        c = self.db.cursor()
        c.execute('''SELECT id_perso
                     FROM BadgePerso
                     WHERE id_badge = ?''', (id_badge,))
        id_persos = c.fetchall()
        c.close()

        return [id_perso[0] for id_perso in id_persos]
