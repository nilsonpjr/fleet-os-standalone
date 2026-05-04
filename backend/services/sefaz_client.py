# backend/services/sefaz_client.py
import requests
import ssl
import base64
import tempfile
import os
from lxml import etree
from cryptography.hazmat.primitives.serialization import pkcs12, Encoding, PrivateFormat, NoEncryption
from cryptography.hazmat.backends import default_backend
from .sefaz_constants import URLS

class SefazAdapter(requests.adapters.HTTPAdapter):
    """
    Adaptador para o requests que injeta o certificado A1 na conexão SSL.
    """
    def __init__(self, cert_data, password):
        self.cert_data = cert_data
        self.password = password
        super().__init__()

    def init_poolmanager(self, *args, **kwargs):
        context = ssl.create_default_context()
        
        # Extrair cert e key do PFX
        pfx_content = base64.b64decode(self.cert_data)
        private_key, certificate, additional_certificates = pkcs12.load_key_and_certificates(
            pfx_content,
            self.password.encode() if self.password else None,
            default_backend()
        )

        # Requests/SSL do Python ainda exigem arquivos temporários para o contexto de baixo nível
        # ou o uso de pyOpenSSL. Como não temos pyOpenSSL, usaremos arquivos temporários seguros.
        with tempfile.NamedTemporaryFile(delete=False) as cert_file, \
             tempfile.NamedTemporaryFile(delete=False) as key_file:
            
            cert_file.write(certificate.public_bytes(Encoding.PEM))
            key_file.write(private_key.private_bytes(
                Encoding.PEM, 
                PrivateFormat.TraditionalOpenSSL, 
                NoEncryption()
            ))
            
            cert_path = cert_file.name
            key_path = key_file.name

        context.load_cert_chain(certfile=cert_path, keyfile=key_path)
        kwargs['ssl_context'] = context
        
        # Limpar arquivos temporários após carregar no contexto
        os.unlink(cert_path)
        os.unlink(key_path)
        
        return super().init_poolmanager(*args, **kwargs)

class SefazClient:
    def __init__(self, cert_base64, cert_pass, environment='homologation'):
        self.cert_base64 = cert_base64
        self.cert_pass = cert_pass
        self.env = environment
        self.session = requests.Session()
        self.session.mount('https://', SefazAdapter(cert_base64, cert_pass))

    def _build_soap_envelope(self, body_xml_str):
        """Envelopa o XML da NFe em um SOAP 1.2 Envelope"""
        # Remove a declaração XML UTF-8 se houver no body
        if '<?xml' in body_xml_str:
            body_xml_str = body_xml_str.split('?>')[-1].strip()

        soap = f"""<?xml version="1.0" encoding="utf-8"?>
<soap12:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
                 xmlns:xsd="http://www.w3.org/2001/XMLSchema" 
                 xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">
    <soap12:Body>
        <nfeDadosMsg xmlns="http://www.portalfiscal.inf.br/nfe/wsdl/NFeAutorizacao4">
            {body_xml_str}
        </nfeDadosMsg>
    </soap12:Body>
</soap12:Envelope>"""
        return soap

    def send_nfe(self, signed_xml_str):
        """Envia a NFe para autorização"""
        url = URLS[self.env]['NFeAutorizacao']
        soap_content = self._build_soap_envelope(signed_xml_str)
        
        headers = {
            'Content-Type': 'application/soap+xml; charset=utf-8',
            'SOAPAction': 'http://www.portalfiscal.inf.br/nfe/wsdl/NFeAutorizacao4'
        }

        try:
            response = self.session.post(url, data=soap_content.encode('utf-8'), headers=headers, timeout=30)
            response.raise_for_status()
            return response.text
        except Exception as e:
            raise Exception(f"Erro na comunicação com SEFAZ: {str(e)}")

    def parse_response(self, response_xml):
        """Extrai dados relevantes do retorno SOAP da SEFAZ"""
        try:
            parser = etree.XMLParser(recover=True)
            root = etree.fromstring(response_xml.encode('utf-8'), parser)
            
            ns = {"ns": "http://www.portalfiscal.inf.br/nfe"}
            
            ret_env = root.find(".//ns:retEnviNFe", namespaces=ns)
            if ret_env is not None:
                c_stat_lote = ret_env.find("ns:cStat", namespaces=ns).text
                x_motivo_lote = ret_env.find("ns:xMotivo", namespaces=ns).text
                
                # Se for 104 (Lote processado), buscamos o protocolo da nota
                prot_nfe = ret_env.find(".//ns:protNFe", namespaces=ns)
                if prot_nfe is not None:
                    inf_prot = prot_nfe.find("ns:infProt", namespaces=ns)
                    c_stat_nfe = inf_prot.find("ns:cStat", namespaces=ns).text
                    x_motivo_nfe = inf_prot.find("ns:xMotivo", namespaces=ns).text
                    n_prot = inf_prot.find("ns:nProt", namespaces=ns).text if inf_prot.find("ns:nProt", namespaces=ns) is not None else None
                    
                    return {
                        'cStat': c_stat_nfe,
                        'xMotivo': x_motivo_nfe,
                        'nProt': n_prot,
                        'isLote': False
                    }
                
                # Se for 103 (Lote Recebido - Assíncrono), pegamos o recibo
                inf_rec = ret_env.find("ns:infRec", namespaces=ns)
                if inf_rec is not None:
                    n_rec = inf_rec.find("ns:nRec", namespaces=ns).text
                    return {
                        'cStat': c_stat_lote,
                        'xMotivo': x_motivo_lote,
                        'nRec': n_rec,
                        'isLote': True
                    }
                
                return {
                    'cStat': c_stat_lote,
                    'xMotivo': x_motivo_lote
                }
            
            return {'cStat': '999', 'xMotivo': 'Resposta SEFAZ não reconhecida ou vazia.'}
        except Exception as e:
            return {'cStat': '999', 'xMotivo': f'Erro ao ler resposta SEFAZ: {str(e)}'}
