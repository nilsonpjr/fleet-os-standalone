"""
Este módulo define as rotas da API para interagir com o Portal Mercury Marine.
Ele permite buscar produtos e obter informações de garantia de motores
ao realizar web scraping do portal.
"""

from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any, List, Optional
import sys
import os
import requests # Biblioteca para fazer requisições HTTP.
import asyncio # Para rodar funções síncronas em um threadpool.
from bs4 import BeautifulSoup # Biblioteca para parsing de HTML (web scraping).
import re # Módulo para expressões regulares.
from datetime import datetime, timezone
from urllib.parse import quote_plus
import auth
import schemas
from logger import get_logger

# Adiciona o diretório pai (backend) ao sys.path para permitir importações relativas.
# Isso é necessário para importar `services.fiscal_service` de `main.py`.
# Mantido conforme estrutura existente.
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Cria uma instância de APIRouter com um prefixo e tags para organização na documentação OpenAPI.
router = APIRouter(
    prefix="/api/mercury",
    tags=["Mercury"], # Tag para agrupar as rotas do Mercury na documentação.
    responses={404: {"description": "Não encontrado"}}, # Resposta padrão para 404.
)

# Limita o número de instâncias simultâneas do Playwright para economizar memória (importante para Render/Serverless)
import threading
from fastapi.concurrency import run_in_threadpool
mercury_thread_semaphore = threading.Semaphore(2)

def run_playwright_in_isolated_thread(coro_func, *args):
    """
    Executa a função async em um thread isolado com suporte completo ao subprocess_exec no Windows.
    Bypassa as limitações do Uvicorn e resolve o NotImplementedError do asyncio.
    """
    import asyncio
    import sys
    
    if sys.platform == "win32":
        policy = asyncio.WindowsProactorEventLoopPolicy()
        asyncio.set_event_loop_policy(policy)
        loop = policy.new_event_loop()
    else:
        loop = asyncio.new_event_loop()
        
    asyncio.set_event_loop(loop)
    
    try:
        with mercury_thread_semaphore:
            return loop.run_until_complete(coro_func(*args))
    finally:
        loop.close()
logger = get_logger("mercury_router")


class MercuryScraperError(Exception):
    pass


MERCURY_NO_RECORDS_XPATH = "/html/body/form[1]/table/tbody/tr/td/table[2]/tbody/tr[3]"
MERCURY_TABLE_ROWS_XPATH = "//*[@id='preco_item_web']/table/tbody/tr/td/table[2]/tbody/tr"
MERCURY_TABLE_ROW_COLS_XPATH = "//*[@id='preco_item_web']/table/tbody/tr/td/table[2]/tbody/tr[3]/td"


def normalize_mercury_header(text: str) -> str:
    cleaned = re.sub(r"\s+", " ", (text or "")).strip().lower()
    cleaned = cleaned.replace("ç", "c").replace("ã", "a")
    return cleaned


def parse_mercury_product_rows(html: str) -> List[Dict[str, str]]:
    """
    Faz parsing da grade de preços da Mercury com tolerância a variações de layout.
    """
    soup = BeautifulSoup(html, "html.parser")
    results: List[Dict[str, str]] = []

    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        if not rows:
            continue

        header_map: Dict[str, int] = {}
        for row in rows[:5]:
            header_cells = row.find_all(["th", "td"])
            if len(header_cells) < 5:
                continue
            candidate_map: Dict[str, int] = {}
            for idx, cell in enumerate(header_cells):
                normalized = normalize_mercury_header(cell.get_text(" ", strip=True))
                if normalized:
                    candidate_map[normalized] = idx
            if any("item" in key or "preco" in key or "nome" in key for key in candidate_map):
                header_map = candidate_map
                break

        for row in rows:
            cols = row.find_all("td")
            if len(cols) < 8:
                continue

            texts = [col.get_text(" ", strip=True) for col in cols]
            if not any(re.search(r"\d", cell or "") for cell in texts):
                continue

            codigo_idx = header_map.get("item", 1)
            descricao_idx = header_map.get("nome", 3)
            qtd_idx = header_map.get("quant", 0)
            estoque_idx = header_map.get("saldo", 4)
            preco_tabela_idx = header_map.get("preco tabela", 5)
            preco_base_idx = header_map.get("preco base", 6)
            preco_compra_idx = header_map.get("preco compra", 7)
            unidade_idx = header_map.get("unid p/lote", 2)

            codigo = texts[codigo_idx] if codigo_idx < len(texts) else ""
            if not codigo or not re.search(r"\d", codigo):
                continue

            valor_tabela = texts[preco_tabela_idx] if preco_tabela_idx < len(texts) else ""
            valor_base = texts[preco_base_idx] if preco_base_idx < len(texts) else ""
            valor_compra = texts[preco_compra_idx] if preco_compra_idx < len(texts) else ""

            if not valor_tabela and len(texts) > 5:
                valor_tabela = texts[5]
            if not valor_base and len(texts) > 6:
                valor_base = texts[6]
            if not valor_compra and len(texts) > 7:
                valor_compra = texts[7]

            has_price_signal = any("R$" in value for value in [valor_tabela, valor_base, valor_compra])
            if not has_price_signal:
                continue

            # Quando "Preço Base" vier vazio, usamos o preço de tabela como referência pública.
            valor_venda = valor_base or valor_tabela

            results.append({
                "codigo": codigo,
                "qtd": texts[qtd_idx] if qtd_idx < len(texts) else "",
                "descricao": texts[descricao_idx] if descricao_idx < len(texts) else "",
                "qtdaEst": texts[estoque_idx] if estoque_idx < len(texts) else "",
                "valorVenda": valor_venda,
                "valorTabela": valor_tabela,
                "valorCusto": valor_compra,
                "unidade": texts[unidade_idx] if unidade_idx < len(texts) else "",
            })

    deduped: Dict[str, Dict[str, str]] = {}
    for item in results:
        deduped[item["codigo"]] = item
    return list(deduped.values())


