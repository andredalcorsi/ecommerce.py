import os
import csv
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from tqdm import tqdm  # Para a barra de progresso

# Configurações otimizadas para 8GB RAM
DESKTOP_PATH = os.path.join(os.path.expanduser('~'), 'Desktop')
INPUT_FILE = os.path.join(DESKTOP_PATH, 'codigos_barras.txt')
OUTPUT_CSV = os.path.join(DESKTOP_PATH, 'resultados_petlove_otimizado.csv')

def setup_driver():
    chrome_options = Options()
    # Otimizações para reduzir uso de memória
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")  # Crucial para baixa memória
    chrome_options.add_argument("--window-size=800,600")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-logging")
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")
    
    # Configuração do serviço para reduzir consumo
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

def buscar_produto(driver, codigo):
    try:
        driver.get(f"https://www.petlove.com.br/busca?q={codigo}")
        # Tempo reduzido para melhor performance
        time.sleep(0.8)  # Ajuste fino entre velocidade e confiabilidade
        
        # Seletores otimizados
        for seletor in ["h2.product-card__name", "h1.product-name"]:
            try:
                elemento = driver.find_element(By.CSS_SELECTOR, seletor)
                return elemento.text.strip() if elemento else None
            except:
                continue
        return None
    except Exception:
        return None

def main():
    print("🚀 Iniciando busca ULTRA otimizada para 8GB RAM")
    
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Arquivo não encontrado: {INPUT_FILE}")
        return

    # Inicia com mensagem de uso otimizado
    print("💡 Dica: Mantenha outros programas fechados para melhor performance")
    
    driver = setup_driver()
    resultados = []
    
    try:
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            codigos = [linha.strip() for linha in f if linha.strip()]
        
        total = len(codigos)
        print(f"🔍 Total de códigos a processar: {total}")
        
        # Barra de progresso com tqdm
        with tqdm(total=total, desc="Progresso", unit="item", ncols=100) as pbar:
            for i, codigo in enumerate(codigos, 1):
                try:
                    produto = buscar_produto(driver, codigo)
                    
                    # Tentativa com código reduzido se necessário
                    if not produto and len(codigo) > 8:
                        produto = buscar_produto(driver, codigo[-8:])
                        if produto:
                            produto += " (reduzido)"
                    
                    # Adiciona resultado
                    resultados.append({
                        'CÓDIGO': codigo,
                        'PRODUTO': produto.replace("Ã§", "ç").replace("Ã£", "ã").replace("Ã©", "é") if produto else "Não encontrado",
                        'ENCONTRADO': "SIM" if produto else "NÃO"
                    })
                    
                    # Atualiza barra de progresso a cada 10 itens para performance
                    if i % 10 == 0 or i == total:
                        pbar.update(10 if i % 10 == 0 else i % 10)
                        
                    # Salva periodicamente para evitar perda de dados
                    if i % 200 == 0:
                        salvar_resultados(resultados)
                
                except KeyboardInterrupt:
                    print("\n⏸ Interrupção solicitada. Salvando progresso...")
                    break
                
                except Exception as e:
                    print(f"\n⚠️ Erro no código {codigo}: {str(e)}")
                    continue
        
        # Salva resultados finais
        salvar_resultados(resultados)
        print(f"\n✅ Busca concluída! Arquivo salvo em: {OUTPUT_CSV}")
        print(f"📊 Resumo: {sum(1 for r in resultados if r['ENCONTRADO'] == 'SIM')}/{total} encontrados")
        
    finally:
        driver.quit()
        print("🛑 Navegador fechado. Memória liberada.")

def salvar_resultados(resultados):
    """Função otimizada para salvar resultados"""
    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8-sig') as csvfile:
        writer = csv.writer(csvfile, delimiter=';')
        writer.writerow(["CÓDIGO", "PRODUTO", "ENCONTRADO"])
        for resultado in resultados:
            writer.writerow([resultado['CÓDIGO'], resultado['PRODUTO'], resultado['ENCONTRADO']])

if __name__ == "__main__":
    # Verifica se o tqdm está instalado
    try:
        from tqdm import tqdm
    except ImportError:
        print("❌ Pacote tqdm não encontrado. Instale com: pip install tqdm")
        exit(1)
    
    main()