import os
import csv
import asyncio
import random
import uuid
from playwright.async_api import async_playwright
from urllib.parse import quote_plus

# Configurações
DESKTOP_PATH = os.path.join(os.path.expanduser('~'), 'Desktop')
INPUT_FILE = os.path.join(DESKTOP_PATH, 'EAN.txt')  # Agora com nomes de produtos
OUTPUT_CSV = os.path.join(DESKTOP_PATH, 'google_shopping_results.csv')
IMAGES_DIR = os.path.join(DESKTOP_PATH, 'product_images')
os.makedirs(IMAGES_DIR, exist_ok=True)

# Seletores Google Shopping atualizados
PRODUCT_SELECTORS = {
    'title': 'div.tol8Rb.OSrXXb h3',
    'price': 'span.a8Pemb',
    'store': 'div.IuHnof',
    'link': 'a[jsname="UWckNb"]',
    'image': 'img.Q4LuWd'
}

async def setup_browser():
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(
        headless=True,
        timeout=60000
    )
    return browser, playwright

async def search_google_shopping(page, product_name):
    """Busca produtos no Google Shopping pelo nome"""
    try:
        search_url = f"https://www.google.com/search?tbm=shop&q={quote_plus(product_name)}"
        await page.goto(search_url, timeout=15000, wait_until="networkidle")
        
        # Fechar popups (cookies, etc)
        try:
            await page.click('button:has-text("Aceitar tudo")', timeout=2000)
        except:
            pass

        # Extrair resultados
        results = []
        product_cards = await page.query_selector_all('div.sh-dgr__content')
        
        for card in product_cards[:3]:  # Limitar a 3 resultados
            try:
                title = await card.query_selector(PRODUCT_SELECTORS['title'])
                price = await card.query_selector(PRODUCT_SELECTORS['price'])
                store = await card.query_selector(PRODUCT_SELECTORS['store'])
                link = await card.query_selector(PRODUCT_SELECTORS['link'])
                
                result = {
                    'product': await title.text_content() if title else "N/A",
                    'price': await price.text_content() if price else "N/A",
                    'store': await store.text_content() if store else "N/A",
                    'link': await link.get_attribute('href') if link else "N/A"
                }
                results.append(result)
            except Exception as e:
                print(f"Erro ao extrair resultado: {str(e)}")
                continue
        
        return results if results else None
    
    except Exception as e:
        print(f"Erro na busca por {product_name}: {str(e)}")
        return None

async def download_product_image(page, product_name):
    """Baixa a imagem principal do produto"""
    try:
        search_url = f"https://www.google.com/search?tbm=isch&q={quote_plus(product_name)}"
        await page.goto(search_url, timeout=15000, wait_until="domcontentloaded")
        
        # Aguardar imagem carregar
        try:
            await page.wait_for_selector(PRODUCT_SELECTORS['image'], timeout=5000)
        except:
            return None
        
        # Selecionar a melhor imagem (primeira com largura >= 300px)
        images = await page.query_selector_all(PRODUCT_SELECTORS['image'])
        for img in images:
            try:
                width = await img.get_attribute('width')
                if width and int(width) >= 300:
                    img_src = await img.get_attribute('src')
                    if img_src:
                        filename = f"{uuid.uuid4().hex[:8]}.jpg"
                        filepath = os.path.join(IMAGES_DIR, filename)
                        
                        if img_src.startswith('data:'):
                            import base64
                            img_data = img_src.split('base64,')[1]
                            with open(filepath, 'wb') as f:
                                f.write(base64.b64decode(img_data))
                        else:
                            async with page.expect_download() as download_info:
                                await img.click()
                            download = await download_info.value
                            await download.save_as(filepath)
                        
                        return filename
            except:
                continue
        return None
    
    except Exception as e:
        print(f"Erro ao baixar imagem: {str(e)}")
        return None

async def process_batch(browser, product_names):
    context = await browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        viewport={'width': 1280, 'height': 800}
    )
    page = await context.new_page()
    
    results = []
    for product_name in product_names:
        print(f"\n🔍 Buscando: {product_name}")
        
        # Buscar no Google Shopping
        shopping_results = await search_google_shopping(page, product_name)
        
        # Baixar imagem
        image_file = None
        if shopping_results:
            image_file = await download_product_image(page, product_name)
        
        # Salvar resultados
        first_result = shopping_results[0] if shopping_results else None
        results.append({
            'PRODUTO': product_name,
            'TÍTULO': first_result['product'] if first_result else "Não encontrado",
            'PREÇO': first_result['price'] if first_result else "N/A",
            'LOJA': first_result['store'] if first_result else "N/A",
            'LINK': first_result['link'] if first_result else "N/A",
            'IMAGEM': image_file if image_file else "",
            'STATUS': 'ENCONTRADO' if first_result else 'NÃO ENCONTRADO'
        })
        
        await asyncio.sleep(random.uniform(2, 4))  # Delay entre buscas
    
    await context.close()
    return results

def save_results(results):
    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8-sig') as csvfile:
        writer = csv.writer(csvfile, delimiter=';')
        writer.writerow(["PRODUTO", "TÍTULO", "PREÇO", "LOJA", "LINK", "IMAGEM", "STATUS"])
        for result in results:
            writer.writerow([
                result['PRODUTO'],
                result['TÍTULO'],
                result['PREÇO'],
                result['LOJA'],
                result['LINK'],
                result['IMAGEM'],
                result['STATUS']
            ])

async def main():
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Arquivo não encontrado: {INPUT_FILE}")
        return

    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        product_names = [linha.strip() for linha in f if linha.strip()]
    
    print(f"🔍 Total de produtos a pesquisar: {len(product_names)}")
    print(f"📁 Imagens serão salvas em: {IMAGES_DIR}")
    
    browser, playwright = await setup_browser()
    
    try:
        batch_size = 10  # Tamanho do lote reduzido para evitar bloqueios
        batches = [product_names[i:i + batch_size] for i in range(0, len(product_names), batch_size)]
        
        all_results = []
        for i, batch in enumerate(batches, 1):
            print(f"\n📦 Processando lote {i}/{len(batches)} ({len(batch)} produtos)")
            
            batch_results = await process_batch(browser, batch)
            all_results.extend(batch_results)
            save_results(all_results)
            
            if i < len(batches):
                delay = random.uniform(10, 20)
                print(f"⏳ Aguardando {delay:.1f} segundos...")
                await asyncio.sleep(delay)
        
        found_count = sum(1 for r in all_results if r['STATUS'] == 'ENCONTRADO')
        print(f"\n✅ Concluído! {found_count}/{len(product_names)} produtos encontrados")
        print(f"📄 Resultados salvos em: {OUTPUT_CSV}")
    
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
    finally:
        await browser.close()
        await playwright.stop()

if __name__ == "__main__":
    asyncio.run(main())