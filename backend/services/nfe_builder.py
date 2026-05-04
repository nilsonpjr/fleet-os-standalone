
# backend/services/nfe_builder.py
import os
from datetime import datetime
from uuid import uuid4
import random

def format_date_sefaz(dt):
    """Formata data para padrão SEFAZ: AAAA-MM-DDTHH:MM:SS-03:00"""
    return dt.strftime("%Y-%m-%dT%H:%M:%S") + "-03:00"

class NFeBuilder:
    def __init__(self, invoice_data, company_info, seq_nfe, series_nfe):
        self.data = invoice_data
        self.company = company_info
        self.seq = seq_nfe
        self.series = series_nfe
        self.access_key = self.generate_access_key()
        
    def generate_access_key(self):
        """Gera a Chave de Acesso de 44 dígitos"""
        # Estrutura: UF(2) + AAMM(4) + CNPJ(14) + Mod(2) + Serie(3) + nNF(9) + tpEmis(1) + cNF(8) + DV(1)
        uf = "41" # PR (Hardcoded for MVP, should come from IBGE table)
        aamm = datetime.now().strftime("%y%m")
        cnpj = self.company.cnpj.replace(".", "").replace("/", "").replace("-", "") if self.company.cnpj else "00000000000000"
        mod = "55" # NFe
        serie = f"{self.series:03d}"
        nNM = f"{self.seq:09d}"
        tpEmis = "1" # Normal
        cNF = f"{random.randint(0, 99999999):08d}" # Código numérico aleatório
        
        base_key = f"{uf}{aamm}{cnpj}{mod}{serie}{nNM}{tpEmis}{cNF}"
        dv = self.calculate_dv(base_key)
        
        return f"{base_key}{dv}"

    def calculate_dv(self, key):
        """Cálculo do Dígito Verificador (Módulo 11)"""
        weights = [4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        soma = 0
        for i, char in enumerate(key):
            soma += int(char) * weights[i]
        
        resto = soma % 11
        if resto == 0 or resto == 1:
            return "0"
        else:
            return str(11 - resto)

    def build_xml(self):
        """Constrói o XML da NFe 4.00 com dados reais"""
        recipient_data = self.data.get('recipient') or {}
        recipient_doc = str(recipient_data.get('doc') or '').replace(".", "").replace("/", "").replace("-", "")
        recipient_name = recipient_data.get('name') or recipient_data.get('companyName') or 'CONSUMIDOR'
        
        # Limita nome do destinatário para SEFAZ
        if self.company.fiscal_environment != 'production':
            recipient_name = "NF-E EMITIDA EM AMBIENTE DE HOMOLOGACAO - SEM VALOR FISCAL"
            
        is_cnpj = len(recipient_doc) > 11
        doc_tag = "CNPJ" if is_cnpj else "CPF"

        # Itens
        det_xml = ""
        total_prod = 0
        for i, item in enumerate(self.data.get('items') or [], 1):
            qty = float(item.get('qty', 1))
            price = float(item.get('price', 0))
            item_total = qty * price
            total_prod += item_total
            
            det_xml += f"""
        <det nItem="{i}">
            <prod>
                <cProd>{item.get('code', f'{i:04d}')}</cProd>
                <cEAN>SEM GTIN</cEAN>
                <xProd>{item.get('desc', 'PRODUCO SEM DESCRICAO')[:120]}</xProd>
                <NCM>89039900</NCM>
                <CFOP>5102</CFOP>
                <uCom>UN</uCom>
                <qCom>{qty:.4f}</qCom>
                <vUnCom>{price:.2f}</vUnCom>
                <vProd>{item_total:.2f}</vProd>
                <cEANTrib>SEM GTIN</cEANTrib>
                <uTrib>UN</uTrib>
                <qTrib>{qty:.4f}</qTrib>
                <vUnTrib>{price:.2f}</vUnTrib>
                <indTot>1</indTot>
            </prod>
            <imposto>
                <vTotTrib>0.00</vTotTrib>
                <ICMS>
                    <ICMSSN102>
                        <orig>0</orig>
                        <CSOSN>102</CSOSN>
                    </ICMSSN102>
                </ICMS>
                <PIS>
                    <PISOutr>
                        <CST>99</CST>
                        <vBC>0.00</vBC>
                        <pPIS>0.00</pPIS>
                        <vPIS>0.00</vPIS>
                    </PISOutr>
                </PIS>
                <COFINS>
                    <COFINSOutr>
                        <CST>99</CST>
                        <vBC>0.00</vBC>
                        <pCOFINS>0.00</pCOFINS>
                        <vCOFINS>0.00</vCOFINS>
                    </COFINSOutr>
                </COFINS>
            </imposto>
        </det>"""

        recipient_addr = recipient_data.get('address') or {}
        
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<NFe xmlns="http://www.portalfiscal.inf.br/nfe">
    <infNFe Id="NFe{self.access_key}" versao="4.00">
        <ide>
            <cUF>41</cUF>
            <cNF>{self.access_key[35:43]}</cNF>
            <natOp>{self.data.get('naturezaOperacao', 'Venda de Mercadoria')}</natOp>
            <mod>55</mod>
            <serie>{self.series}</serie>
            <nNF>{self.seq}</nNF>
            <dhEmi>{format_date_sefaz(datetime.now())}</dhEmi>
            <tpNF>1</tpNF>
            <idDest>1</idDest>
            <cMunFG>{self.company.city_code or '4118204'}</cMunFG>
            <tpImp>1</tpImp>
            <tpEmis>1</tpEmis>
            <cDV>{self.access_key[43]}</cDV>
            <tpAmb>{'1' if self.company.fiscal_environment == 'production' else '2'}</tpAmb>
            <finNFe>1</finNFe>
            <indFinal>1</indFinal>
            <indPres>1</indPres>
            <procEmi>0</procEmi>
            <verProc>ViverdiNautica 1.0</verProc>
        </ide>
        <emit>
            <CNPJ>{self.company.cnpj.replace(".", "").replace("/", "").replace("-", "")}</CNPJ>
            <xNome>{self.company.company_name[:60]}</xNome>
            <xFant>{(self.company.trade_name or self.company.company_name)[:60]}</xFant>
            <enderEmit>
                <xLgr>{self.company.street[:60]}</xLgr>
                <nro>{self.company.number[:10]}</nro>
                <xBairro>{self.company.neighborhood[:60]}</xBairro>
                <cMun>{self.company.city_code or '4118204'}</cMun>
                <xMun>{self.company.city[:60]}</xMun>
                <UF>{self.company.state}</UF>
                <CEP>{self.company.zip_code.replace("-", "") if self.company.zip_code else "83200000"}</CEP>
                <cPais>1058</cPais>
                <xPais>BRASIL</xPais>
            </enderEmit>
            <IE>{self.company.ie.replace(".", "").replace("-", "") if self.company.ie else ""}</IE>
            <CRT>{self.company.crt or "1"}</CRT>
        </emit>
        <dest>
            <{doc_tag}>{recipient_doc}</{doc_tag}>
            <xNome>{recipient_name[:60]}</xNome>
            <enderDest>
                <xLgr>{recipient_addr.get('street', 'CONDOMINIO RESIDENCIAL')[:60]}</xLgr>
                <nro>{recipient_addr.get('number', 'SN')[:10]}</nro>
                <xBairro>{recipient_addr.get('neighborhood', 'CENTRO')[:60]}</xBairro>
                <cMun>{recipient_addr.get('city_code', '4118204')}</cMun>
                <xMun>{recipient_addr.get('city', 'PARANAGUA')[:60]}</xMun>
                <UF>{recipient_addr.get('state', 'PR')}</UF>
                <CEP>{str(recipient_addr.get('zip') or '83200000').replace("-", "")}</CEP>
                <cPais>1058</cPais>
                <xPais>BRASIL</xPais>
            </enderDest>
            <indIEDest>9</indIEDest>
        </dest>{det_xml}
        <total>
            <ICMSTot>
                <vBC>0.00</vBC>
                <vICMS>0.00</vICMS>
                <vICMSDeson>0.00</vICMSDeson>
                <vFCP>0.00</vFCP>
                <vBCST>0.00</vBCST>
                <vST>0.00</vST>
                <vFCPST>0.00</vFCPST>
                <vFCPSTRet>0.00</vFCPSTRet>
                <vProd>{total_prod:.2f}</vProd>
                <vFrete>0.00</vFrete>
                <vSeg>0.00</vSeg>
                <vDesc>0.00</vDesc>
                <vII>0.00</vII>
                <vIPI>0.00</vIPI>
                <vIPIDevol>0.00</vIPIDevol>
                <vPIS>0.00</vPIS>
                <vCOFINS>0.00</vCOFINS>
                <vOutro>0.00</vOutro>
                <vNF>{total_prod:.2f}</vNF>
            </ICMSTot>
        </total>
        <transp>
            <modFrete>9</modFrete>
        </transp>
    </infNFe>
</NFe>"""
