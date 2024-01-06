# printed-tree
Rough gec file from scanned pages inherited in a box of printed Family Tree Maker.  It is rough but potentially helpful to someone else getting started on the same.

My mother-in-law was her family's family tree enthusiast when she died we inherited binders of printed pages for thousands of names. 
I could not find any import for the structure available in programs that write gec files.  Decades since I've done any programming, this project was my learn-to-code with chatgpt.

How to use:

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
