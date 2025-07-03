import os
import csv
import asyncio
import random
from playwright.async_api import async_playwright

# Configurações
DESKTOP_PATH = os.path.join(os.path.expanduser('~'), 'Desktop')
INPUT_FILE = os.path.join(DESKTOP_PATH, 'codigos_barras.txt')
OUTPUT_CSV = os.path.join(DESKTOP_PATH, 'resultados_cobasi_async.csv')

# Configuração de tempo de espera
TIMEOUT = 20000  # 15 segundos

def formatar_codigo(codigo):
    """Garante que o código seja tratado como string e no formato completo"""
    return str(int(float(codigo))) if '.' in str(codigo) else str(codigo)

async def setup_browser():
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(
        headless=False,  # Mantenha como False para depuração
        args=[
            '--disable-blink-features=AutomationControlled',
            '--start-maximized'
        ]
    )
    return browser, playwright

import os
import csv
import asyncio
import random
from playwright.async_api import async_playwright

# Configurações
DESKTOP_PATH = os.path.join(os.path.expanduser('~'), 'Desktop')
INPUT_FILE = os.path.join(DESKTOP_PATH, 'codigos_barras.txt')
OUTPUT_CSV = os.path.join(DESKTOP_PATH, 'resultados_cobasi_async.csv')

# Configuração de tempo de espera
TIMEOUT = 15000  # 15 segundos

def formatar_codigo(codigo):
    """Garante que o código seja tratado como string e no formato completo"""
    return str(int(float(codigo))) if '.' in str(codigo) else str(codigo)

async def setup_browser():
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(
        headless=False,  # Mantenha como False para depuração
        args=[
            '--disable-blink-features=AutomationControlled',
            '--start-maximized'
        ]
    )
    return browser, playwright

async def buscar_produto(page, codigo):
    try:
        codigo_formatado = formatar_codigo(codigo)
        print(f"\nBuscando: {codigo_formatado}")
        
        await asyncio.sleep(random.uniform(1, 3))
        page.set_default_timeout(TIMEOUT)
        
            # Configuração turbo
        await page.goto(
            f"https://www.cobasi.com.br/pesquisa?terms={codigo_formatado}",
            timeout=8000,  # Reduzido para 8 segundos
            wait_until="domcontentloaded"  # Mais rápido que networkidle
        )
            
        # Verifica redirecionamento para página de produto
        if "/p/" in page.url:
            print("Redirecionado para página de produto")
            nome_produto = await extrair_nome_pagina_produto(page)
            if nome_produto:
                return nome_produto
        
        # Seletores específicos para a estrutura atual da Cobasi
        selectors = [
            {"selector": "h3.styles_Title-sc-3uf957-1", "description": "Título principal novo padrão"},
            {"selector": "h3[class*='Title-sc']", "description": "Título com classe contendo Title-sc"},
        ]
        
        for seletor in selectors:
            try:
                print(f"Tentando seletor: {seletor['description']}")
                element = await page.wait_for_selector(seletor['selector'], timeout=2000, state="attached")
                if element:
                    texto = (await element.text_content()).strip()
                    if texto:
                        print(f"Produto encontrado com seletor {seletor['description']}: {texto}")
                        return texto
            except Exception as e:
                continue
                
        print("Nenhum seletor encontrou produto")
        return None
        
    except Exception as e:
        print(f"Erro ao buscar {codigo}: {str(e)}")
        return None

async def extrair_nome_pagina_produto(page):
    """Extrai nome do produto quando redirecionado para página de detalhe"""
    try:
        selectors = [
            "h1.product-name",
            "h1[itemprop='name']",
            ".product-name__title",
            ".product-info__name",
            "h1.title",
            "h1.productName"
        ]
        
        for selector in selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    texto = (await element.text_content()).strip()
                    if texto:
                        return texto
            except:
                continue
        return None
    except:
        return None

async def processar_lote(browser, lote):
    context = await browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        viewport={'width': 1280, 'height': 720}
    )
    page = await context.new_page()
    
    resultados = []
    for codigo in lote:
        produto = await buscar_produto(page, codigo)
        resultados.append({
            'CÓDIGO': codigo,
            'PRODUTO': produto if produto else '',
            'ENCONTRADO': 'SIM' if produto else 'NÃO'
        })
        await context.clear_cookies()  # Limpa cookies entre requisições
    
    await context.close()
    return resultados

def salvar_resultados(resultados):
    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8-sig') as csvfile:
        writer = csv.writer(csvfile, delimiter=';')
        writer.writerow(["CÓDIGO", "PRODUTO", "ENCONTRADO"])
        for resultado in resultados:
            writer.writerow([resultado['CÓDIGO'], resultado['PRODUTO'], resultado['ENCONTRADO']])

async def main():
    print("🚀 Iniciando busca na Cobasi")
    
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Arquivo não encontrado: {INPUT_FILE}")
        return

    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        codigos = [linha.strip() for linha in f if linha.strip()]
    
    print(f"🔍 Total de códigos a processar: {len(codigos)}")
    
    browser, playwright = await setup_browser()
    
    try:
        tamanho_lote = 20
        lotes = [codigos[i:i + tamanho_lote] for i in range(0, len(codigos), tamanho_lote)]
        resultados_totais = []
        
        for i, lote in enumerate(lotes, 1):
            print(f"\n📦 Processando lote {i}/{len(lotes)} ({len(lote)} itens)")
            resultados = await processar_lote(browser, lote)
            resultados_totais.extend(resultados)
            salvar_resultados(resultados_totais)
            
            if i < len(lotes):
                delay = random.uniform(3, 8)
                print(f"⏳ Aguardando {delay:.1f}s...")
                await asyncio.sleep(delay)
        
        encontrados = sum(1 for r in resultados_totais if r['ENCONTRADO'] == 'SIM')
        print(f"\n✅ Concluído! {encontrados}/{len(codigos)} encontrados")
        print(f"📄 Resultados salvos em: {OUTPUT_CSV}")
    
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
    finally:
        await browser.close()
        await playwright.stop()

if __name__ == "__main__":
    asyncio.run(main())