import crcmod
import qrcode
import io
import base64
from typing import Optional

class PaymentService:
    @staticmethod
    def generate_static_pix(
        pix_key: str, 
        merchant_name: str, 
        merchant_city: str, 
        amount: float, 
        description: Optional[str] = None
    ) -> str:
        """
        Gera a string do Pix Estático (EMV BR Code).
        """
        # Formata o valor com 2 casas decimais
        amount_str = f"{amount:.2f}"
        
        # Limpa merchant_name e merchant_city (máximo 25 e 15 chars, sem caracteres especiais)
        import unicodedata
        def clean_str(s):
            return "".join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn' and (c.isalnum() or c.isspace())).upper()

        merchant_name = clean_str(merchant_name)[:25]
        merchant_city = clean_str(merchant_city)[:15]

        # Payload Format Indicator
        payload = "000201"

        # Merchant Account Information - Pix
        # GUI (00): br.gov.bcb.pix
        # Chave (01): pix_key
        # Info Adicional (02): description (opcional)
        gui = "br.gov.bcb.pix"
        inner_payload = f"00{len(gui):02d}{gui}01{len(pix_key):02d}{pix_key}"
        if description:
            description = clean_str(description)[:25]
            inner_payload += f"02{len(description):02d}{description}"

        payload += f"26{len(inner_payload):02d}{inner_payload}"

        # Merchant Category Code (Fixed 0000)
        payload += "52040000"

        # Transaction Currency (986 = BRL)
        payload += "5303986"

        # Transaction Amount
        payload += f"54{len(amount_str):02d}{amount_str}"

        # Country Code (BR)
        payload += "5802BR"

        # Merchant Name
        payload += f"59{len(merchant_name):02d}{merchant_name}"

        # Merchant City
        payload += f"60{len(merchant_city):02d}{merchant_city}"

        # Additional Data Field (TXID)
        txid = "***"
        inner_additional = f"05{len(txid):02d}{txid}"
        payload += f"62{len(inner_additional):02d}{inner_additional}"

        # CRC16
        payload += "6304"
        
        # Calcula CRC16
        crc16 = crcmod.predefined.Crc('crc-ccitt-false')
        crc16.update(payload.encode('utf-8'))
        payload += crc16.hexdigest().upper()
        
        return payload

    @staticmethod
    def generate_qr_code_base64(pix_string: str) -> str:
        """
        Gera um QR Code em Base64 a partir da string do Pix.
        """
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(pix_string)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        return f"data:image/png;base64,{img_str}"

payment_service = PaymentService()
