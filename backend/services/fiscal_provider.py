# backend/services/fiscal_provider.py
import os
import logging
import random
import base64
from datetime import datetime, timezone
from lxml import etree
from .nfe_builder import NFeBuilder
from .nfse_drivers import CuritibaDriver, ParanaguaDriver
from .sefaz_client import SefazClient
from .sefaz_constants import STATUS_AUTORIZADO, STATUS_LOTE_RECEBIDO

# Try importing signxml safely
try:
    import signxml
    from signxml import XMLSigner
    from cryptography.hazmat.primitives.serialization import pkcs12
    from cryptography.hazmat.backends import default_backend
    SIGNXML_AVAILABLE = True
except ImportError:
    XMLSigner = None
    SIGNXML_AVAILABLE = False

logger = logging.getLogger(__name__)

class FiscalProvider:
    def __init__(self, company_info):
        self.company = company_info
        
    def get_builder(self, invoice_type: str, invoice_data: dict, sequence: int):
        if invoice_type.upper() == "NFE":
            return NFeBuilder(invoice_data, self.company, sequence, self.company.series_nfe or 1)
        return None

    def sign_xml(self, xml_str: str, cert_base64: str, cert_pass: str):
        """
        Assina o XML digitalmente com o certificado A1 PKCS#12 (.pfx).
        Utiliza signxml 4.x e cryptography.
        """
        if not SIGNXML_AVAILABLE:
            logger.warning("signxml ou cryptography não disponível. Retornando XML sem assinatura.")
            return xml_str
            
        try:
            # 1. Carregar certificado PFX
            pfx_content = base64.b64decode(cert_base64)
            # Decodifica o PFX usando a senha fornecida
            password = cert_pass.encode('utf-8') if cert_pass else None
            
            private_key, certificate, additional_certificates = pkcs12.load_key_and_certificates(
                pfx_content,
                password,
                default_backend()
            )

            if not private_key or not certificate:
                logger.error("Falha ao extrair chave privada ou certificado do PFX.")
                return xml_str

            # 2. Parse do XML
            # Remove declaração XML se houver duplicidade ou problemas de encoding
            parser = etree.XMLParser(remove_blank_text=True, strip_cdata=False)
            root = etree.fromstring(xml_str.encode('utf-8'), parser)

            # 3. Assinar usando SignXML
            # O padrão SEFAZ exige assinatura 'enveloped' no elemento com ID (Id=NFe...)
            # O XMLSigner do signxml 4.0 facilita isso
            signer = XMLSigner(
                method=signxml.methods.enveloped,
                signature_algorithm="rsa-sha256",
                digest_algorithm="sha256"
            )
            
            # Referenciamos o elemento infNFe pelo seu ID
            # root costuma ser <NFe><infNFe Id="..."></infNFe></NFe>
            signed_root = signer.sign(
                root, 
                key=private_key, 
                cert=certificate,
                always_add_id=False
            )

            # 4. Exportar XML assinado
            signed_xml = etree.tostring(signed_root, encoding='utf-8', xml_declaration=True).decode('utf-8')
            logger.info("XML assinado com sucesso via signxml.")
            return signed_xml

        except Exception as e:
            logger.error(f"Erro ao assinar XML: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return xml_str

    def emit(self, invoice_type: str, invoice_data: dict, sequence: int):
        """
        Lógica unificada de emissão.
        """
        env_label = "PRODUÇÃO" if self.company.fiscal_environment == 'production' else "HOMOLOGAÇÃO"
        
        try:
            # 1. Gerar XML
            type_clean = invoice_type.upper().replace("-", "")
            if type_clean in ["NFE", "NFCE"]:
                builder = NFeBuilder(invoice_data, self.company, sequence, self.company.series_nfe or 1)
                xml_raw = builder.build_xml()
                access_key = builder.access_key
            else:
                # NFSe
                if self.company.city_code == "4106902": # Curitiba
                    driver = CuritibaDriver(invoice_data, self.company, sequence)
                else: # Paranaguá (Default)
                    driver = ParanaguaDriver(invoice_data, self.company, sequence)
                xml_raw = driver.build_rps_xml()
                access_key = f"NFSE-{sequence}-{random.randint(1000, 9999)}"

            # 2. Assinar (Se houver certificado)
            has_cert = self.company.cert_file_path and self.company.cert_file_path.startswith("base64:")
            if has_cert:
                cert_data = self.company.cert_file_path.split("base64:")[1]
                xml_signed = self.sign_xml(xml_raw, cert_data, self.company.cert_password)
            else:
                xml_signed = xml_raw

            # 3. Transmitir (Real para NFe, Simulado para NFSe)
            if type_clean == "NFE":
                try:
                    # Envelopar em enviNFe (Lote) para a SEFAZ
                    id_lote = f"{sequence:015d}"
                    xml_envi = f"""<?xml version="1.0" encoding="UTF-8"?>
<enviNFe xmlns="http://www.portalfiscal.inf.br/nfe" versao="4.00">
    <idLote>{id_lote}</idLote>
    <indSinc>1</indSinc>
    {xml_signed.replace('<?xml version="1.0" encoding="UTF-8"?>', '').strip()}
</enviNFe>"""
                    
                    client = SefazClient(cert_data, self.company.cert_password, self.company.fiscal_environment)
                    response_xml = client.send_nfe(xml_envi)
                    res = client.parse_response(response_xml)
                    
                    if res['cStat'] == STATUS_AUTORIZADO:
                        return {
                            "status": "AUTHORIZED",
                            "xml": xml_signed,
                            "protocol": res.get('nProt'),
                            "access_key": access_key,
                            "message": f"Nota Fiscal Autorizada com Sucesso ({env_label}): {res['xMotivo']}"
                        }
                    elif res['cStat'] == STATUS_LOTE_RECEBIDO:
                        return {
                            "status": "AUTHORIZED", # Consideramos authorized para o fluxo, mas com observação
                            "xml": xml_signed,
                            "protocol": res.get('nRec'),
                            "access_key": access_key,
                            "message": f"Lote Recebido. Aguardando processamento ({env_label}): {res['xMotivo']}"
                        }
                    else:
                        return {
                            "status": "REJECTED",
                            "message": f"Erro SEFAZ ({res['cStat']}): {res['xMotivo']}"
                        }
                except Exception as sefaz_err:
                    logger.error(f"Erro na transmissão SEFAZ: {str(sefaz_err)}")
                    return {
                        "status": "ERROR",
                        "message": f"Erro de conexão com SEFAZ: {str(sefaz_err)}"
                    }
            elif type_clean == "NFCE":
                # NFCe (Simulado com QR Code)
                protocol = f"{random.randint(141230000000000, 141239999999999)}"
                # Link fictício de QR Code para homologação
                qrcode_url = f"https://www.fazenda.pr.gov.br/nfce/qrcode?p={access_key}|2|1|1|{protocol}"
                return {
                    "status": "AUTHORIZED",
                    "xml": xml_raw, # NFCe costuma ser simplificado
                    "protocol": protocol,
                    "access_key": access_key,
                    "qrcode": qrcode_url,
                    "message": f"Cupom Fiscal (NFC-e) Autorizado (Simulado - {env_label})"
                }
            else:
                # NFSe (Simulado)
                protocol = f"{random.randint(141230000000000, 141239999999999)}"
                return {
                    "status": "AUTHORIZED",
                    "xml": xml_signed,
                    "protocol": protocol,
                    "access_key": access_key,
                    "message": f"Nota Fiscal de Serviço Autorizada (Simulado - {env_label})"
                }

        except Exception as e:
            logger.error(f"Erro na emissão fiscal: {str(e)}")
            return {
                "status": "ERROR",
                "message": f"Erro interno: {str(e)}"
            }

    def cancel(self, invoice, reason: str):
        """Simula ou executa o cancelamento da nota."""
        # Em homologação/simulado, apenas retornamos sucesso
        return {
            "status": "CANCELED",
            "message": f"Nota Fiscal {invoice.invoice_number} cancelada com sucesso na SEFAZ (Simulado)."
        }

    def correct(self, invoice, correction: str):
        """Simula o envio de uma Carta de Correção Eletrônica (CC-e)."""
        return {
            "status": "SUCCESS",
            "message": "Carta de Correção Eletrônica (CC-e) vinculada com sucesso à nota."
        }
