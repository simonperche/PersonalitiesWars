import csv
import sys
import os

import sqlite3
from google_images_download import google_images_download
import sys
from io import BytesIO, TextIOWrapper
import multiprocessing
from joblib import delayed, Parallel
from nordvpn_switcher import initialize_VPN, rotate_VPN, terminate_VPN


def main():
    csv_filename = 'person_2020_update.csv'

    if not os.path.isfile(csv_filename):
        print("File error : ", csv_filename, " does not exist.")
        sys.exit(2)

    db = sqlite3.connect('./database_idol.db')

    c = db.cursor()
    # Query to check if the schema exists
    c.execute(''' SELECT count(name) FROM sqlite_master WHERE type='table' AND name='Idol' ''')

    if c.fetchone()[0] != 1:
        create_database_schema(db)

    c.close()

    if not populate_database(db, csv_filename):
        print("Error while populate database. Please check the integrity of csv file. 'database.db' remains unchanged.")
        sys.exit(2)

    print("Done.")


def create_database_schema(db):
    print("Creating database schema...")
    query = open('create_database.sql', 'r').read()

    c = db.cursor()
    c.executescript(query)
    db.commit()
    c.close()


def get_urls(search):
    old_stdout = sys.stdout
    sys.stdout = TextIOWrapper(BytesIO(), sys.stdout.encoding)

    response = google_images_download.googleimagesdownload()

    arguments = {"keywords": search,
                 "limit": 5,
                 "print_urls": True,
                 "no_download": True
                 }
    paths = response.download(arguments)
    sys.stdout.seek(0)
    output = sys.stdout.read()

    sys.stdout.close()
    sys.stdout = old_stdout

    urls = []
    for line in output.split("\n"):
        if line.startswith("Image URL:"):
            line = line.replace("Image URL: ", "")
            urls.append(line)

    print(search)
    print(urls)
    print()

    return urls


def populate_database(db, csv_filename):
    print("Populating database...")
    people = []

    with open(csv_filename, 'r', encoding="utf8") as csvfile:
        reader = csv.reader(csvfile, delimiter=',', quotechar='"')
        for line in reader:
            line = list(line)
            people.append([line[4], line[5]])

    people = people[1:]
    print(len(people))

    settings = initialize_VPN(stored_settings=True)

    step = 10
    for i in range(0, 10, step):
        rotate_VPN(settings)

        start = i
        end = i+step

        urls_people = Parallel(n_jobs=16)(delayed(get_urls)(f'{person[0]} {person[1]}') for person in people[start:end])

        c = db.cursor()

        id_idol = start+1
        for person in people[start:end]:
            print(f'{id_idol} : {person[0]}')
            c.execute(''' INSERT OR IGNORE INTO Idol(id, name) VALUES (?, ?) ''', (id_idol, person[0],))

            c.execute(''' INSERT OR IGNORE INTO Groups(name) VALUES (?) ''', (person[1],))
            c.execute(''' SELECT id FROM Groups WHERE name = ? ''', (person[1],))
            id_group = c.fetchone()

            if not id_group:
                return False

            id_group = id_group[0]

            c.execute(''' INSERT OR IGNORE INTO IdolGroups(id_idol, id_groups) VALUES (?, ?) ''', (id_idol, id_group,))

            for url in urls_people[id_idol-start-1]:
                c.execute(''' INSERT OR IGNORE INTO Image(url, id_idol) VALUES (?, ?) ''', (url, id_idol,))

            id_idol += 1

            # if id_idol % 1000 == 0:
            #     db.commit()

        db.commit()

        c.close()

    terminate_VPN(settings)

    return True


if __name__ == "__main__":
    main()