async def find_mercury_result_context(page, attempts: int = 6, delay_seconds: float = 1.0):
    """
    Procura o frame/página onde a tabela da Mercury realmente foi renderizada.
    """
    for _ in range(attempts):
        candidates = [page.main_frame, *page.frames]
        seen = set()

        for frame in candidates:
            if id(frame) in seen:
                continue
            seen.add(id(frame))

            try:
                no_records_locator = frame.locator(f"xpath={MERCURY_NO_RECORDS_XPATH}")
                rows_locator = frame.locator(f"xpath={MERCURY_TABLE_ROWS_XPATH}")
                if await no_records_locator.count() > 0 or await rows_locator.count() > 0:
                    return frame
            except Exception:
                continue

        await asyncio.sleep(delay_seconds)

    return None


async def collect_mercury_frame_debug(page) -> str:
    diagnostics = []
    candidates = [page.main_frame, *page.frames]
    seen = set()

    for index, frame in enumerate(candidates):
        if id(frame) in seen:
            continue
        seen.add(id(frame))
        try:
            content = await frame.content()
            snippet = re.sub(r"\s+", " ", BeautifulSoup(content, "html.parser").get_text(" ", strip=True))[:220]
            diagnostics.append(
                f"frame[{index}] url={frame.url or '-'} len={len(content)} "
                f"has_preco_item_web={'preco_item_web' in content} "
                f"has_no_records={'NoRecords' in content} "
                f"has_currency={'R$' in content} "
                f"text='{snippet}'"
            )
        except Exception as exc:
            diagnostics.append(f"frame[{index}] error={exc}")

    return " | ".join(diagnostics) if diagnostics else "nenhum frame disponível"


async def scrape_mercury_results_from_dom(page) -> List[Dict[str, str]]:
    """
    Fallback genérico: percorre tabelas/linhas do DOM procurando células com padrão de preço.
    """
    candidates = [page.main_frame, *page.frames]
    seen = set()

    for frame in candidates:
        if id(frame) in seen:
            continue
        seen.add(id(frame))

        try:
            rows = await frame.evaluate(
                """
                () => Array.from(document.querySelectorAll('tr'))
                  .map((row) => Array.from(row.querySelectorAll('td')).map((cell) => (cell.innerText || '').replace(/\\u00a0/g, ' ').trim()))
                  .filter((cells) => cells.length >= 7 && cells.some((cell) => cell.includes('R$')))
                """
            )
        except Exception:
            continue

        results = []
        for cells in rows or []:
            if len(cells) >= 8:
                codigo = cells[1].replace(" ", "")
                qtd = cells[2]
                descricao = cells[3]
                qtda_est = cells[4].replace(" ", "")
                valor_venda = cells[5]
                valor_tabela = cells[6]
                valor_custo = cells[7]
            else:
                codigo = cells[0].replace(" ", "")
                qtd = cells[1] if len(cells) > 1 else ""
                descricao = cells[2] if len(cells) > 2 else ""
                qtda_est = cells[3].replace(" ", "") if len(cells) > 3 else ""
                valor_venda = cells[4] if len(cells) > 4 else ""
                valor_tabela = cells[5] if len(cells) > 5 else ""
                valor_custo = cells[6] if len(cells) > 6 else ""

            if not codigo or not re.search(r"\d", codigo):
                continue

            results.append({
                "codigo": codigo,
                "qtd": qtd,
                "descricao": re.sub(r"\s+", " ", descricao).strip(),
                "qtdaEst": qtda_est,
                "valorVenda": valor_venda,
                "valorTabela": valor_tabela,
                "valorCusto": valor_custo,
            })

        if results:
            return results

    return []


