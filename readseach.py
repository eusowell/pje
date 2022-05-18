from bs4 import BeautifulSoup


with open('pesquisa.txt') as f:
    html_doc = f.read()
    # print(html_doc)

soup = BeautifulSoup(html_doc, 'html.parser')

divs = soup.find_all("div", {"class": "form-group numero-processo"})
# print(divs)
"""
ids = []

for d in divs:
    for id in d.select('input[id]'):
        # print(id)
        ids.append(id['id'])
"""
print(len(divs))
#ids = [tag['id'] for tag in soup.select('input[id]')]
ids = [tag['id'] for tag in divs[0].select('input[id]')]

print(len(ids))

print(ids[0])
print(ids[1]) 
print(ids[2]) 
print(ids[3])
print(ids[4])
print(ids[5])


