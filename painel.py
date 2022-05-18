from playwright.sync_api import sync_playwright
from random import randint
from time import sleep
from configparser import ConfigParser
from pathlib import Path
from datetime import date, timedelta
from workalendar.america import BrazilBeloHorizonteCity
import os
import urllib.request
import zipfile
from bs4 import BeautifulSoup as bs

dias = ('Segunda-feira', 'Terça-feira', 'Quarta-feira', 'Quinta-feira', 'Sexta-feira', 'Sábado', 'Domingo')

hoje = date.today()
cal = BrazilBeloHorizonteCity()


def delay():
    t = randint(1, 5)
    sleep(t)


# data
def diasUteis(today):
    offset = max(1, (today.weekday() + 6) % 7 - 3)
    day_work = timedelta(offset)
    most_recent = today - day_work
    dia_semana = date.weekday(most_recent)
    # print(f'O dia da semana do def é : {dias[dia_semana]}')

    return most_recent


# verifica feriado
def feriado(data):
    if not cal.is_working_day(data):
        most_recent = diasUteis(data)
        dia_semana = date.weekday(most_recent)
        # print(f'O dia da semana do if é : {dias[dia_semana]}')
        # print(f'dia util :{most_recent}')
        return most_recent
    else:
        dia_semana = date.weekday(data)
        # print(f'O dia da semana é do else: {dias[dia_semana]}')
        # print(f'dia util :{data}')
        return data


configur = ConfigParser()
configur.read('config.ini')

api = configur.get('captcha', 'api')


# download the plugin
url = 'https://antcpt.com/anticaptcha-plugin.zip'
filehandle, _ = urllib.request.urlretrieve(url)
# unzip it
with zipfile.ZipFile(filehandle, "r") as f:
    f.extractall("plugin")

# set API key in configuration file
api_key = api
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
user_data_dir = "/tmp/test-user-data-dir"

folha = configur.get('installation', 'folha')
path = configur.get('installation', 'dir_read')
pje = configur.get('installation', 'pje')

USERNAME = configur.get('login', 'username')
PASSWORD = configur.get('login', 'password')


# lista items
def listaitems(xpath, pg):
    all_items = pg.query_selector_all(f'xpath={xpath}')
    tr_counts = []
    for item in all_items:
        name_el = item.query_selector('tr')
        rows = name_el.inner_text()
        tr_counts.append(rows)
    # print(tr_counts)
    return tr_counts


# clica em cada comarca
def click(xpath, pg):
    # print(f'Elemnto:\n {xpath}')
    titulo = pg.inner_text(f'xpath={xpath}')
    titulo.replace('\n', '')
    # print(f'Nome da comarca {titulo} \ntamanho da lista {len(titulo)}')
    pg.wait_for_selector(f'xpath={xpath}', timeout=50000)
    pg.click(f'xpath={xpath}')
    pg.wait_for_selector(f'xpath=//*[@id=formExpedientes:Filtros')


# clica na lupa
def bt_pesquisa(p):
    p.wait_for_selector('xpath=//*[@id="formExpedientes:Filtros"]/div/div[2]/ul/li[4]/a/i', timeout=30000)
    p.click('xpath=//*[@id="formExpedientes:Filtros"]/div/div[2]/ul/li[4]/a/i')


# botao input
def psq(dt_input, p):
    input_data = '/html/body/div[6]/div/div/div/div[2]/table/tbody/tr[2]' \
                 '/td/table/tbody/tr/td/div[4]/div/div/form/div[1]/div/div' \
                 '/div[2]/ul/li[4]/div/div[2]/div[3]/div/span[1]/input[1]'
    p.fill(f'xpath={input_data}', dt_input.strftime('%d/%m/%Y'))


# botao pesquisa
def psq_bt(p):
    p.wait_for_selector('xpath=//*[@id="formExpedientes:btPesq"]')
    p.click('xpath=//*[@id="formExpedientes:btPesq"]')
    p.wait_for_selector('xpath=//*[@id="formExpedientes:conteudoPesquisaExpedientes"]', timeout=50000)
    sleep(2)


# Lista as linhas
def listarows(xpath, pg):
    linhas = pg.query_selector_all(f'xpath={xpath}')
    qtd = len(linhas)
    # print(f'Tamanho da lista: {qtd}')
    return qtd