async def scrape_mercury_results_with_xpath(page) -> List[Dict[str, str]]:
    """
    Replica a estratégia antiga do Selenium, mas usando Playwright.
    """
    frame = await find_mercury_result_context(page)
    if frame is None:
        raise MercuryScraperError("Tabela de preços Mercury não apareceu na página.")

    no_records_locator = frame.locator(f"xpath={MERCURY_NO_RECORDS_XPATH}")
    if await no_records_locator.count() > 0:
        no_records_class = (await no_records_locator.first.get_attribute("class")) or ""
        if no_records_class.strip() == "NoRecords":
            return []

    rows_locator = frame.locator(f"xpath={MERCURY_TABLE_ROWS_XPATH}")
    row_count = await rows_locator.count()
    if row_count == 0:
        raise MercuryScraperError("Tabela de preços Mercury não apareceu na página.")

    cols_locator = frame.locator(f"xpath={MERCURY_TABLE_ROW_COLS_XPATH}")
    col_count = await cols_locator.count()
    if col_count < 8:
        raise MercuryScraperError("Tabela de preços Mercury veio com menos colunas do que o esperado.")

    values: List[str] = []
    last_col = col_count - 1

    for row_idx in range(3, row_count + 1):
        for col_idx in range(2, last_col + 1):
            cell_locator = frame.locator(
                f"xpath=//*[@id='preco_item_web']/table/tbody/tr/td/table[2]/tbody/tr[{row_idx}]/td[{col_idx}]"
            )
            if await cell_locator.count() == 0:
                continue
            text = (await cell_locator.first.inner_text()).replace("\xa0", " ").strip()
            values.append(text)

    if not values:
        raise MercuryScraperError("A tabela Mercury foi encontrada, mas veio sem valores legíveis.")

    results: List[Dict[str, str]] = []
    for idx in range(0, len(values), 7):
        chunk = values[idx:idx + 7]
        if len(chunk) < 7:
            continue
        codigo = chunk[0].replace(" ", "")
        if not codigo:
            continue
        results.append({
            "codigo": codigo,
            "qtd": chunk[1],
            "descricao": re.sub(r"\s+", " ", chunk[2]).strip(),
            "qtdaEst": chunk[3].replace(" ", ""),
            "valorVenda": chunk[4],
            "valorTabela": chunk[5],
            "valorCusto": chunk[6],
        })

    if not results:
        raise MercuryScraperError("A tabela Mercury foi encontrada, mas não foi possível montar as linhas dos itens.")

    return results


async def get_mercury_relevant_content(page, selector_hints: List[str], text_hints: List[str], attempts: int = 6, delay_seconds: float = 1.0):
    """
    Alguns fluxos do portal Mercury renderizam o resultado dentro de frames.
    Este helper procura o HTML relevante tanto na página principal quanto nos frames.
    """
    last_content = ""

    for _ in range(attempts):
        candidates = [page.main_frame, *page.frames]
        seen = set()

        for frame in candidates:
            if id(frame) in seen:
                continue
            seen.add(id(frame))

            try:
                content = await frame.content()
            except Exception:
                continue

            if not content:
                continue

            last_content = content

            if any(text_hint in content for text_hint in text_hints):
                return content

            for selector in selector_hints:
                try:
                    if await frame.query_selector(selector):
                        return content
                except Exception:
                    continue

        await asyncio.sleep(delay_seconds)

    return last_content

# --- FUNÇÕES AUXILIARES ---
# Funções para realizar o web scraping e interagir com o portal Mercury.


# --- FUNÇÕES AUXILIARES (PLAYWRIGHT) ---

