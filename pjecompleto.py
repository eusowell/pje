from playwright.async_api import async_playwright
import asyncio

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
head = configur.get('Headless', 'headless')
file = configur.get('files', 'file')


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


def openbrowser():
    if head == 'True':
        return True
    else:
        return False


async def handle_dialog(dialog):
    print(dialog.message)
    await dialog.accept()

async def downloads_files(page, destino):

    # #navbar\:downloadProcesso
    async with page.expect_download() as download_info:
        await page.locator("#navbar\:downloadProcesso").click()
        page.on("dialog", handle_dialog)
        await page.locator("#navbar\:downloadProcesso").click()
    download = await download_info.value
    # waits for download to complete
    path = await download.path()
    # name file
    file_name = download.suggested_filename

    destination_folder_path = f"{destino}/"
    await download.save_as(os.path.join(destination_folder_path, file_name))


async def handle_page(tab, n_processo):
    new_tab = await tab.value
    # title = f"{numero_formatado} · Processo Judicial Eletrônico - 1º Grau"
    await new_tab.wait_for_load_state()
    destino = f'RESULTADO\\{n_processo}\\'
    if not os.path.exists(destino):
        os.makedirs(destino)
    
    if file == 'sim':
        await new_tab.click('xpath=//*[@id="navbar:ajaxPanelAlerts"]/ul[2]/li[5]/a')
        await downloads_files(new_tab, destino)
    
    # print(new_tab.title())
    await new_tab.click('xpath=//*[@id="divTimeLine"]/div[1]/div/div/div/a/i')
    filtro = '//*[@id="divTimeLine"]/div[1]/div/div/div/ul/li[2]/label'
    await new_tab.wait_for_selector(f'xpath={filtro}')
    check = '//*[@id="divTimeLine:chkExibirDocumentos"]'
    await new_tab.uncheck(f'xpath={check}')
    await new_tab.click('xpath=//*[@id="divTimeLine"]/div[1]/div/div/div/a/i')

    andamentos = await new_tab.inner_text('xpath=//*[@id="divTimeLine:divEventosTimeLine"]')
    texto = str(andamentos)

    await new_tab.click('xpath=//*[@id="navbar"]/ul/li/a[1]')
    detalhe = '//*[@id="maisDetalhes"]'
    await new_tab.wait_for_selector(f'xpath={detalhe}')
  
    conteudo = await new_tab.inner_text('xpath=//*[@id="navbar"]/ul/li/ul')

    arquivo = open(f'{destino}/processo.txt', 'w')
    arquivo.writelines(conteudo)
    arquivo.close()

    timeline = texto

    arquivo = open(f'{destino}/andamento.txt', 'w')
    arquivo.writelines(timeline)
    arquivo.close()

    await new_tab.screenshot(path="pje.png")
    sleep(1)
    await new_tab.close()

async def pesquisa_doc(page, tipo_doc, doc):
    print(f'Numero do doc: {doc}')
    await page.check(f'xpath={tipo_doc}')
    assert await page.is_checked(f'xpath={tipo_doc}') is True
    await page.wait_for_selector('#fPP\:dpDec\:documentoParte')
    await page.click('#fPP\:dpDec\:documentoParte')
    await page.fill('#fPP\:dpDec\:documentoParte', doc)
    await page.click('xpath=//*[@id="fPP:searchProcessos"]')
    # //*[@id="fPP:processosGridPanel"]
    sleep(2)
    await page.wait_for_selector(
            'xpath=//*[@id="fPP:processosTable:tb"]',
            timeout=100*600
            )
    html = await page.inner_html('xpath=//*[@id="fPP:processosGridPanel"]')
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


async def pesquisa(page, proc, html_doc):
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
    
    await page.wait_for_selector('xpath=//*[@id="fPP:consultaSearchForm"]')
    await page.fill(f'xpath=//*[@id="{numeroSequencial}"]', seq)
    await page.fill(f'xpath=//*[@id="{numeroDigitoVerificador}"]', p[7:9])
    await page.fill(f'xpath=//*[@id="{ano}"]', p[9:13])
    await page.fill(f'xpath=//*[@id="{numeroOrgaoJustica}"]', p[16:])

    await page.click('xpath=//*[@id="fPP:searchProcessos"]')
    numero_formatado = f'{p[:7]}-{p[7:9]}.{p[9:13]}.{p[13:14]}.{p[14:16]}.{p[16:]}'
    async with page.context.expect_page() as tab:
        await page.wait_for_selector('xpath=//*[@id="fPP:processosTable:tb"]/tr')
        await page.click(f'text={numero_formatado}')
        page.on("dialog", handle_dialog)

    await handle_page(tab, p)

 
async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=openbrowser())
        context = await browser.new_context(accept_downloads=True)
        page = await context.new_page()
        await page.goto(pje)
        # Interact with login form
        try:
            frame = await page.frame('ssoFrame')
            await frame.fill('xpath=//*[@id="username"]', USERNAME)
            await frame.fill('xpath=//*[@id="password"]', PASSWORD)
            await frame.click('xpath=//*[@id="kc-login"]')
        except:
            await page.fill('xpath=//*[@id="username"]', USERNAME)
            await page.fill('xpath=//*[@id="password"]', PASSWORD)
            await page.click('xpath=//*[@id="btnEntrar"]')
        # Verify app is logged
        if await page.is_visible('[class="rich-messages"]') == True:
            print(await page.inner_text('[class=rich-messages]'))
            destino = f'RESULTADO\\'
            if not os.path.exists(destino):
                os.makedirs(destino)
            erro = f'Erro : {await page.inner_text("[class=rich-messages]")}'
            print(f'Erro Apresentado: {erro}')
            arquivo = open(f'{destino}/erro.txt', 'w')
            arquivo.writelines(erro)
            arquivo.close()
            browser.close()
        else:
            print('logado')
        # page.locator('xpath=//*[@id="home"]').wait_for()
        await page.wait_for_load_state(timeout=500*100)
        # Interact with a page
        await page.click('xpath=//*[@id="barraSuperiorPrincipal"]/div/div[1]/ul/li/a')
        await page.click('xpath=//*[@id="menu"]/div[2]/ul/li[2]')
        await page.click('xpath=//*[@id="menu"]/div[2]/ul/li[2]/div/ul/li[4]')
        await page.click('xpath=//*[@id="menu"]/div[2]/ul/li[2]/div/ul/li[4]/div/ul/li')
        await page.wait_for_load_state(timeout=500*100)

        html = await page.inner_html('xpath=//*[@id="fPP:consultaSearchForm"]')
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
                    await pesquisa_doc(page, ck, d)
                else:
                    d = d.zfill(14) 
                    ck = '//*[@id="cnpj"]'
                    await pesquisa_doc(page, ck, d)
                await page.reload()
                sleep(2)
                await page.wait_for_load_state()
        else:

            for processo in PROCESSOS:
                print(f'Processo pesquisado: {processo}')
                try:
                    await pesquisa(page, processo, html)
                except TimeoutError:
                    destino = f'RESULTADO\\{processo}\\'
                    if not os.path.exists(destino):
                        os.makedirs(destino)
                    erro = f'Erro pesquisa de processo: {processo}'
                    print(f'Erro Apresentado: {erro}')
                    arquivo = open(f'{destino}/erro.txt', 'w')
                    arquivo.writelines(erro)
                    arquivo.close()

                await page.reload()
                sleep(2)
                await page.wait_for_load_state()


        await context.close()
        await browser.close()
 
if __name__ == '__main__':
    asyncio.run(main())