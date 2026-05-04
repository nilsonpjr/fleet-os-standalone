from __future__ import annotations
from typing import Optional, List

import io
import mimetypes
import re
import os
from urllib.parse import quote_plus, urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from import models
from core.logger import get_logger
from services.storage_service import upload_file_to_storage

logger = get_logger("part_image_service")

SEARCH_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    )
}


def should_auto_fetch_part_image(part: models.Part) -> bool:
    # Pula itens genéricos ou Yamaha explicitamente conforme solicitado pelo usuário
    if part.sku.startswith("MARE-GEN") or (part.manufacturer and "yamaha" in part.manufacturer.lower()):
        return False
    # Para todos os outros, se não houver imagem, tentamos a busca automática
    return not part.public_image_url


class MercuryPortalFetcher:
    """
    Fetcher especializado no portal oficial da Mercury Marine (EzPartsWeb).
    Usa as credenciais BrazilUser para autenticar e buscar imagens via SKU direto.
    URL base: https://mercurymarine.sysonline.com/
    """
    def __init__(self, username: str = "BrazilUser", password: str = "Mercury"):
        self.username = username
        self.password = password
        self.base_url = "https://mercurymarine.sysonline.com/"
        self.session = requests.Session()
        self.is_authenticated = False

    def authenticate(self) -> bool:
        """Realiza o login no portal EzPartsWeb"""
        if not self.username or not self.password:
            logger.warning("Credenciais Mercury não fornecidas para o Fetcher.")
            return False

        try:
            # 1. Pegar a página de login para cookies iniciais e ViewState (ASP.NET)
            login_url = urljoin(self.base_url, "Login2.aspx")
            login_page = self.session.get(login_url, headers=SEARCH_HEADERS, timeout=15)
            login_page.raise_for_status()
            
            soup = BeautifulSoup(login_page.text, "html.parser")
            vs_el = soup.find("input", {"id": "__VIEWSTATE"})
            ev_el = soup.find("input", {"id": "__EVENTVALIDATION"})
            vg_el = soup.find("input", {"id": "__VIEWSTATEGENERATOR"})
            
            if not vs_el:
                logger.error("Não foi possível encontrar __VIEWSTATE na página de login do EzParts.")
                return False

            viewstate = vs_el.get("value")
            eventvalidation = ev_el.get("value") if ev_el else ""
            viewstategen = vg_el.get("value") if vg_el else ""
            
            # 2. Submeter formulário de login
            login_data = {
                "__VIEWSTATE": viewstate,
                "__VIEWSTATEGENERATOR": viewstategen,
                "__EVENTVALIDATION": eventvalidation,
                "tbLogin": self.username,
                "tbPassword": self.password,
                "btnLogin": "Login"
            }
            
            # Adicionar Referer - Essencial para muitos sistemas ASP.NET
            post_headers = SEARCH_HEADERS.copy()
            post_headers["Referer"] = login_url
            
            response = self.session.post(
                login_url, 
                data=login_data, 
                headers=post_headers, 
                timeout=15,
                allow_redirects=True
            )
            
            # Se logamos com sucesso, ele redireciona para Default.aspx ou similar
            if "Default.aspx" in response.url or "frmDashBoard.aspx" in response.url or "frmSelectCatalog.aspx" in response.url:
                self.is_authenticated = True
                logger.info("Autenticado com sucesso no Portal Mercury (EzPartsWeb)")
                return True
            else:
                logger.error(f"Falha na autenticação Mercury (EzParts). URL final: {response.url}")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao autenticar no portal Mercury EzParts: {e}")
            return False

    def get_image_url_binary(self, sku: str) -> Optional[tuple[io.BytesIO, str]]:
        """Busca a imagem diretamente pelo SKU via padrão do EzPartsWeb"""
        if not self.is_authenticated:
            if not self.authenticate():
                return None
        
        # Padronização de SKU: Remove espaços e pontos para o portal EzParts Web se necessário
        image_pattern_url = urljoin(self.base_url, f"frmGetPartImage.aspx?pn={sku}")
        
        try:
            response = self.session.get(image_pattern_url, headers=SEARCH_HEADERS, timeout=15)
            response.raise_for_status()
            
            content_type = response.headers.get("content-type", "").lower()
            if "image/" not in content_type:
                logger.debug(f"Portal Mercury não forneceu imagem para SKU {sku} (Tipo: {content_type})")
                return None
            
            return io.BytesIO(response.content), content_type
            
        except Exception as e:
            logger.error(f"Erro ao buscar imagem direta para SKU {sku}: {e}")
            return None


def sync_part_image(db: Session, part: models.Part, force: bool = False, fetcher: Optional[MercuryPortalFetcher] = None) -> models.Part:
    if not force and part.public_image_url:
        return part

    # Primeiro tentamos o Portal Oficial (EzParts) se for Mercury
    if fetcher and should_auto_fetch_part_image(part):
        try:
            result = fetcher.get_image_url_binary(part.sku)
            if result:
                image_io, content_type = result
                stored_url = _persist_image_binary(image_io, content_type, part)
                if stored_url:
                    part.public_image_url = stored_url
                    # Se encontrou no portal oficial, rotulamos como marca Mercury
                    if not part.manufacturer or "yamaha" not in part.manufacturer.lower():
                        part.manufacturer = "Mercury / Quicksilver / Seachoice / Attwood"
                    db.add(part)
                    db.commit()
                    db.refresh(part)
                    logger.info(f"Imagem e Marca OFICIAIS definida para SKU {part.sku}: {stored_url}")
                    return part
        except Exception as e:
            logger.warning(f"Erro ao tentar portal oficial para SKU {part.sku}, tentando fallback: {e}")

    # Fallback: Busca genérica (DDG + Busca em site global da Mercury indexado)
    logger.info(f"Iniciando busca em fallback (web search) para SKU {part.sku}")
    image_url = find_part_image_url(part.sku, part.name)
    if not image_url:
        logger.info(f"Nenhuma imagem automática encontrada para SKU {part.sku} (via DDG)")
        return part

    stored_url = _persist_image(image_url, part)
    final_url = stored_url or image_url

    part.public_image_url = final_url
    db.add(part)
    db.commit()
    db.refresh(part)
    logger.info(f"Imagem DDG definida para SKU {part.sku}: {final_url}")
    return part