async def search_product_playwright(item: str, username: str, password: str) -> List[Dict[str, str]]:
    """
    Pesquisa produtos no Portal Mercury Marine usando Playwright.
    Adaptado de nilsonpjr/mercury-automation (pesqpreco_playwright).
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("Playwright não instalado. Scraper desativado.")
        return []

    if True: # Removido mercury_semaphore, limite de threads garante segurança
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-dev-shm-usage"]
            )
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = await context.new_page()

            try:
                await mercury_login(page, username, password)

                # --- BUSCA DE ITEM ---
                url_pesquisa = f"https://portal.mercurymarine.com.br/epdv/epdv002d2.asp?s_nr_pedido_web=11111111111111111&s_nr_tabpre=&s_fm_cod_com=null&s_desc_item={quote_plus(item)}"
                print(f"Searching (Playwright): {url_pesquisa}")
                await page.goto(url_pesquisa, timeout=45000, wait_until="domcontentloaded")
                await asyncio.sleep(4)

                # Verificar sem resultados
                content = await get_mercury_relevant_content(
                    page,
                    selector_hints=["form#preco_item_web", "table", ".NoRecords"],
                    text_hints=["NoRecords", "Nenhum registro encontrado", "LoginForm", "ePDV - Login"],
                )
                if "LoginForm" in content or "ePDV - Login" in content:
                    raise MercuryScraperError("Sessão Mercury inválida após login. Verifique credenciais ou bloqueio no portal.")
                if "NoRecords" in content or "Nenhum registro encontrado" in content:
                    print(f"Mercury search returned 'NoRecords' for item: {item}")
                    return []

                try:
                    dados = await scrape_mercury_results_with_xpath(page)
                except MercuryScraperError:
                    dados = await scrape_mercury_results_from_dom(page)
                    if not dados:
                        dados = parse_mercury_product_rows(content)
                    if not dados:
                        diagnostics = await collect_mercury_frame_debug(page)
                        raise MercuryScraperError(f"Tabela de preços Mercury não apareceu na página. Debug: {diagnostics}")
                return dados

            except MercuryScraperError:
                raise
            except Exception as e:
                print(f"Erro Playwright Search Product: {e}")
                raise MercuryScraperError(f"Falha ao consultar produto na Mercury: {e}")
            finally:
                await browser.close()


async def search_warranty_playwright(nro_motor: str, username: str, password: str) -> Optional[Dict[str, str]]:
    """
    Busca garantia usando Playwright com lógica otimizada (exatamente como solicitado).
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("Playwright não instalado.")
        return None

    # Função interna para gerenciar o contexto do browser e login, 
    # evitando duplicar código e mantendo encapsulamento.
    async def conecta_login_playwright(p):
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        await mercury_login(page, username, password)
        return page, browser

    async def get_cliente_name(nro_motor_val, browser_instance, page_instance):
        # Navega para obter cliente
        try:
            await page_instance.goto(f"https://portal.mercurymarine.com.br/epdv/ewr010c.asp?s_nr_serie={nro_motor_val}", timeout=30000)
            
            content = await page_instance.content()
            soup = BeautifulSoup(content, "html.parser")
            
            # Lógica específica do usuário
            nome_cli_element = soup.select_one("#warranty_clients table tbody tr:nth-of-type(3)")
            if nome_cli_element:
                 raw_text = nome_cli_element.get_text(strip=True)
                 cleaned_name = re.sub(r'^(NOME\s*:?\s*)', '', raw_text, flags=re.IGNORECASE).strip()
                 return cleaned_name
            return ""
        except Exception as e:
            print(f"Erro ao buscar cliente: {e}")
            return ""

    if True: # Removido mercury_semaphore, limite de threads garante segurança
        async with async_playwright() as p:
            page, browser = await conecta_login_playwright(p)
            
            try:
                # 1. Consulta Garantia Principal
                print(f"Consultando garantia para: {nro_motor}")
                await page.goto(f"https://portal.mercurymarine.com.br/epdv/ewr010.asp?s_nr_serie={nro_motor}", timeout=45000)
                await page.wait_for_load_state("domcontentloaded")
                
                content = await get_mercury_relevant_content(
                    page,
                    selector_hints=["#warr_cardnr_serie_1", "#warranty_clients", "table"],
                    text_hints=["LoginForm", "ePDV - Login", nro_motor.upper()],
                )
                if "LoginForm" in content or "ePDV - Login" in content:
                    raise MercuryScraperError("Sessão Mercury inválida na consulta de garantia. Verifique credenciais ou bloqueio no portal.")
                soup = BeautifulSoup(content, "html.parser")
                
                # Verificação de existência (lógica do usuário)
                # Procura texto do motor na página
                found_text = soup.find(string=lambda text: text and nro_motor.upper() in text.upper())
                
                if not found_text:
                    print("Nenhum Motor encontrado para esse número de série!")
                    return None
                    
                print("Sucesso! Motor encontrado na página.")
                
                # Extração dos dados usando seletores CSS específicos fornecidos
                # Usando try/except para cada campo para evitar crash total se mudar layout
                def safe_select(selector):
                    el = soup.select_one(selector)
                    return el.get_text(strip=True) if el else ""

                # Seletores do usuário
                nro_serie = safe_select("#warr_cardnr_serie_1")
                
                # Tabelas aninhadas são frágeis, mas é o que foi pedido.
                base_selector = "body > table > tbody > tr > td > table:nth-of-type(2) > tbody > tr:nth-of-type(3)"
                
                modelo = safe_select(f"{base_selector} > td:nth-of-type(2)")
                dt_venda = safe_select(f"{base_selector} > td:nth-of-type(3)")
                status_garantia = safe_select(f"{base_selector} > td:nth-of-type(5)")
                vld_garantia = safe_select(f"{base_selector} > td:nth-of-type(6)")
                
                # 2. Busca nome do cliente (requer navegação extra)
                nome_cli = await get_cliente_name(nro_motor, browser, page)
                
                return {
                    "nro_motor": nro_motor,
                    "nro_serie": nro_serie or nro_motor,
                    "modelo": modelo,
                    "dt_venda": dt_venda,
                    "status_garantia": status_garantia,
                    "vld_garantia": vld_garantia,
                    "nome_cli": nome_cli,
                }

            except Exception as e:
                print(f"Erro Playwright Search Warranty: {e}")
                if isinstance(e, MercuryScraperError):
                    raise
                raise MercuryScraperError(f"Falha ao consultar garantia na Mercury: {e}")
            finally:
                await browser.close()


