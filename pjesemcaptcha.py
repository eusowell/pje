from playwright.sync_api import sync_playwright
from playwright._impl._api_types import TimeoutError
import os
import pandas as pd
from time import sleep
from configparser import ConfigParser
from bs4 import BeautifulSoup

import urllib.request
import zipfile
from pathlib import Path
import json
from more_itertools import locate



configur = ConfigParser()
configur.read('config.ini')

folha = configur.get('installation', 'folha')
path = configur.get('installation', 'dir_read')
pje = configur.get('installation', 'pje')

doc = configur.get('documento', 'docs')

if doc == 'sim':
    DOCUMENTOS = []
    path_doc = configur.get('documento', 'dir_read_doc')
    path_complete_doc = os.path.abspath(path_doc)
    xlsx_doc = pd.ExcelFile(path_complete_doc)
    df_doc = pd.read_excel(xlsx_doc, folha)
    for d in range(len(df_doc)):
        DOCUMENTOS.append(df_doc.loc[d, 'DOCUMENTOS'])
else:
    PROCESSOS = []
    path_complete = os.path.abspath(path)
    xlsx = pd.ExcelFile(path_complete)
    df = pd.read_excel(xlsx, folha)
    for d in range(len(df)):
        PROCESSOS.append(df.loc[d, 'PROCESSOS'])


USERNAME = configur.get('login', 'username')
PASSWORD = configur.get('login', 'password')


def handle_dialog(dialog):
    message = dialog.message
    dialog.accept()


def handle_page(tab, n_processo):
    new_tab = tab.value
    # title = f"{numero_formatado} · Processo Judicial Eletrônico - 1º Grau"
    new_tab.wait_for_load_state()
    # print(new_tab.title())
    new_tab.click('xpath=//*[@id="divTimeLine"]/div[1]/div/div/div/a/i')
    filtro = '//*[@id="divTimeLine"]/div[1]/div/div/div/ul/li[2]/label'
    new_tab.wait_for_selector(f'xpath={filtro}')
    check = '//*[@id="divTimeLine:chkExibirDocumentos"]'
    new_tab.uncheck(f'xpath={check}')
    new_tab.click('xpath=//*[@id="divTimeLine"]/div[1]/div/div/div/a/i')

    andamentos = new_tab.inner_text('xpath=//*[@id="divTimeLine:divEventosTimeLine"]')
    texto = str(andamentos)

    new_tab.click('xpath=//*[@id="navbar"]/ul/li/a[1]')
    detalhe = '//*[@id="maisDetalhes"]'
    new_tab.wait_for_selector(f'xpath={detalhe}')

    destino = f'RESULTADO\\{n_processo}\\'
    if not os.path.exists(destino):
        os.makedirs(destino)

    conteudo = new_tab.inner_text('xpath=//*[@id="navbar"]/ul/li/ul')

    arquivo = open(f'{destino}/processo.txt', 'w')
    arquivo.writelines(conteudo)
    arquivo.close()

    timeline = texto

    arquivo = open(f'{destino}/andamento.txt', 'w')
    arquivo.writelines(timeline)
    arquivo.close()

    new_tab.screenshot(path="pje.png")
    sleep(1)
    new_tab.close()

def pesquisa_doc(page, tipo_doc, doc):
    print(f'Numero do doc: {doc}')
    page.check(f'xpath={tipo_doc}')
    assert page.is_checked(f'xpath={tipo_doc}')
    page.wait_for_selector('#fPP\:dpDec\:documentoParte')
    sleep(1)
    page.fill('#fPP\:dpDec\:documentoParte', doc)
    page.click('xpath=//*[@id="fPP:searchProcessos"]')
    # //*[@id="fPP:processosGridPanel"]
    sleep(2)
    page.wait_for_selector(
            'xpath=//*[@id="fPP:processosTable:tb"]',
            timeout=100*600
            )
    html = page.inner_html('xpath=//*[@id="fPP:processosGridPanel"]')
    soup = BeautifulSoup(html, 'html.parser')
    destino = f'RESULTADO\\{doc}\\'
    if not os.path.exists(destino):
        os.makedirs(destino)
    
    table = soup.find('table')

    headers = [header.text for header in table.find_all('th')]
    results = [{headers[i]: cell.text.replace('\n', '').strip() for i, cell in enumerate(row.find_all('td'))}
            for row in table.find_all('tr', attrs={"class": "rich-table-row"} )]

    results = list(filter(None, results))

    jsonStr = json.dumps(results, ensure_ascii=False)
    # print(jsonStr)

    with open(f"{destino}/data.json", 'w') as outfile:
        json.dump(results, outfile, ensure_ascii=False,  indent=4)

    """
    gdp_table = soup.find("table")
    headers = [header.text for header in table.find_all('th')]
    gdp_table_data = gdp_table.find_all("th")

    # Get all the headings of Lists
    headings = []
    for td in gdp_table_data:
        # remove any newlines and extra spaces from left and right
        headings.append(td.text.replace('\n', ' ').strip())
    
    table_data = []
    for tr in gdp_table.find_all("tr", attrs={"class": "rich-table-row"}): # find all tr's from table's tbody
        t_row = {}
        # Each table row is stored in the form of
        # find all td's(3) in tr and zip it with t_header
        for td in tr.find_all("td"): 
            t_row = td.text.replace('\n', '').strip()
            table_data.append(t_row)

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
    with open(f"{destino}/data.json", 'w') as outfile:
          json.dump(data, outfile, ensure_ascii=False)

    arquivo = open(f'{destino}/pesquisa_doc.txt', 'w')
    arquivo.writelines(data)
    arquivo.close()"""


