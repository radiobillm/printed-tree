"""
For Family Tree Maker printouts to scan and import (the digital version is missing)
1. Scan pages with ScannerPro, crop left column with gender, crop empty rows
   rename file (say first name on first page), set recognize text, save pdf and .txt to Dropbox
2. From computer review .txt file
   for readability, use editor to remove double newlines, add three above Husband, two above Wife and Name
   mannually review to fix OCR problems, especially delimiters like Husband:
   manually move in:[location] sets (often scanned as a column) to their Husband/Wife/Name
3. Copy contents to family.txt and run this script csv-from-scan.py
4. Check places.csv (which must be in the same dir) for missing places,
   add fix column for any problems appended, run csv-from-scan again (or fix manually later)
   Save spouse2 list printed for use below (if any)
5. Open tree.csv with a spreadsheet
   look for any obvious problems, sometimes there is a blank row that will crash below unless removed
   format birth, death, marriage date colums as [dd mmm yyy] but ignore yyyy-only dates,  save tree.csv
6. Run gec-from-csv.py which reads tree.csv above and produces tree.gec
7. Use Family Tree Maker to import tree.gec
   Manually set spouse from the spouse2 list
   Look for duplicate people and merge or delete if isolated
   Fix single names (move from family to given)
   Use Tools/Resolve Place Names and fix problems
   Compare people in main tree, especially root to confirm name and birth date for later merge
   Review each scanned page, especially sex for ambigous names, and year-only dates (a bug)
   Export from Family Tree Maker as a GEDCOM file in tree-test.gec
8. Open tree-test.gec with RootMagic to find problems, but fix within Family Tree Maker
   run Tools Count number of trees to find isolated, normally a floating dupe to be deleted
   run Problem Search utility 
8. Close tree.ftm from Family Tree Maker, open moore.ftm with Family tree maker
9. Merge from tree.ftm
   Review merged names
   Delete tree.ftm to reuse same name for more sets of printed pages
10. Sync with Ancestry
   """

import re
import csv
import os
import datetime
import gender_guesser.detector as gender


def extract_family(text):
    family_range = []
    person_names = set()

    family_start = None
    family_end = None

    for idx, line in enumerate(text):
        if re.match(r'^Husband:', line, re.IGNORECASE):
            if family_start is not None:
                family_range.append((family_start, family_end))
            family_start = idx
        # Set family_end to the current index
        family_end = idx

    if family_start is not None:
        family_range.append((family_start, family_end + 1))

    return family_range


def extract_person(lines, family_start, family_end):
    person_range = []
    person_start = None
    person_end = None

    for idx, line in enumerate(lines[family_start:family_end], start=family_start):
        if re.match(r'^(Husband|Wife|Name):', line, re.IGNORECASE):
            if person_start is not None:
                person_range.append((person_start, person_end))
            person_start = idx
        # Set person_end to the current index
        person_end = idx

    if person_start is not None:
        person_range.append((person_start, person_end + 1))

    return person_range


def extract_details(lines, family_range):
    csv_data = []
    person_names = set()

    for family_start, family_end in family_range:
        for person_start, person_end in extract_person(lines, family_start, family_end):
            row = []  # Initialize an empty row for the person
            name = ''
            sex = ''
            born = ''
            birth_place = ''
            died = ''
            death_place = ''
            father = ''
            mother = ''
            spouse = ''
            spouse2 = ''
            husband = ''
            wife = ''
            married = ''
            marriage_place = ''

            for line in lines[person_start:person_end]:
                if line.startswith('Husband'):
                    name = line.split(':')[1].strip().title()
                    wife = get_wife(lines, family_start, family_end)
                    spouse = wife
                    sex = 'M'
                elif line.startswith('Wife'):
                    name = line.split(':')[1].strip().title()
                    husband = get_husband(lines, family_start, family_end)
                    spouse = husband
                    sex = 'F'
                elif line.startswith('Name:'):
                    name = line.split(':')[1].strip().title()
                    father = get_father(lines, family_start, family_end)
                    mother = get_mother(lines, family_start, family_end)
                elif line.startswith('Born:'):
                    born = convert_date(line.split(':')[1].strip())
                elif line.startswith('Died:'):
                    died = convert_date(line.split(':')[1].strip())
                elif line.startswith('Married:'):
                    married = convert_date(line.split(':')[1].strip())
                elif line.startswith('Father:'):
                    father = line.split(':')[1].strip().title()
                elif line.startswith('Mother:'):
                    mother = line.split(':')[1].strip().title()
                elif line.startswith('Spouse'):
                    spouses = line.split(':')[1].strip().split(',')
                    spouse = spouses[0].strip().title()
                    spouse2 = spouses[1].strip().title() if len(spouses) > 1 else ''
                elif line.startswith('Other Spouses:'):
                    spouse2 = line.split(':')[1].strip().title()
                elif line.startswith('in:'):
                    place = line.split(':', 1)[1].strip()
                    place = fix_place(place, places, add_places)
                    if birth_place == '':
                        birth_place = place
                    elif marriage_place == '':
                        marriage_place = place
                    elif death_place == '':
                        death_place = place

            if spouse2:
                print('Spouse2:', spouse2, ':  for :', name)

            csv_data.append([name, sex, born, birth_place, died, death_place, father, mother, spouse, spouse2, husband, wife, married, marriage_place])
 
    return csv_data


def get_wife(lines, family_start, family_end):
    wife = ''
    for current_line in lines[family_start:family_end]:
        if 'Wife:' in current_line:
            wife = current_line.split(':')[1].strip().title()
            break
    return wife