async def mercury_login(page, username: str, password: str):
    login_url = "https://portal.mercurymarine.com.br/epdv/epdv001.asp"

    for attempt in range(2):
        try:
            await page.goto(login_url, timeout=45000, wait_until="domcontentloaded")
            break
        except Exception as e:
            if attempt == 1:
                raise MercuryScraperError(f"Não foi possível abrir a página de login da Mercury: {e}")
            await asyncio.sleep(2)

    frame = None
    for _ in range(5):
        for f in page.frames:
            try:
                if await f.query_selector("input[name='sUsuar']"):
                    frame = f
                    break
            except Exception:
                continue
        if frame:
            break
        await asyncio.sleep(1)

    if frame is None:
        frame = page.main_frame

    await frame.fill("input[name='sUsuar']", username)
    await frame.fill("input[name='sSenha']", password)

    submit_button = await frame.query_selector("#LoginFormButton_Ok")
    if submit_button:
        await submit_button.click()
    else:
        await frame.press("input[name='sSenha']", "Enter")

    try:
        await frame.wait_for_load_state("domcontentloaded", timeout=30000)
    except Exception:
        pass
    await asyncio.sleep(4)

    login_frame_still_visible = False
    login_frame_url = ""
    login_frame_text = ""
    for f in page.frames:
        try:
            has_login_input = await f.query_selector("input[name='sUsuar']") is not None
            if has_login_input or "epdv001.asp" in (f.url or ""):
                login_frame_still_visible = True
                login_frame_url = f.url or ""
                try:
                    login_frame_text = re.sub(r"\s+", " ", await f.inner_text("body"))[:200]
                except Exception:
                    login_frame_text = ""
                content = await f.content()
                if "Campo Usuário é Obrigatório" in content or "Campo Senha é Obrigatório" in content:
                    raise MercuryScraperError("O portal Mercury rejeitou o formulário de login.")
        except MercuryScraperError:
            raise
        except Exception:
            continue

    shell_urls = [f.url for f in page.frames if f.url]
    logged_in_signal = any(
        any(signal in (url or "") for signal in ["epdv000.asp", "epdv000t.asp", "epdv002", "ewr010"])
        for url in shell_urls
    )

    if login_frame_still_visible:
        raise MercuryScraperError(
            f"Login Mercury não foi concluído. Frame de login permaneceu ativo em '{login_frame_url or 'sem-url'}'. "
            f"Texto visível: '{login_frame_text}'"
        )

    if not logged_in_signal:
        debug = await collect_mercury_frame_debug(page)
        raise MercuryScraperError(f"Não foi possível confirmar a sessão Mercury após o login. Debug: {debug}")

