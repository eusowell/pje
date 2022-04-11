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



configur = ConfigParser()
configur.read('config.ini')

# download the plugin
url = 'https://antcpt.com/anticaptcha-plugin.zip'
filehandle, _ = urllib.request.urlretrieve(url)
# unzip it
with zipfile.ZipFile(filehandle, "r") as f:
    f.extractall("plugin")

# set API key in configuration file
api_key = configur.get('captcha', 'api')
file = Path('./plugin/js/config_ac_api_key.js')
file.write_text(file.read_text().replace("antiCapthaPredefinedApiKey = ''", "antiCapthaPredefinedApiKey = '{}'".format(api_key)))

# zip plugin directory back to plugin.zip
zip_file = zipfile.ZipFile('./plugin.zip', 'w', zipfile.ZIP_DEFLATED)
for root, dirs, files in os.walk("./plugin"):
    for file in files:
        path = os.path.join(root, file)
        zip_file.write(path, arcname=path.replace("./plugin/", ""))
zip_file.close()

path_to_extension = os.path.abspath('./plugin')
user_data_dir = "./tmp/test-user-data-dir"

folha = configur.get('installation', 'folha')
path = configur.get('installation', 'dir_read')
pje = configur.get('installation', 'pje')

path_complete = os.path.abspath(path)
xlsx = pd.ExcelFile(path_complete)
PROCESSOS = []
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
    """

    if p[13:16] == '813':
        page.wait_for_selector('xpath=//*[@id="fPP:consultaSearchForm"]')
        page.fill('xpath=//*[@id="fPP:numeroProcesso:numeroSequencial"]', p[:7])
        page.fill('xpath=//*[@id="fPP:numeroProcesso:numeroDigitoVerificador"]', p[7:9])
        page.fill('xpath=//*[@id="fPP:numeroProcesso:ano"]', p[9:13])
        page.fill('xpath=//*[@id="fPP:numeroProcesso:numeroOrgaoJustica"]', p[16:])
    else:
        page.wait_for_selector('xpath=//*[@id="fPP:consultaSearchForm"]')
        page.fill('xpath=//*[@id="fPP:numeroProcesso:numeroSequencial"]', p[:7])
        page.fill('xpath=//*[@id="fPP:numeroProcesso:numeroDigitoVerificador"]', p[7:9])
        page.fill('xpath=//*[@id="fPP:numeroProcesso:Ano"]', p[9:13])
        page.fill('xpath=//*[@id="fPP:numeroProcesso:NumeroOrgaoJustica"]', p[16:])
    """
    page.click('xpath=//*[@id="fPP:searchProcessos"]')
    numero_formatado = f'{p[:7]}-{p[7:9]}.{p[9:13]}.{p[13:14]}.{p[14:16]}.{p[16:]}'
    with page.context.expect_page() as tab:
        page.wait_for_selector('xpath=//*[@id="fPP:processosTable:tb"]/tr')
        page.click(f'text={numero_formatado}')
        page.on("dialog", handle_dialog)

    handle_page(tab, p)


def run(playwright):
    chromium = playwright.chromium  # or "firefox" or "webkit".
    browser = chromium.launch_persistent_context(
        user_data_dir,
        headless=False,
        args=[
            f"--disable-extensions-except={path_to_extension}",
            f"--load-extension={path_to_extension}",
        ],
    )
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
    # //*[@id="username"]
    # //*[@id="username"]
    # //*[@id="btnEntrar"]
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