# Checa qdt paginas
def qtd_page(pg):
    pages = pg.query_selector_all('xpath=/html/body/div[6]/div/div/div/div[2]/table/tbody/tr[2]/td/table/tbody'
                                  '/tr/td/div[4]/div/div/form/div[2]/table/tfoot/tr/td/div/div[1]/div/table/tbody'
                                  '/tr/td')
    qtd = len(pages)
    # print(f'quantidade de paginas: {qtd}')
    return qtd


# clica na proxima pagina
def click_next_page(p, pg):
    pag = p-1
    element = f'//*[@id="formExpedientes:tbExpedientes:scPendentes_table"]/tbody/tr/td[{pag}]'
    pg.click(f'xpath={element}')
    pg.wait_for_locator(f'xpath=//*[@id="_viewRoot:status.start"]')
    pg.wait_for_selector('xpath=//*[@id="divListaExpedientes"]')


def handle_dialog(dialog):
    message = dialog.message
    dialog.accept()


def handle_page(tab, n_processo, caminho):
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

    destino = f'{caminho}\\{n_processo}\\'
    if not os.path.exists(destino):
        os.makedirs(destino)

    conteudo = new_tab.inner_text('xpath=//*[@id="navbar"]/ul/li/ul')

    arquivo = open(f'{destino}processo.txt', 'w')
    arquivo.writelines(conteudo)
    arquivo.close()

    timeline = texto

    arquivo = open(f'{destino}andamento.txt', 'w')
    arquivo.writelines(timeline)
    arquivo.close()

    new_tab.screenshot(path="pje.png")
    sleep(1)
    new_tab.close()


def pesquisa(page, proc, autos, c):
    if type(proc) == int:
        p = str(proc)
    else:
        p = proc
    print(f'Numero {p}')
    numero_formatado = f'{p[:7]}-{p[7:9]}.{p[9:13]}.{p[13:14]}.{p[14:16]}.{p[16:]}'
    with page.context.expect_page(timeout=50000) as tab:
        page.click(f'xpath={autos}')
        page.on("dialog", handle_dialog)

    handle_page(tab, p, c)


# coletas os expedientes
def coleta(rows, pg, c):
    delay()
    expen = '//*[@id="formExpedientes:tbExpedientes:tb"]/tr'
    conteudo = []
    for i in range(listarows(expen, pg)):
        row = f'[{i + 1}]'
        autos = f'/html/body/div[6]/div/div/div/div[2]/table/tbody/tr[2]/td/table/tbody/tr/td/div[4]/div/div/' \
                f'form/div[2]/table/tbody/tr[{i + 1}]/td[1]/div/div/span[1]/a'
        # print(f'caminho: {autos}')
        proc = f'/html/body/div[6]/div/div/div/div[2]/table/tbody/tr[2]/td/table/tbody/tr/td/div[4]/div/div/' \
               f'form/div[2]/table/tbody/tr[{i + 1}]/td[2]/div/div[2]/div/div[1]/a'
        n_proc = pg.inner_text(f'xpath={proc}')
        n_proc = ''.join([n for n in n_proc if n.isdigit()])
        # print(f'numero do processo: {n_proc}')
        pesquisa(pg, n_proc, autos, c)

        texto = pg.inner_text(f'xpath={expen + row}')
        # print(f'texto expediente {i}: \n {texto}' + '\n' + 50 * "-")
        conteudo.append(f'{texto}\n')
        conteudo.append('\n')
        rows += 1
        print(f'linhas inseridas: {rows}')
    return conteudo