# --- ENDPOINTS ---

from database import get_db
from database import SessionLocal
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from fastapi import Depends
import crud

@router.get("/search/{item}")
async def search_mercury_product(
    item: str,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(auth.get_current_active_user)
):
    try:
        # Fetch credentials
        company = crud.get_company_info(db, tenant_id=current_user.tenant_id)
        if not company or not company.mercury_username or not company.mercury_password:
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Credenciais Mercury não configuradas.")

        # Executa num thread isolado construindo um Event Loop independente de Uvicorn
        results = await run_in_threadpool(
            run_playwright_in_isolated_thread, 
            search_product_playwright, 
            item, company.mercury_username, company.mercury_password
        )
        return {"status": "success", "results": results}
    except MercuryScraperError as e:
        logger.warning(f"Mercury search failed for item '{item}': {e}")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro ao buscar produto: {str(e)}")

@router.get("/warranty/{serial}")
async def get_engine_warranty(
    serial: str,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(auth.get_current_active_user)
):
    try:
        # Fetch credentials
        company = crud.get_company_info(db, tenant_id=current_user.tenant_id)
        if not company or not company.mercury_username or not company.mercury_password:
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Credenciais Mercury não configuradas.")

        # Executa num thread isolado para permitir o Event Loop do Playwright respirar no Windows
        result = await run_in_threadpool(
            run_playwright_in_isolated_thread,
            search_warranty_playwright,
            serial, company.mercury_username, company.mercury_password
        )
        if result:
            return {"status": "success", "data": result}
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Motor com serial '{serial}' não encontrado.")
    except MercuryScraperError as e:
        logger.warning(f"Mercury warranty failed for serial '{serial}': {e}")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro ao buscar garantia: {str(e)}")

# --- HELPER DE PARSING ---
def parse_brl_currency(value_str: str) -> float:
    """Converte string de moeda BRL ('1.234,56') para float (1234.56)."""
    if not value_str:
        return 0.0
    try:
        # Remove caracteres não numéricos exceto , e . (e R$)
        clean_str = value_str.strip().replace("R$", "").strip()
        # Remove pontos de milhar
        clean_str = clean_str.replace(".", "")
        # Troca vírgula decimal por ponto
        clean_str = clean_str.replace(",", ".")
        return float(clean_str)
    except ValueError:
        return 0.0

@router.post("/sync-price/{part_id}")
async def sync_part_price_mercury(
    part_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(auth.get_current_active_user)
):
    """
    Sincroniza o preço de uma peça específica com o portal Mercury.
    Atualiza Custo e Preço se encontrado.
    """
    import models
    
    # 1. Fetch credentials
    company = crud.get_company_info(db, tenant_id=current_user.tenant_id)
    if not company or not company.mercury_username or not company.mercury_password:
        raise HTTPException(status_code=400, detail="Credenciais Mercury não configuradas")

    # 2. Buscar a peça
    part = crud.get_part(db, part_id=part_id)
    if not part:
        raise HTTPException(status_code=404, detail="Peça não encontrada")
    
    # 3. Buscar no Portal
    print(f"Sincronizando SKU: {part.sku}")
    try:
        results = await run_in_threadpool(run_playwright_in_isolated_thread, search_product_playwright, part.sku, company.mercury_username, company.mercury_password)
    except Exception as e:
         raise HTTPException(status_code=500, detail=f"Erro no scraper: {str(e)}")
    
    # 4. Processar Resultados
    matched_data = None
    for item in results:
        item_code = item['codigo'].strip()
        # Comparação flexível mas segura
        if item_code == part.sku or item_code in part.sku or part.sku in item_code:
             matched_data = item
             break
    
    if not matched_data:
        raise HTTPException(status_code=404, detail=f"Produto não encontrado no portal Mercury para SKU {part.sku}")
    
    # 5. Atualizar Preços
    cost = parse_brl_currency(matched_data.get('valorCusto', '0'))
    price = parse_brl_currency(matched_data.get('valorVenda', '0'))
    if price == cost and cost > 0:
        price = round(cost * 1.60, 2)
    
    print(f"Atualizando peça {part.id}: Custo {part.cost}->{cost}, Preço {part.price}->{price}")
    
    part_update = schemas.PartUpdate(
        cost=cost,
        price=price
    )
    
    updated_part = crud.update_part(db, part_id, part_update)
    
    updated_part.last_price_updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(updated_part)
    
    return {
        "status": "success",
        "part_id": part_id,
        "new_price": price,
        "new_cost": cost,
        "updated_at": updated_part.last_price_updated_at
    }
