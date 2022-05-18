from bs4 import BeautifulSoup
from more_itertools import locate
import json

with open('lista de processos.txt', encoding='utf-8') as f:
    html_doc = f.read()
    # print(html_doc)

soup = BeautifulSoup(html_doc, 'html.parser')

gdp_table = soup.find("table")

gdp_table_data = gdp_table.find_all("th")

# Get all the headings of Lists
headings = []
for td in gdp_table_data:
    # remove any newlines and extra spaces from left and right
    headings.append(td.text.replace('\n', ' ').strip())

print(headings)

table_data = []
for tr in gdp_table.find_all("tr", attrs={"class": "rich-table-row"}): # find all tr's from table's tbody

    t_row = {}
    # Each table row is stored in the form of
    # find all td's(3) in tr and zip it with t_header
    for td in tr.find_all("td"): 
        t_row = td.text.replace('\n', '').strip()
        table_data.append(t_row)

position = list(locate(table_data, lambda x: x == ''))

data = []

for c, t in enumerate(table_data):
    # print(f'texto: {t}, e posição {c}')
    if '' == t:
        p = c-1
        c = c
        o = c+1
        d = c+2
        cs = c+3
        pa = c+4
        pp = c+5
        u = c+6

        data.append(f'{headings[0]}: {table_data[p]},'
        f'{headings[1]}: {table_data[c]},'
        f'{headings[2]}: {table_data[o]},'
        f'{headings[3]}: {table_data[d]},'
        f'{headings[4]}: {table_data[cs]},'
        f'{headings[5]}: {table_data[pa]},'
        f'{headings[6]}: {table_data[pp]},'
        f'{headings[7]}: {table_data[u]}'
        )
jsonStr = json.dumps(data, ensure_ascii=False)
print(jsonStr)