def get_husband(lines, family_start, family_end):
    husband = ''
    for current_line in lines[family_start:family_end]:
        if 'Husband:' in current_line:
            husband = current_line.split(':')[1].strip().title()
            break
    return husband


def get_father(lines, family_start, family_end):
    father = ''
    for current_line in lines[family_start:family_end]:
        if 'Husband:' in current_line:
            father = current_line.split(':')[1].strip().title()
            break
    return father


def get_mother(lines, family_start, family_end):
    mother = ''
    for current_line in lines[family_start:family_end]:
        if 'Wife:' in current_line:
            mother = current_line.split(':')[1].strip().title()
            break
    return mother


def determine_sex(name):
    d = gender.Detector()
    if ' ' in name:
        first_name = name.split()[0]
    else:
        first_name = name

    gender_guess = d.get_gender(first_name)

    if gender_guess == 'male' or gender_guess == 'mostly_male':
        return 'M'
    elif gender_guess == 'female' or gender_guess == 'mostly_female':
        return 'F'
    else:
        return 'M'


def convert_date(date_string):
    try:
        if date_string:
            date = datetime.datetime.strptime(date_string, '%B %d, %Y')
            formatted_date = date.strftime('%d %b %Y')
            return formatted_date
        else:
            return None
    except (ValueError, IndexError):
        return date_string

def add_missing_names(family_data):
    names_set = set([row[0] for row in family_data])  # Create a set of existing names in the table
    new_rows = []

    for row in family_data:
        if row[6] and row[6] not in names_set:  # Father
            new_row = [row[6]] + [''] * (len(row) - 1)
            new_rows.append(new_row)
            names_set.add(row[6])  # Update names_set with the new name
        if row[7] and row[7] not in names_set:  # Mother
            new_row = [row[7]] + [''] * (len(row) - 1)
            new_rows.append(new_row)
        if row[10] and row[10] not in names_set:  # Husband
            new_row = [row[10]] + [''] * (len(row) - 1)
            new_rows.append(new_row)
        if row[11] and row[11] not in names_set:  # Wife
            new_row = [row[11]] + [''] * (len(row) - 1)
            new_rows.append(new_row)
        if row[8] and row[8] not in names_set:  # Spouse
            new_row = [row[8]] + [''] * (len(row) - 1)
            new_rows.append(new_row)
        if row[9] and row[9] not in names_set:  # Spouse2
                new_row = [row[9]] + [''] * (len(row) - 1)
                new_rows.append(new_row)

    family_data.extend(new_rows)  # Append the new rows to family_data

    return family_data

def consolidate_names(family_data):
    consolidated_rows = []
    names_set = set()

    for row in family_data:
        name = row[0]

        if name not in names_set:
            consolidated_row = list(row)
            consolidated_rows.append(consolidated_row)
            names_set.add(name)
        else:
            for consolidated_row in consolidated_rows:
                if consolidated_row[0] == name:
                    for i in range(1, len(row)):
                        if row[i] and not consolidated_row[i]:
                            consolidated_row[i] = row[i]
                    break
    return consolidated_rows


def finish_for_tree(family_data):
    for index, row in enumerate(family_data):
        row.append('I' + str(index))  # Add unique ID as column 14

        if not row[1]: #guess gender from first name
            row[1] = determine_sex(row[0])
        
        if not row[10] and not row[11] and row[8]:  # no husband or wife but spouse
            if row[1] == 'M':
                row[11] = row[8]
            else:
                row[10] = row[8]
                
        if row[8]and row[10]: # copy wife marriage info to husband
            add_wife_info(row[10], row[0], row[12], row[13], family_data) 

        if row[6] and row[7]:
            marry_parents(row[6], row[7], family_data)  # assume Father and Mother are spouse

    return family_data


def add_wife_info(husband, wife, m_date, m_place, family_data): #set wife info for leaf husbands
    for row in family_data:
        if row[0] == husband and not row[11]: # found husband with no wife column
            row[11] = wife
            row[12] = m_date
            row[13] = m_place

    return family_data

def marry_parents(father, mother, family_data):
    for row in family_data:
        if not row[8]: #empty spouse
            if row[0] == mother:
                row[8] = father
                row[10] = father
            elif row[0] == father:
                row[8] = mother
                row[11] = mother

    return family_data


def fix_place(check_place, places, add_places):
    if check_place == '':
        return ''

    for row in places:
        if row[0] == check_place:
            return row[1]

    add_places.append([check_place, ''])
    return check_place


with open('places.csv', 'r', newline='') as csvfile:
    places = list(csv.reader(csvfile))
add_places = []

with open('family.txt', 'r') as file:
    text = file.readlines()
          
# Get the family block line range
family_range = extract_family(text)

# Extract individual names and details for each family
family_data = extract_details(text, family_range)

# Add names in a column not yet included as a row
family_data = add_missing_names(family_data)

# Consolidate multiple entries left
family_data = consolidate_names(family_data)

# set sex, missing relationships and add index
family_data = finish_for_tree(family_data)

header_row = ['Name', 'Sex', 'Born', 'Birth Place', 'Died', 'Death Place', 'Father', 'Mother', 'Spouse', 'Spouse2',
              'Husband', 'Wife', 'Married', 'Marriage Place', 'INDI']

csv_out = 'tree.csv'
with open(csv_out, 'w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(header_row)  # Write the header row
    writer.writerows(family_data)  # Write the consolidated table rows

print('Added to places.csv:', add_places)
with open('places.csv', 'a', newline='') as csvfile:
    csv.writer(csvfile).writerows(add_places)

