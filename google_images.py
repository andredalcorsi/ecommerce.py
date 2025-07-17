import os
import csv
import asyncio
import random
import uuid
from playwright.async_api import async_playwright
from urllib.parse import quote_plus

# Configurações de entrada/saída
DESKTOP_PATH = os.path.join(os.path.expanduser('~'), 'Desktop')
INPUT_FILE = os.path.join(DESKTOP_PATH, 'EAN.txt')
OUTPUT_CSV = os.path.join(DESKTOP_PATH, 'google_results.csv')
IMAGES_DIR = os.path.join(DESKTOP_PATH, 'product_images')

# Criar diretório para imagens se não existir
os.makedirs(IMAGES_DIR, exist_ok=True)

# Seletores para extrair informações do Google
GOOGLE_SEARCH_SELECTOR = 'div#search div.g'  # Blocos de resultados de busca
GOOGLE_TITLE_SELECTOR = 'h3'  # Título do resultado
GOOGLE_LINK_SELECTOR = 'a'  # Link do resultado
GOOGLE_DESCRIPTION_SELECTOR = 'div[data-sncf]'  # Descrição
GOOGLE_IMAGE_SELECTOR = 'div[jsname="dTDiAc"] img[jsname="Q4LuWd"]'  # Imagens

# URL base para buscas
GOOGLE_SEARCH_URL = "https://www.google.com/search?q="
GOOGLE_IMAGE_URL = "https://www.google.com/search?tbm=isch&q="

def formatar_codigo(codigo):
    """Garante que o código seja tratado como string e no formato completo"""
    return str(int(float(codigo))) if '.' in str(codigo) else str(codigo)

async def setup_browser():
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(
        headless=True,  # Altere para False para depuração
        timeout=60000
    )
    return browser, playwright

async def buscar_no_google(page, codigo):
    """Busca informações sobre o produto no Google"""
    try:
        codigo_formatado = formatar_codigo(codigo)
        print(f"\n🔍 Buscando: {codigo_formatado}")
        
        await page.goto(
            f"{GOOGLE_SEARCH_URL}{quote_plus(codigo_formatado)}",
            timeout=20000,
            wait_until="domcontentloaded"
        )
        
        # Aceitar cookies se necessário (para evitar o popup)
        try:
            accept_button = await page.query_selector('button:has-text("Aceitar tudo")')
            if accept_button:
                await accept_button.click()
                await asyncio.sleep(1)
        except:
            pass
        
        resultados = []
        
        # Extrair resultados da primeira página
        search_results = await page.query_selector_all(GOOGLE_SEARCH_SELECTOR)
        
        for result in search_results[:3]:  # Pegar apenas os 3 primeiros resultados
            try:
                title_element = await result.query_selector(GOOGLE_TITLE_SELECTOR)
                link_element = await result.query_selector(GOOGLE_LINK_SELECTOR)
                desc_element = await result.query_selector(GOOGLE_DESCRIPTION_SELECTOR)
                
                title = await title_element.text_content() if title_element else "Sem título"
                link = await link_element.get_attribute('href') if link_element else "Sem link"
                description = await desc_element.text_content() if desc_element else "Sem descrição"
                
                resultados.append({
                    'titulo': title.strip(),
                    'link': link,
                    'descricao': description.strip()
                })
            except:
                continue
        
        return resultados if resultados else None
        
    except Exception as e:
        print(f"Erro ao buscar {codigo_formatado} no Google: {str(e)}")
        return None

async def download_image(page, codigo):
    """Busca e salva a imagem do produto no Google Images"""
    try:
        codigo_formatado = formatar_codigo(codigo)
        print(f"📷 Buscando imagem para: {codigo_formatado}")
        
        await page.goto(
            f"{GOOGLE_IMAGE_URL}{quote_plus(codigo_formatado)}",
            timeout=15000,
            wait_until="domcontentloaded"
        )
        
        # Aguardar carregamento das imagens
        try:
            await page.wait_for_selector(GOOGLE_IMAGE_SELECTOR, timeout=5000)
        except:
            print(f"Nenhuma imagem encontrada para {codigo_formatado}")
            return None
        
        # Pegar a primeira imagem
        img_elements = await page.query_selector_all(GOOGLE_IMAGE_SELECTOR)
        if not img_elements:
            print(f"Nenhuma imagem encontrada para {codigo_formatado}")
            return None
        
        img_element = img_elements[0]
        img_src = await img_element.get_attribute('src')
        
        if not img_src:
            print(f"Imagem sem src para {codigo_formatado}")
            return None
        
        # Gerar nome único para o arquivo
        filename = f"{codigo_formatado}_{uuid.uuid4().hex[:6]}.jpg"
        filepath = os.path.join(IMAGES_DIR, filename)
        
        # Salvar a imagem
        if img_src.startswith('data:'):
            # Imagem em base64
            import base64
            img_data = img_src.split('base64,')[1]
            with open(filepath, 'wb') as f:
                f.write(base64.b64decode(img_data))
        else:
            # URL regular
            async with page.expect_download() as download_info:
                await img_element.click()
            download = await download_info.value
            await download.save_as(filepath)
        
        print(f"✅ Imagem salva: {filename}")
        return filename
        
    except Exception as e:
        print(f"Erro ao baixar imagem para {codigo_formatado}: {str(e)}")
        return None