def login(page, browser):

    # Interact with login form
    page.fill('input[name="username"]', USERNAME)
    page.fill('input[name="password"]', PASSWORD)
    page.click('input[name="btnEntrar"]')
    # Verify app is logged

    delay()
    page.wait_for_event('load')
    # print(page.inner_text('body > div.conteudo-login > div.login > div.msg-login'))
    if page.is_visible('[class="rich-messages"]', timeout=20000) == True:
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
    page.locator('xpath=//*[@id="home"]').wait_for(timeout=50000)


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
    login(page, browser)
    # Interact with a page
    page.click('xpath=//*[@id="barraSuperiorPrincipal"]/div/div[1]/ul/li/a')
    page.click('xpath=//*[@id="menu"]/div[2]/ul/li[1]/a')
    page.click('xpath=//*[@id="menu"]/div[2]/ul/li[1]/div/ul/li/a')
    page.wait_for_selector('#divResultadoMenuContexto')
    dados = page.inner_text('#divResultadoMenuContexto')
    dados.replace('\n', '')
    # print(dados)
    page.click('xpath=//*[@id="formAbaExpediente:listaAgrSitExp:7:linhaN1"]')
    page.wait_for_load_state(timeout=50000)
    page.wait_for_selector('xpath=//*[@id="formAbaExpediente:listaAgrSitExp:7:divArvoreJursExp"]', timeout=50000)
    """" 

    tipodocumento = '/html/body/div[6]/div/div/div/div[2]/table/tbody/tr[2]/td/table/tbody/tr/td/div[1]/div/div[2]' \
                    '/form/div/div[16]/div/div/div/div[1]/table'
    """

    tipodocumento = '//*[@id="formAbaExpediente:listaAgrSitExp:7:trPend:childs"]'

    comarcas = listaitems(tipodocumento, page)
    pagina = page.inner_html(f'xpath={tipodocumento}')
    '//*[@id="formAbaExpediente:listaAgrSitExp:7:trPend:257::jNp"]'
    soup = bs(pagina, 'html.parser')
    ids = [r['id'] for r in soup.find_all(name="a", attrs={"id": True})]
    num_id = []
    for i in ids:
        if 'jNp' in i:
            print(i)
            num_id.append(i)

    tam = len(num_id)
    print(f'Tamanho da lista de comarcas: {tam}')
    names = []
    for n in range(tam):
        c = page.inner_text(f'xpath=//*[@id="{num_id[n]}"]')
        c = c.replace('\t\t ', '')
        c = c.replace('\n', '')
        print(f'Comarca : {c}')
        s = ''.join(i for i in c if not i.isdigit())
        names.append(s)
        destino = f'RESULTADO\\{s}\\'
        if not os.path.exists(destino):
            os.makedirs(destino)
        names_comarcas = str(names)
        arquivo = open(f'./listacomarcas2.txt', 'w')
        arquivo.writelines(names_comarcas)
        arquivo.close()
        """
        endcomarca = f'/html/body/div[6]/div/div/div/div[2]/table/tbody/tr[2]/td/table/tbody/tr/td/div[1]/div/div[2]' \
                     f'/form/div/div[16]/div/div/div/div[1]/table[{n + 1}]/tbody/tr/td[3]/a'
        """
        endcomarca = f'//*[@id="{num_id[n]}"]'

        page.click(f'xpath={endcomarca}')
        page.is_hidden('xpath=//*[@id="formExpedientes:Filtros"]')
        page.wait_for_selector('xpath=//*[@id="formExpedientes:conteudoPesquisaExpedientes"]', timeout=50000)
        # pesquisa(page, 1, formulario)
        delay()
        page.is_disabled('xpath=//*[@id="_viewRoot:status.start"]')
        bt_pesquisa(page)
        data = diasUteis(hoje)
        input_dt = feriado(data)

        psq(input_dt, page)
        # data = '19/02/2021'
        delay()
        psq_bt(page)
        delay()
        page.is_disabled('xpath=//*[@id="_viewRoot:status.start"]')
        page.wait_for_selector('xpath=//*[@id="formExpedientes:conteudoPesquisaExpedientes"]', timeout=50000)
        pag = qtd_page(page)
        print(pag)

        rows = 0
        if pag == 0:
            print(f'Coletando os dados da pagina : Atual')
            page.wait_for_load_state(timeout=30000)
            page.is_disabled('xpath=//*[@id="_viewRoot:status.start"]')
            page.wait_for_selector('xpath=//*[@id="divListaExpedientes"]')
            conteudo = coleta(rows, page, destino)
            arquivo = open(f'{destino}expedientes - {USERNAME}.txt', 'w')
            arquivo.writelines(conteudo)
            arquivo.close()
            delay()
        else:
            print(pag)
            num_of_pages = True
            for p in range(pag - 6):
                print(f'Coletando os dados da pagina : {p + 1}')
                sleep(2)
                page.is_disabled('xpath=//*[@id="_viewRoot:status.start"]')
                page.wait_for_selector('xpath=//*[@id="divListaExpedientes"]')
                conteudo = coleta(rows, page, destino)
                arquivo = open(f'{destino}expedientes - {USERNAME}.txt', 'w')
                arquivo.writelines(conteudo)
                arquivo.close()
                delay()
                try:
                    click_next_page(pag, page)
                except:
                    print('You are at the end')
    browser.close()


with sync_playwright() as p:
    run(p)