def find_part_image_url(sku: str, name: Optional[str] = None) -> Optional[str]:
    candidate_pages = _search_mercury_product_pages(sku, name)
    for page_url in candidate_pages:
        image_url = _extract_image_from_product_page(page_url)
        if image_url:
            return image_url
    return None


def _search_mercury_product_pages(sku: str, name: Optional[str] = None) -> list[str]:
    queries = [
        f'site:mercurymarine.com "{sku}" "Mercury Marine"',
        f'site:mercurymarine.com/br/en/product "{sku}"',
    ]
    if name:
        queries.append(f'site:mercurymarine.com "{sku}" "{name}"')

    results: list[str] = []
    for query in queries:
        try:
            search_url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
            response = requests.get(search_url, headers=SEARCH_HEADERS, timeout=10)
            response.raise_for_status()
            for candidate in _extract_result_links(response.text):
                if candidate not in results:
                    results.append(candidate)
        except Exception as exc:
            logger.warning(f"Falha ao pesquisar imagem Mercury para '{sku}' com query '{query}': {exc}")

    return results


def _extract_result_links(html: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    links: list[str] = []
    for anchor in soup.select("a.result__a, a[data-testid='result-title-a']"):
        href = (anchor.get("href") or "").strip()
        if not href:
            continue
        parsed = urlparse(href)
        if "mercurymarine.com" not in parsed.netloc:
            continue
        if "/product/" not in parsed.path:
            continue
        links.append(href)

    if not links:
        for anchor in soup.find_all("a", href=True):
            href = anchor["href"].strip()
            parsed = urlparse(href)
            if "mercurymarine.com" in parsed.netloc and "/product/" in parsed.path and href not in links:
                links.append(href)
    return links[:5]


def _extract_image_from_product_page(page_url: str) -> Optional[str]:
    try:
        response = requests.get(page_url, headers=SEARCH_HEADERS, timeout=10)
        response.raise_for_status()
    except Exception as exc:
        logger.warning(f"Falha ao abrir página de produto Mercury '{page_url}': {exc}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")

    meta_candidates = [
        soup.find("meta", attrs={"property": "og:image"}),
        soup.find("meta", attrs={"name": "twitter:image"}),
        soup.find("meta", attrs={"property": "og:image:url"}),
    ]
    for meta in meta_candidates:
        content = (meta.get("content") if meta else "") or ""
        if _looks_like_image_url(content):
            return urljoin(page_url, content)

    for img in soup.find_all("img", src=True):
        src = img.get("src", "").strip()
        alt = (img.get("alt") or "").lower()
        if not _looks_like_image_url(src):
            continue
        if "mercury" in alt or "quicksilver" in alt or "/product/" in response.url:
            return urljoin(page_url, src)

    return None


def _looks_like_image_url(url: str) -> bool:
    if not url:
        return False
    normalized = url.lower()
    return any(
        ext in normalized for ext in [".jpg", ".jpeg", ".png", ".webp", ".gif", "images/", "/img/", "data:image"]
    )


def _persist_image_binary(image_io: io.BytesIO, content_type: str, part: models.Part) -> Optional[str]:
    """Persiste uma imagem já baixada via binary IO."""
    try:
        extension = mimetypes.guess_extension(content_type) or ".jpg"
        extension = ".jpg" if extension == ".jpe" else extension
        safe_sku = re.sub(r"[^A-Za-z0-9_-]+", "-", part.sku).strip("-") or f"part-{part.id}"
        filename = f"parts/auto/{safe_sku}{extension}"
        
        try:
            return upload_file_to_storage(image_io, filename, content_type)
        except Exception as storage_exc:
            logger.info(f"Usando fallback local para imagem {part.sku}: {storage_exc}")
            local_dir = "site-marealta/public/images/products/"
            os.makedirs(local_dir, exist_ok=True)
            local_path = os.path.join(local_dir, f"{safe_sku}{extension}")
            with open(local_path, "wb") as f:
                f.write(image_io.getvalue())
            return f"/images/products/{safe_sku}{extension}"
            
    except Exception as exc:
        logger.warning(f"Falha ao persistir imagem binária da peça {part.sku}: {exc}")
        return None


def _persist_image(remote_url: str, part: models.Part) -> Optional[str]:
    try:
        response = requests.get(remote_url, headers=SEARCH_HEADERS, timeout=15)
        response.raise_for_status()
        content_type = response.headers.get("content-type", "image/jpeg").split(";")[0].strip()
        if not content_type.startswith("image/"):
            logger.warning(f"URL encontrada para SKU {part.sku} não retornou imagem: {remote_url}")
            return None

        return _persist_image_binary(io.BytesIO(response.content), content_type, part)
    except Exception as exc:
        logger.warning(f"Falha ao persistir imagem automática da peça {part.sku}: {exc}")
        return None
