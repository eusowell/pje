from bs4 import BeautifulSoup

page = open('pje.txt', 'r')
soup = BeautifulSoup(page, 'html.parser')

div_tags = soup.find_all('div')
ids = []
for div in div_tags:
    ID = div.get('id')
    print(div)
    if ID is not None:
        ids.append(ID)
        print(ID)

test = [r['id'] for r in soup.find_all(name="a", attrs={"id": True})]

print(ids)
print(test)
num_id = []
for t in test:
    if 'jNp' in t:
        print(t)
        num_id.append(t)
print(len(num_id))
