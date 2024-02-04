from nsdotpy.session import NSSession
import csv
import requests
from xml.etree import ElementTree as ET
import time


class Nation:
    def __init__(self, nation, bank):
        self.nation = nation
        self.bank = bank


def allocate_transfer_cards(occurrences_count, nations):
    nations_objects = [Nation(**nation) if isinstance(nation, dict) else nation for nation in nations]

    sorted_nations = sorted(nations_objects, key=lambda nation: nation.bank, reverse=True)

    for key, value in occurrences_count.items():
        card_id, season, worth = key
        copies = value

        for nation in sorted_nations:
            while copies > 0 and float(nation.bank) >= (float(worth) + 0.01):
                copies -= 1
                nation.bank = round(float(nation.bank) - float(worth), 2)
                yield {
                    "Nation": nation.nation,
                    "Worth": float(worth),
                    "CardID": card_id,
                    "Season": season,
                    "CopiesUsed": value - copies,
                    "BankAfterTransfer": round(float(nation.bank), 2)
                }


UA = input("Please enter your main nation: ")
UA = UA.lower().replace(' ', '_')
passy = input("Please enter that nation's password: ")
version = "1.0"
try:
    floor = float(input("Please enter the amount of bank you'd like left on puppets (Default 0): "))
    if floor < 0:
        raise ValueError("Negative value not allowed")
except ValueError:
    print("Invalid input. Setting default value to 0.")
    floor = 0

headers = {
    "User-Agent": f"Mass Transfer Tool/{version} (github: https://github.com/Thorn1000 ; user:{UA})"
}

occurrences_count = {}

csv_file_path = 'cards.csv'
with open(csv_file_path, 'r') as csv_file:
    reader = csv.reader(csv_file)
    card_info_list = list(reader)

csv_file_path_2 = 'nations.csv'
with open(csv_file_path_2, 'r') as csv_file:
    reader = csv.reader(csv_file)
    valid_nations = set()
    nation_dict = {}

    for row in reader:
        if len(row) == 2:
            processed_nation = row[0].lower().replace(' ', '_')
            if UA != processed_nation:   # make sure main nation isnt in .csv
                if processed_nation not in valid_nations:  # make sure there isnt a duplicate
                    nation_dict[processed_nation] = row[1]
                    valid_nations.add(processed_nation)
                else:
                    print(f"Warning: Duplicate entry found for {processed_nation}. Skipping.")
            else:
                print(f"Warning: Provied main nation {UA} and {processed_nation} provided in {csv_file_path_2} are the same. Dont put your main in there. Skipping.")

session = NSSession("Mass Transfer Tool", version, "Thorn1000", UA)

for entry in card_info_list:
    card_id, season, worth = entry[0], entry[1], entry[2]
    url = f"https://www.nationstates.net/cgi-bin/api.cgi?q=card+info+owners;cardid={card_id};season={season}"
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        xml_data = response.text
        root = ET.fromstring(xml_data)
        owners = [owner.text for owner in root.find('OWNERS')]

    else:
        print('Something blew up when trying to get card info')

    if owners:
        all_nations = owners
        total_occurrences = sum(all_nations.count(nation) for nation in valid_nations) + all_nations.count(UA)
        occurrences_count[(card_id, season, worth)] = total_occurrences
        all_nations = sorted(all_nations)

        for nations in all_nations:
            valid_nations = sorted(valid_nations)
            if nations in valid_nations:
                password = nation_dict[nations]
                if session.api_giftcard(nations, int(entry[0]), int(entry[1]), UA, password):
                    print(f"Gifted Card {entry[0]} (Season {entry[1]}) from {nations} to {UA}")
                else:
                    print("Something blew up while gifting. Try rerunning?")

for key, value in occurrences_count.items():
    card_id, season, worth = key
    print(f"Card {card_id} (Season {season}): Worth - {worth}, Total Occurrences - {value}")

print()

banky = []
total_nations = len(valid_nations)

for idx, nation in enumerate(valid_nations):
    url = f"https://www.nationstates.net/cgi-bin/api.cgi?q=cards+info;nationname={nation}"
    response = requests.get(url, headers=headers)
    time.sleep(0.65)

    if response.status_code == 200:
        xml_tree = ET.fromstring(response.text)
        bank_value = float(xml_tree.find(".//BANK").text)
        bank_value = round(bank_value, 2)
        bank_value = bank_value - floor
        banky.append({"nation": nation, "bank": bank_value})
        print(f"{idx + 1}/{total_nations} Nation: {nation} with Bank: {bank_value}")

print()

banky.sort(key=lambda x: x["bank"], reverse=True)

result = list(allocate_transfer_cards(occurrences_count, banky))

if session.login(UA, passy):
    for entry in result:
        nation = entry['Nation']
        worth = entry['Worth']
        card_id = entry['CardID']
        season = entry['Season']
        copies_used = entry['CopiesUsed']
        bank_after_transfer = entry['BankAfterTransfer']
        session.ask(str(worth), card_id, season)

print()

for entry in result:
    nation = entry['Nation']
    worth = entry['Worth']
    card_id = entry['CardID']
    season = entry['Season']
    copies_used = entry['CopiesUsed']
    bank_after_transfer = entry['BankAfterTransfer']

    password = nation_dict[nation]
    if session.login(nation,password):
        session.bid(str(worth),card_id,season)
