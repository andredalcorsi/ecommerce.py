import os
import csv
import asyncio
import random
from playwright.async_api import async_playwright

# Input/Output Settings
DESKTOP_PATH = os.path.join(os.path.expanduser('~'), 'Desktop')
INPUT_FILE = os.path.join(DESKTOP_PATH, 'EAN.txt')
OUTPUT_CSV = os.path.join(DESKTOP_PATH, 'results.csv')

# Selectors list to extract the product name
PRODUCT_SELECTORS = [
    'h2.product-card__name'
]

def formatar_codigo(codigo):
    """Garante que o código seja tratado como string e no formato completo"""
    return str(int(float(codigo))) if '.' in str(codigo) else str(codigo)

async def setup_browser():
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(
        headless=True,  # Switch to "False" to active the depuration mode
        timeout=60000
    )
    return browser, playwright


# Specific Selector for empty state
EMPTY_STATE_SELECTOR = 'p.empty-state__title'

async def buscar_produto(page, codigo):
    try:
        codigo_formatado = formatar_codigo(codigo)
        print(f"\nBuscando: {codigo_formatado}")
        
        await page.goto(
            f"https://www.petlove.com.br/busca?q={codigo_formatado}",
            timeout=25000,
            wait_until="networkidle"
        )
        
        # Verify first if it's a empty result
        empty_state = await page.query_selector(EMPTY_STATE_SELECTOR)
        if empty_state:
            print(f"Estado vazio detectado para {codigo_formatado}")
            return None
            
        # If not, then extract the name of the product by the selector according the EAN
        for selector in PRODUCT_SELECTORS:
            try:
                element = await page.wait_for_selector(selector, timeout=3000)
                if element:
                    produto = (await element.text_content()).strip()
                    if produto and codigo_formatado not in produto:
                        print(f"Produto encontrado: {produto}")
                        return produto
            except:
                continue
        
        # If you didn't find a product not even the 'empty state' 
        print(f"Nenhum produto encontrado (sem estado vazio explícito) para {codigo_formatado}")
        return None
        
    except Exception as e:
        print(f"Erro ao buscar {codigo_formatado}: {str(e)}")
        return None

async def extrair_nome_pagina_produto(page):
    """Extrai nome do produto quando redirecionado para página de detalhe"""
    try:
        for selector in PRODUCT_SELECTORS:
            try:
                element = await page.wait_for_selector(selector, timeout=3000)
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
        viewport={'width': 720, 'height': 1280}
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
        await context.clear_cookies()
    
    await context.close()
    return resultados

def salvar_resultados(resultados):
    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8-sig') as csvfile:
        writer = csv.writer(csvfile, delimiter=';')
        writer.writerow(["CÓDIGO", "PRODUTO", "ENCONTRADO"])
        for resultado in resultados:
            writer.writerow([resultado['CÓDIGO'], resultado['PRODUTO'], resultado['ENCONTRADO']])

async def main():
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Arquivo não encontrado: {INPUT_FILE}")
        return

    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        codigos = [linha.strip() for linha in f if linha.strip()]
    
    print(f"🔍 Total de códigos a processar: {len(codigos)}")
    
    browser, playwright = await setup_browser()
    
    try:
        tamanho_lote = 1000  # You can change the batch size here
        lotes = [codigos[i:i + tamanho_lote] for i in range(0, len(codigos), tamanho_lote)]
        resultados_totais = []
        
        for i, lote in enumerate(lotes, 1):
            print(f"\n📦 Processando lote {i}/{len(lotes)} ({len(lote)} itens)")
            resultados = await processar_lote(browser, lote)
            resultados_totais.extend(resultados)
            salvar_resultados(resultados_totais)
            
            if i < len(lotes):
                delay = random.uniform(5, 10)  # Delay between bactchs
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