async def _batch_sync_playwright_logic(parts_data, username, password, tenant_id):
    from playwright.async_api import async_playwright
    import models
    from database import SessionLocal
    from sqlalchemy import text
    from sqlalchemy.exc import SQLAlchemyError
    import asyncio
    from urllib.parse import quote_plus
    from datetime import datetime, timezone
    
    results_summary = []
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-dev-shm-usage"]
            )
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            
            try:
                print("Batch Sync: Logging in...")
                await mercury_login(page, username, password)
                print("Batch Sync: Logged in.")
                
                for part_info in parts_data:
                    p_id = part_info["id"]
                    p_sku = part_info["sku"]
                    try:
                        search_variants = [p_sku]
                        if "-" in p_sku:
                            search_variants.append(p_sku.split("-")[-1])
                        
                        found_content = None
                        used_variant = p_sku
                        
                        for variant in search_variants:
                            url_pesquisa = f"https://portal.mercurymarine.com.br/epdv/epdv002d2.asp?s_nr_pedido_web=11111111111111111&s_nr_tabpre=&s_fm_cod_com=null&s_desc_item={quote_plus(variant)}"
                            await page.goto(url_pesquisa, timeout=30000, wait_until="domcontentloaded")
                            await asyncio.sleep(1.5)
                            
                            content = await get_mercury_relevant_content(
                                page,
                                selector_hints=["form#preco_item_web", "table", ".NoRecords"],
                                text_hints=["NoRecords", "Nenhum registro encontrado", "LoginForm", "ePDV - Login"],
                            )
                            
                            if "LoginForm" in content or "ePDV - Login" in content:
                                raise MercuryScraperError("Sessão Mercury expirou durante sincronização.")
                            
                            if not ("NoRecords" in content or "Nenhum registro encontrado" in content):
                                found_content = content
                                used_variant = variant
                                break
                        
                        if not found_content:
                            results_summary.append({
                                "id": p_id,
                                "sku": p_sku,
                                "status": "not_found",
                                "message": f"SKU não encontrado após tentar: {', '.join(search_variants)}"
                            })
                            continue
                            
                        dados_localizados = None
                        try:
                            dados_portal = await scrape_mercury_results_with_xpath(page)
                        except MercuryScraperError:
                            dados_portal = await scrape_mercury_results_from_dom(page)
                            if not dados_portal:
                                dados_portal = parse_mercury_product_rows(content)

                        if not dados_portal:
                            results_summary.append({
                                "id": p_id,
                                "sku": p_sku,
                                "status": "parse_error",
                                "message": "Tabela de preços Mercury não apareceu na página."
                            })
                            continue

                        for item_data in dados_portal:
                            item_code = item_data.get("codigo", "").strip()
                            if item_code == p_sku:
                                dados_localizados = item_data
                                break
                        
                        if dados_localizados:
                            cost = parse_brl_currency(dados_localizados['valorCusto'])
                            price = parse_brl_currency(dados_localizados['valorVenda'])
                            if price == cost and cost > 0:
                                price = round(cost * 1.60, 2)
                            
                            update_db = SessionLocal()
                            try:
                                update_db.execute(text("SET LOCAL lock_timeout = '3s'"))
                                db_part = (
                                    update_db.query(models.Part)
                                    .filter(
                                        models.Part.id == p_id,
                                        models.Part.tenant_id == tenant_id,
                                    )
                                    .first()
                                )
                                if db_part:
                                    db_part.cost = cost
                                    db_part.price = price
                                    db_part.last_price_updated_at = datetime.now(timezone.utc)
                                    update_db.commit()
                                    results_summary.append({
                                        "id": p_id,
                                        "sku": p_sku,
                                        "status": "updated",
                                        "price": price,
                                        "cost": cost,
                                        "message": "Preço sincronizado com sucesso."
                                    })
                                else:
                                    results_summary.append({
                                        "id": p_id,
                                        "sku": p_sku,
                                        "status": "error",
                                        "message": "Peça não encontrada no banco após consulta."
                                    })
                            except SQLAlchemyError as db_err:
                                update_db.rollback()
                                err_msg = str(db_err)
                                if "statement timeout" in err_msg.lower() or "lock timeout" in err_msg.lower():
                                    err_msg = "Registro bloqueado por outra operação no banco."
                                results_summary.append({
                                    "id": p_id,
                                    "sku": p_sku,
                                    "status": "db_error",
                                    "message": err_msg
                                })
                            finally:
                                update_db.close()
                        else:
                            results_summary.append({
                                "id": p_id,
                                "sku": p_sku,
                                "status": "not_found_in_table",
                                "message": "SKU não apareceu na tabela de resultados da Mercury."
                            })
                            
                    except Exception as item_err:
                        results_summary.append({
                            "id": p_id,
                            "sku": p_sku,
                            "status": "error",
                            "message": str(item_err)
                        })
                        
            finally:
                await browser.close()
    except Exception as e:
        for p in parts_data:
            results_summary.append({
                "id": p["id"],
                "sku": p["sku"],
                "status": "error",
                "message": f"Erro catastrófico no motor de sincronização: {e}"
            })
            
    return results_summary

