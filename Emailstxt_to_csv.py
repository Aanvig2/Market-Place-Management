import re
import csv
import os

# this code helps to extract needed information from the emails and upload them into a csv file
def extract_info(email_text):
    name_pattern = r"Name:\s*(.+)"
    price_pattern = r"Price per unit:\s*\$?(\d+(\.\d+)?)"
    place_pattern = r"Place:\s*(.+)"
    time_pattern = r"Time required:\s*(\d+)\s*hours"
    offers_pattern = r"Offers:\s*(.+)"

    name = re.search(name_pattern, email_text)
    price = re.search(price_pattern, email_text)
    place = re.search(place_pattern, email_text)
    time = re.search(time_pattern, email_text)
    offers = re.search(offers_pattern, email_text)

    return {
        "name": name.group(1) if name else "",
        "price_per_unit": price.group(1) if price else "",
        "place": place.group(1) if place else "",
        "time_required": time.group(1) if time else "",
        "offers": offers.group(1) if offers else ""
    }

# Path containing txt email files
directory_path = ""

# Path to the output CSV file
csv_file = 'C:/Users/aanvi/Desktop/VS_code/Python/Fetchai/compiled.csv'

with open(csv_file, 'w', newline='') as csvfile:
    fieldnames = ['id', 'name', 'Price per unit', 'Place', 'Time required', 'Offers']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

    writer.writeheader()

    for i in range(27):
        email_file = f'C:/Users/aanvi/Desktop/VS_code/Python/Fetchai/Email_data/email_{i+1}.txt'
        with open(email_file, 'r') as file:
            email_text = file.read()
        info = extract_info(email_text)
        writer.writerow({
            'id': i + 1,
            'name': info['name'],
            'Price per unit': info['price_per_unit'],
            'Place': info['place'],
            'Time required': info['time_required'],
            'Offers': info['offers']
        })

print("Summary saved to", csv_file)

