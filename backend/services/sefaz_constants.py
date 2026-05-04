# backend/services/sefaz_constants.py

# URLs SEFAZ Paraná (PR) - Versão 4.00
URLS = {
    'production': {
        'NFeAutorizacao': 'https://nfe.fazenda.pr.gov.br/nfe/NFeAutorizacao4',
        'NFeRetAutorizacao': 'https://nfe.fazenda.pr.gov.br/nfe/NFeRetAutorizacao4',
        'NFeStatusServico': 'https://nfe.fazenda.pr.gov.br/nfe/NFeStatusServico4',
        'NFeConsultaProtocolo': 'https://nfe.fazenda.pr.gov.br/nfe/NFeConsultaProtocolo4',
    },
    'homologation': {
        'NFeAutorizacao': 'https://homologacao.nfe.fazenda.pr.gov.br/nfe/NFeAutorizacao4',
        'NFeRetAutorizacao': 'https://homologacao.nfe.fazenda.pr.gov.br/nfe/NFeRetAutorizacao4',
        'NFeStatusServico': 'https://homologacao.nfe.fazenda.pr.gov.br/nfe/NFeStatusServico4',
        'NFeConsultaProtocolo': 'https://homologacao.nfe.fazenda.pr.gov.br/nfe/NFeConsultaProtocolo4',
    }
}

# Namespaces SOAP/NFe
NAMESPACES = {
    'soap12': 'http://www.w3.org/2003/05/soap-envelope',
    'nfe': 'http://www.portalfiscal.inf.br/nfe/wsdl/NFeAutorizacao4'
}

# Código de Status Comuns (cStat)
STATUS_AUTORIZADO = "100"
STATUS_LOTE_RECEBIDO = "103"
STATUS_LOTE_EM_PROCESSAMENTO = "105"