@router.post("/batch-sync-prices")
async def batch_sync_part_prices(
    part_ids: List[int],
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(auth.get_current_active_user)
):
    """
    Sincroniza precos de multiplas pecas em uma unica sessao de navegador.
    Muito mais rapido que chamadas individuais.
    """
    import models
    
    # 1. Fetch credentials
    company = crud.get_company_info(db, tenant_id=current_user.tenant_id)
    if not company or not company.mercury_username or not company.mercury_password:
        raise HTTPException(status_code=400, detail="Credenciais Mercury não configuradas")
    
    # 2. Fetch parts data first (to avoid keeping session open during long scrape)
    parts_query = (
        db.query(models.Part.id, models.Part.sku)
        .filter(
            models.Part.id.in_(part_ids),
            models.Part.tenant_id == current_user.tenant_id,
        )
        .all()
    )
    parts_data = [{"id": r.id, "sku": r.sku} for r in parts_query]
    
    if not parts_data:
        return {"status": "success", "updated_count": 0, "results": []}
    
    try:
        results_summary = await run_in_threadpool(
            run_playwright_in_isolated_thread,
            _batch_sync_playwright_logic,
            parts_data, company.mercury_username, company.mercury_password, current_user.tenant_id
        )
        updated_count = sum(1 for r in results_summary if r["status"] == "updated")
        
        return {
            "status": "success",
            "updated_count": updated_count,
            "results": results_summary
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/batch-sync-images")
async def batch_sync_part_images(
    part_ids: List[int],
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(auth.get_current_active_user)
):
    """
    Sincroniza imagens de múltiplas peças em lote.
    Usa o part_image_service com fallback automático.
    """
    from services.part_image_service import MercuryPortalFetcher, sync_part_image
    
    # 1. Buscar credenciais
    company = crud.get_company_info(db, tenant_id=current_user.tenant_id)
    if not company:
        raise HTTPException(status_code=400, detail="Configurações da empresa não encontradas.")
    
    # 2. Buscar peças
    parts = db.query(models.Part).filter(
        models.Part.id.in_(part_ids),
        models.Part.tenant_id == current_user.tenant_id
    ).all()
    
    if not parts:
        return {"status": "success", "updated_count": 0, "results": []}

    # Inicializa o fetcher (pode falhar o auth, mas o service tem fallback)
    fetcher = MercuryPortalFetcher(
        username=company.mercury_username, 
        password=company.mercury_password
    )
    
    results_summary = []
    updated_count = 0
    
    # Como o processo é de I/O intenso (request e download), rodamos em thread para não travar o event loop
    def process_batch():
        nonlocal updated_count
        # Tenta autenticar uma vez para o lote
        fetcher.authenticate()
        
        for part in parts:
            try:
                # Sincroniza (contém lógica de persistência e commit)
                sync_part_image(db, part, fetcher=fetcher)
                if part.public_image_url:
                    updated_count += 1
                    results_summary.append({
                        "id": part.id,
                        "sku": part.sku,
                        "status": "updated",
                        "image_url": part.public_image_url
                    })
                else:
                    results_summary.append({
                        "id": part.id,
                        "sku": part.sku,
                        "status": "not_found"
                    })
            except Exception as e:
                logger.error(f"Erro ao sincronizar imagem para {part.sku}: {e}")
                results_summary.append({
                    "id": part.id,
                    "sku": part.sku,
                    "status": "error",
                    "message": str(e)
                })
        return results_summary

    await asyncio.to_thread(process_batch)

    return {
        "status": "success", 
        "updated_count": updated_count, 
        "total_requested": len(part_ids),
        "results": results_summary
    }
