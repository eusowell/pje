from bs4 import BeautifulSoup
from more_itertools import locate
import json

with open('tabela.txt', encoding='utf-8') as f:
    html_doc = f.read()
    # print(html_doc)

soup = BeautifulSoup(html_doc, 'html.parser')

table = soup.find('table')

headers = [header.text for header in table.find_all('th')]
results = [{headers[i]: cell.text.replace('\n', '').strip() for i, cell in enumerate(row.find_all('td', attrs={"class": "linhaClara"}))}
           for row in table.find_all('tr')]

# attrs={"class": "linhaClara"}

results = list(filter(None, results))

jsonStr = json.dumps(results, ensure_ascii=False)
# print(jsonStr)

with open(f"table.json", 'w') as outfile:
    json.dump(results, outfile, ensure_ascii=False,  indent=4)


for r in results:
    if r['Tipo Documento'] == 'Contrarrazões - Apelação':
        print(r['Tipo Documento'])
    elif r['Tipo Documento'] == 'Protocolo - Contrarrazões - Recurso Apelação':
        print(r['Tipo Documento'])
        

tipo_doc = [r['Tipo Documento'] for r in results if r['Tipo Documento'] == 'Contrarrazões - Apelação']
# tipo_doc2 = [True for r in results if r['Tipo Documento'] == 'Protocolo - Contrarrazões' else False]

tipo_doc2 = [True if r['Tipo Documento'] == 'Protocolo - Contrarrazões - Recurso Apelação' else (True if r['Tipo Documento'] == 'Contrarrazões - Apelação' else False) for r in results]

resultado = 'ok' if tipo_doc2[0] == True else 'Verificar'

print(resultado)
print(tipo_doc2)