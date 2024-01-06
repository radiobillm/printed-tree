"""run after csv-from-scan.py which explains the process."""
import re
import csv


def generate_gedcom(rows):
    individuals = []
    marriages = []
    families = set()

    for i, row in enumerate(rows, start=1):
        individuals.extend(generate_individual(i, row))
        marriages.extend(generate_marriage_gedcom(row))
        families.add(row[14])  # Add individual ID to families set

    header = [
        '0 HEAD',
        '1 SOUR FTM',
        '2 VERS 24.2',
        '2 NAME Family Tree Maker',
        '1 CHAR UTF-8',
        '1 SUBM @SUBM@',
        '1 GEDC',
        '2 VERS 5.5.1',
        '2 FORM LINEAGE-LINKED',
        '0 @SUBM@ SUBM'
    ]

    gedcom_lines = header + individuals + marriages + ['0 TRLR']
    return '\n'.join(gedcom_lines)


def generate_individual(individual_id, row):
    gedcom_lines = []
    gedcom_lines.append(f'0 @{row[14]}@ INDI')  # Using '@' before and after the individual ID
    given_name, family_name, nickname = extract_name_components(row[0])
    gedcom_lines.append(f'1 NAME {given_name} /{family_name}/')
    if nickname:
        gedcom_lines.append(f'2 NICK {nickname}')
    gedcom_lines.append(f'1 SEX {row[1]}')  # Using 'Sex' column for SEX
    if row[2]:
        gedcom_lines.append(f'1 BIRT')
        gedcom_lines.append(f'2 DATE {row[2]}')  # Using 'Born' column for DATE
        if row[3]:
            gedcom_lines.append(f'2 PLAC {row[3]}')  # Using 'Birth Place' column for PLAC
    if row[4]:
        gedcom_lines.append(f'1 DEAT')
        gedcom_lines.append(f'2 DATE {row[4]}')  # Using 'Died' column for DATE
        if row[5]:
            gedcom_lines.append(f'2 PLAC {row[5]}')  # Using 'Death Place' column for PLAC
    return gedcom_lines


def extract_name_components(name):
    # Extract the family name
    print(name)
    name_parts = name.split()
    family_name = name_parts[-1]

    # Extract the given name parts
    given_name_parts = name_parts[:-1]
    given_name_parts_without_nickname = [part for part in given_name_parts if not re.match(r'".*"', part)]
    given_name = ' '.join(given_name_parts_without_nickname)

    # Extract the nickname if present
    nickname = ''
    if '"' in name:
        nickname_match = re.search(r'"([^"]+)"', name)
        if nickname_match:
            nickname = nickname_match.group(1)

    return given_name, family_name, nickname


def generate_marriage_gedcom(row):
    husband_id = row[14]
    husband_name = row[10]
    wife_name = row[11]
    married_date = row[12]
    marriage_place = row[13]
    # marriage info stored with husband record
    if wife_name:
        gedcom_lines = []
        wife_id = next((r[14] for r in rows if r[0] == wife_name), None)  # Find the wife ID
        if wife_id:
            fam_id = f'@{husband_id}F01@'  # Generate a unique FAM identifier (assuming only one marriage per husband)
            gedcom_lines.append(f'0 {fam_id} FAM')
            gedcom_lines.append(f'1 HUSB @{husband_id}@')
            gedcom_lines.append(f'1 WIFE @{wife_id}@')
            gedcom_lines.append('1 MARR')
            if married_date:
                gedcom_lines.append(f'2 DATE {married_date}')  # Add the marriage date
            if marriage_place:
                gedcom_lines.append(f'2 PLAC {marriage_place}')  # Add the marriage place

            # Find and add children
            children = [r for r in rows if r[7] == wife_name]  # Find all rows where the wife is a mother
            for child in children:
                child_id = child[14]
                gedcom_lines.append(f'1 CHIL @{child_id}@')

        else:
            print(f"Wife not found: '{wife_name}'")

        return gedcom_lines
    else:
        return []


def generate_family_gedcom(row):
    husband_id = row[14]
    husband_name = row[0]
    wife_id = next((r[14] for r in rows if r[0] == row[7]), None)  # Find the wife ID with the corresponding wife name
    married_date = row[12]  # Assuming married date is in column 12
    marriage_place = row[13]  # Assuming marriage place is in column 13

    if wife_id:
        fam_id = f'@{husband_id}F01@'  # Generate a unique FAM identifier (assuming only one marriage per husband)
        gedcom_lines = [
            f'0 {fam_id} FAM',
            f'1 HUSB @{husband_id}@',
            f'1 WIFE @{wife_id}@',
            '1 MARR'
        ]
        if married_date:
            gedcom_lines.append(f'2 DATE {married_date}')  # Add the marriage date
        if marriage_place:
            gedcom_lines.append(f'2 PLAC {marriage_place}')  # Add the marriage place

        return gedcom_lines
    else:
        return []


# Read the CSV file
with open('tree.csv', 'r') as file:
    reader = csv.reader(file)
    header = next(reader)
    rows = list(reader)

# Generate the GEDCOM
gedcom = generate_gedcom(rows)

# Write the GEDCOM to a file
with open('tree.ged', 'w') as file:
    file.write(gedcom)
