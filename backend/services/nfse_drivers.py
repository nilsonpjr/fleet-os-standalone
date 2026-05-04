
# backend/services/nfse_drivers.py
from datetime import datetime
import random

def format_date_abrasf(dt):
    """Formata data para padrão ABRASF: AAAA-MM-DDTHH:MM:SS"""
    return dt.strftime("%Y-%m-%dT%H:%M:%S")

def format_date_dbseller(dt):
    """Formata data para padrão DBSeller: DD/MM/AAAA"""
    return dt.strftime("%d/%m/%Y")

class CuritibaDriver:
    """
    Driver para emissão de NFSe em Curitiba - PR
    Padrão: ABRASF 2.03
    """
    def __init__(self, invoice_data, company_info, seq_rps):
        self.data = invoice_data
        self.company = company_info
        self.seq = seq_rps
        
    def build_rps_xml(self):
        """Gera o XML do Lote RPS para envio (ABRASF)"""
        recipient_data = self.data.get('recipient') or {}
        recipient_doc = str(recipient_data.get('doc') or '').replace(".", "").replace("/", "").replace("-", "")
        recipient_name = recipient_data.get('name') or recipient_data.get('companyName') or 'CONSUMIDOR'
        # Simplificação do XML
        return f"""
<EnviarLoteRpsEnvio xmlns="http://www.abrasf.org.br/nfse.xsd">
    <LoteRps Id="Lote{self.seq}" versao="2.03">
        <NumeroLote>{self.seq}</NumeroLote>
        <Cnpj>{self.company.cnpj.replace(".", "").replace("/", "").replace("-", "")}</Cnpj>
        <InscricaoMunicipal>{self.company.im if hasattr(self.company, 'im') else '000000'}</InscricaoMunicipal>
        <QuantidadeRps>1</QuantidadeRps>
        <ListaRps>
            <Rps>
                <InfDeclaracaoPrestacaoServico Id="Rps{self.seq}">
                    <Rps>
                        <IdentificacaoRps>
                            <Numero>{self.seq}</Numero>
                            <Serie>1</Serie>
                            <Tipo>1</Tipo>
                        </IdentificacaoRps>
                        <DataEmissao>{format_date_abrasf(datetime.now())}</DataEmissao>
                        <Status>1</Status>
                    </Rps>
                    <Competencia>{datetime.now().strftime("%Y-%m-%d")}</Competencia>
                    <Servico>
                        <Valores>
                            <ValorServicos>{self.data.get('serviceValue', 0)}</ValorServicos>
                            <ValoresRetidos>
                                <ValorIss>0</ValorIss>
                                <ValorPis>0</ValorPis>
                                <ValorCofins>0</ValorCofins>
                                <ValorInss>0</ValorInss>
                                <ValorIr>0</ValorIr>
                                <ValorCsll>0</ValorCsll>
                            </ValoresRetidos>
                            <IssRetido>2</IssRetido> <!-- 2=Não -->
                            <ValorIss>0</ValorIss>
                            <ValorLiquidoNfse>{self.data.get('serviceValue', 0)}</ValorLiquidoNfse>
                        </Valores>
                        <IssRetido>2</IssRetido>
                        <ItemListaServico>14.01</ItemListaServico> <!-- Exemplo Manutenção -->
                        <CodigoCnae>3314710</CodigoCnae> <!-- Exemplo Manutenção Motores -->
                        <Discriminacao>{self.data.get('description', 'Serviço Prestado')}</Discriminacao>
                        <CodigoMunicipio>4106902</CodigoMunicipio>
                    </Servico>
                    <Prestador>
                        <CpfCnpj>
                            <Cnpj>{self.company.cnpj.replace(".", "").replace("/", "").replace("-", "")}</Cnpj>
                        </CpfCnpj>
                        <InscricaoMunicipal>{self.company.im if hasattr(self.company, 'im') else '000000'}</InscricaoMunicipal>
                    </Prestador>
                    <Tomador>
                        <IdentificacaoTomador>
                            <CpfCnpj>
                                <Cnpj>{recipient_doc}</Cnpj>
                            </CpfCnpj>
                        </IdentificacaoTomador>
                        <RazaoSocial>{recipient_name}</RazaoSocial>
                        <Endereco>
                            <Endereco>Rua Teste</Endereco>
                            <Numero>100</Numero>
                            <Bairro>Centro</Bairro>
                            <CodigoMunicipio>4106902</CodigoMunicipio>
                            <Uf>PR</Uf>
                            <Cep>80000000</Cep>
                        </Endereco>
                    </Tomador>
                    <OptanteSimplesNacional>1</OptanteSimplesNacional>
                    <IncentivoFiscal>2</IncentivoFiscal>
                </InfDeclaracaoPrestacaoServico>
            </Rps>
        </ListaRps>
    </LoteRps>
</EnviarLoteRpsEnvio>
"""

class ParanaguaDriver:
    """
    Driver para emissão de NFSe em Paranaguá - PR
    Padrão: DBSeller (Fly e-Nota) / IPM (Modelo variável, ajustado para DBSeller comum)
    """
    def __init__(self, invoice_data, company_info, seq_rps):
        self.data = invoice_data
        self.company = company_info
        self.seq = seq_rps
        
    def build_rps_xml(self):
        """Gera o XML específico de Paranaguá"""
        recipient_data = self.data.get('recipient') or {}
        recipient_doc = str(recipient_data.get('doc') or '').replace(".", "").replace("/", "").replace("-", "")
        recipient_name = recipient_data.get('name') or recipient_data.get('companyName') or 'CONSUMIDOR'
        # DBSeller geralmente usa um XML mais simples ou SOAP direto
        # Mocking a structure compatible with many minor layouts
        return f"""
<nfe>
    <lote>{self.seq}</lote>
    <seq>{self.seq}</seq>
    <dt_emissao>{format_date_dbseller(datetime.now())}</dt_emissao>
    <prestador>
        <cnpj>{self.company.cnpj.replace(".", "").replace("/", "").replace("-", "")}</cnpj>
        <im>{self.company.im if hasattr(self.company, 'im') else '000000'}</im>
    </prestador>
    <tomador>
        <documento>{recipient_doc}</documento>
        <nome>{recipient_name}</nome>
    </tomador>
    <servicos>
        <servico>
            <codigo>1401</codigo>
            <discriminacao>{self.data.get('description', 'Serviço Prestado')}</discriminacao>
            <valor>{self.data.get('serviceValue', 0)}</valor>
            <aliquota>2.00</aliquota>
            <iss>0.00</iss>
        </servico>
    </servicos>
</nfe>
"""