def pesquisa(page, proc, html_doc):
    if type(proc) == str:
        p = proc
    else:
        p = str(proc)
    print(f'Numero {p}')

    soup = BeautifulSoup(html_doc, 'html.parser')
    divs = soup.find_all("div", {"class": "form-group numero-processo"})
    ids = [tag['id'] for tag in divs[0].select('input[id]')]

    numeroSequencial = ids[0]
    numeroDigitoVerificador = ids[1]
    ano = ids[2]
    respectivoTribunal = ids[4]
    numeroOrgaoJustica = ids[5]
    seq = p[:7]
    
    page.wait_for_selector('xpath=//*[@id="fPP:consultaSearchForm"]')
    page.fill(f'xpath=//*[@id="{numeroSequencial}"]', seq)
    page.fill(f'xpath=//*[@id="{numeroDigitoVerificador}"]', p[7:9])
    page.fill(f'xpath=//*[@id="{ano}"]', p[9:13])
    page.fill(f'xpath=//*[@id="{numeroOrgaoJustica}"]', p[16:])

    page.click('xpath=//*[@id="fPP:searchProcessos"]')
    numero_formatado = f'{p[:7]}-{p[7:9]}.{p[9:13]}.{p[13:14]}.{p[14:16]}.{p[16:]}'
    with page.context.expect_page() as tab:
        page.wait_for_selector('xpath=//*[@id="fPP:processosTable:tb"]/tr')
        page.click(f'text={numero_formatado}')
        page.on("dialog", handle_dialog)

    handle_page(tab, p)


def run(playwright):
    chromium = playwright.chromium  # or "firefox" or "webkit".
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    # stealth_sync(page)
    page.goto(pje)
    # page.on("requestfailed", lambda request: print(request.url + " " + request.failure.error_text))
    # other actions...
    # Interact with login form
    try:
        frame = page.frame('ssoFrame')
        frame.fill('xpath=//*[@id="username"]', USERNAME)
        frame.fill('xpath=//*[@id="password"]', PASSWORD)
        frame.click('xpath=//*[@id="kc-login"]')
    except:
        page.fill('xpath=//*[@id="username"]', USERNAME)
        page.fill('xpath=//*[@id="password"]', PASSWORD)
        page.click('xpath=//*[@id="btnEntrar"]')
    # Verify app is logged
    if page.is_visible('[class="rich-messages"]') == True:
        print(page.inner_text('[class=rich-messages]'))
        destino = f'RESULTADO\\'
        if not os.path.exists(destino):
            os.makedirs(destino)
        erro = f'Erro : {page.inner_text("[class=rich-messages]")}'
        print(f'Erro Apresentado: {erro}')
        arquivo = open(f'{destino}/erro.txt', 'w')
        arquivo.writelines(erro)
        arquivo.close()
        browser.close()
    else:
        print('logado')
    # page.locator('xpath=//*[@id="home"]').wait_for()
    page.wait_for_load_state(timeout=500*100)
    # Interact with a page
    page.click('xpath=//*[@id="barraSuperiorPrincipal"]/div/div[1]/ul/li/a')
    page.click('xpath=//*[@id="menu"]/div[2]/ul/li[2]')
    page.click('xpath=//*[@id="menu"]/div[2]/ul/li[2]/div/ul/li[4]')
    page.click('xpath=//*[@id="menu"]/div[2]/ul/li[2]/div/ul/li[4]/div/ul/li')
    page.wait_for_load_state(timeout=500*100)

    html = page.inner_html('xpath=//*[@id="fPP:consultaSearchForm"]')
    arquivo = open(f'pesquisa.txt', 'w')
    arquivo.writelines(html)
    arquivo.close()

    if doc == 'sim':
        for d in DOCUMENTOS:
            if type(d) == str:
                d = d
            else:
                d = str(d)
            size_doc = len(d)
            print(f'Tamanho do numero: {size_doc}')
            if size_doc <= 11:
                d = d.zfill(11)                
                ck = '//*[@id="cpf"]'
                pesquisa_doc(page, ck, d)
            else:
                d = d.zfill(14) 
                ck = '//*[@id="cnpj"]'
                pesquisa_doc(page, ck, d)
            page.reload()
            sleep(2)
            page.wait_for_load_state()
    else:

        for processo in PROCESSOS:
            print(f'Processo pesquisado: {processo}')
            try:
                pesquisa(page, processo, html)
            except TimeoutError:
                destino = f'RESULTADO\\{processo}\\'
                if not os.path.exists(destino):
                    os.makedirs(destino)
                erro = f'Erro pesquisa de processo: {processo}'
                print(f'Erro Apresentado: {erro}')
                arquivo = open(f'{destino}/erro.txt', 'w')
                arquivo.writelines(erro)
                arquivo.close()

            page.reload()
            sleep(2)
            page.wait_for_load_state()

    browser.close()


with sync_playwright() as p:
    run(p)