async def processar_lote(browser, lote):
    context = await browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        viewport={'width': 1280, 'height': 720}
    )
    page = await context.new_page()
    
    resultados = []
    for codigo in lote:
        codigo_formatado = formatar_codigo(codigo)
        
        # Buscar resultados no Google
        resultados_busca = await buscar_no_google(page, codigo_formatado)
        
        # Buscar imagem
        imagem = await download_image(page, codigo_formatado)
        
        # Preparar dados para o CSV
        primeiro_resultado = resultados_busca[0] if resultados_busca else None
        
        resultados.append({
            'CÓDIGO': codigo_formatado,
            'TÍTULO': primeiro_resultado['titulo'] if primeiro_resultado else 'Nenhum resultado',
            'LINK': primeiro_resultado['link'] if primeiro_resultado else '',
            'DESCRIÇÃO': primeiro_resultado['descricao'] if primeiro_resultado else '',
            'IMAGEM': imagem if imagem else '',
            'ENCONTRADO': 'SIM' if primeiro_resultado else 'NÃO'
        })
        
        # Limpar cookies e cache entre buscas
        await context.clear_cookies()
        await asyncio.sleep(random.uniform(1, 3))  # Delay aleatório entre buscas
    
    await context.close()
    return resultados

def salvar_resultados(resultados):
    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8-sig') as csvfile:
        writer = csv.writer(csvfile, delimiter=';')
        writer.writerow(["CÓDIGO", "TÍTULO", "LINK", "DESCRIÇÃO", "IMAGEM", "ENCONTRADO"])
        for resultado in resultados:
            writer.writerow([
                resultado['CÓDIGO'],
                resultado['TÍTULO'],
                resultado['LINK'],
                resultado['DESCRIÇÃO'],
                resultado['IMAGEM'],
                resultado['ENCONTRADO']
            ])

async def main():
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Arquivo não encontrado: {INPUT_FILE}")
        return

    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        codigos = [linha.strip() for linha in f if linha.strip()]
    
    print(f"🔍 Total de códigos a processar: {len(codigos)}")
    print(f"📁 Diretório de imagens: {IMAGES_DIR}")
    
    browser, playwright = await setup_browser()
    
    try:
        tamanho_lote = 50  # Tamanho menor para evitar bloqueios
        lotes = [codigos[i:i + tamanho_lote] for i in range(0, len(codigos), tamanho_lote)]
        resultados_totais = []
        
        for i, lote in enumerate(lotes, 1):
            print(f"\n📦 Processando lote {i}/{len(lotes)} ({len(lote)} itens)")
            resultados = await processar_lote(browser, lote)
            resultados_totais.extend(resultados)
            salvar_resultados(resultados_totais)
            
            if i < len(lotes):
                delay = random.uniform(10, 20)  # Delay maior entre lotes
                print(f"⏳ Aguardando {delay:.1f}s...")
                await asyncio.sleep(delay)
        
        encontrados = sum(1 for r in resultados_totais if r['ENCONTRADO'] == 'SIM')
        imagens = sum(1 for r in resultados_totais if r['IMAGEM'])
        print(f"\n✅ Concluído! {encontrados}/{len(codigos)} encontrados, {imagens} imagens salvas")
        print(f"📄 Resultados salvos em: {OUTPUT_CSV}")
        print(f"🖼️ Imagens salvas em: {IMAGES_DIR}")
    
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
    finally:
        await browser.close()
        await playwright.stop()

if __name__ == "__main__":
    asyncio.run(main())