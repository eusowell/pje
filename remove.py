from bs4 import BeautifulSoup
import pandas as pd


with open('comarcas.txt', encoding='utf-8') as f:
    html_doc = f.read()
    # print(html_doc)

soup = BeautifulSoup(html_doc, 'html.parser')


soup.select('option[value]')

items = soup.select('option[value]')
values = [item.get('value') for item in items]
textValues = [item.text for item in items]

print(values)
print(textValues)

data = list(zip(items, values, textValues))

df = pd.DataFrame(data, columns=["Itens", "Número Comarca", "Nome Comarca"]) 
with pd.ExcelWriter("comarcas MT.xlsx") as writer:
    df.to_excel(writer)
