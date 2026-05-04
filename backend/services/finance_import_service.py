import pandas as pd
import pdfplumber
from ofxtools.Parser import OFXTree
from io import BytesIO
from datetime import datetime
import re
import logging

logger = logging.getLogger(__name__)

class FinanceImportService:
    @staticmethod
    def parse_csv(file_content: bytes):
        """
        Parses a CSV file and returns a list of transaction dictionaries.
        Tries to identify columns automatically.
        """
        try:
            df = pd.read_csv(BytesIO(file_content))
            return FinanceImportService._dataframe_to_transactions(df)
        except Exception as e:
            logger.error(f"Error parsing CSV: {e}")
            raise ValueError(f"Não foi possível processar o arquivo CSV: {str(e)}")

    @staticmethod
    def parse_ofx(file_content: bytes):
        """
        Parses an OFX file and returns a list of transaction dictionaries.
        """
        try:
            parser = OFXTree()
            parser.parse(BytesIO(file_content))
            ofx = parser.convert()
            
            transactions = []
            # OFX structure can vary, usually it's in statements
            for stmt in ofx.statements:
                for txn in stmt.banktranlist:
                    transactions.append({
                        "date": txn.dtposted,
                        "description": txn.memo or txn.name,
                        "amount": float(txn.trnamt),
                        "type": "INCOME" if float(txn.trnamt) > 0 else "EXPENSE",
                        "category": "Importado (OFX)",
                        "document_number": txn.fitid
                    })
            return transactions
        except Exception as e:
            logger.error(f"Error parsing OFX: {e}")
            raise ValueError(f"Não foi possível processar o arquivo OFX: {str(e)}")

    @staticmethod
    def parse_pdf(file_content: bytes):
        """
        Parses a PDF file and extract transaction-like lines.
        This is heuristic-based because bank PDFs vary wildly.
        """
        transactions = []
        try:
            with pdfplumber.open(BytesIO(file_content)) as pdf:
                full_text = ""
                for page in pdf.pages:
                    full_text += page.extract_text() + "\n"
                
                # Simple heuristic: Look for lines that start with a date (DD/MM/YYYY or DD/MM)
                # followed by some text and then a value at the end.
                lines = full_text.split('\n')
                date_pattern = r'(\d{2}/\d{2}(?:/\d{4})?)'
                value_pattern = r'(-?[\d\.]+,\d{2})'
                
                for line in lines:
                    dates = re.findall(date_pattern, line)
                    values = re.findall(value_pattern, line)
                    
                    if dates and values:
                        # Take the first date and the last value (usually the amount)
                        date_str = dates[0]
                        amount_str = values[-1].replace('.', '').replace(',', '.')
                        amount = float(amount_str)
                        
                        # Description is what's between date and value
                        description = line.replace(date_str, '').replace(values[-1], '').strip()
                        
                        # Convert date_str to datetime
                        try:
                            if len(date_str) == 5: # DD/MM
                                date_obj = datetime.strptime(f"{date_str}/{datetime.now().year}", "%d/%m/%Y")
                            else: # DD/MM/YYYY
                                date_obj = datetime.strptime(date_str, "%d/%m/%Y")
                        except:
                            date_obj = datetime.now()

                        transactions.append({
                            "date": date_obj,
                            "description": description,
                            "amount": abs(amount),
                            "type": "INCOME" if amount > 0 else "EXPENSE",
                            "category": "Importado (PDF)",
                            "status": "PAID"
                        })
            return transactions
        except Exception as e:
            logger.error(f"Error parsing PDF: {e}")
            raise ValueError(f"Não foi possível processar o arquivo PDF: {str(e)}")

    @staticmethod
    def _dataframe_to_transactions(df):
        """
        Helper to convert a pandas DataFrame to a list of transaction dicts by guessing columns.
        """
        # Try to find date, description and amount columns
        cols = df.columns.tolist()
        date_col = next((c for c in cols if 'data' in c.lower() or 'date' in c.lower()), cols[0])
        desc_col = next((c for c in cols if 'desc' in c.lower() or 'hist' in c.lower() or 'memo' in c.lower()), cols[1] if len(cols) > 1 else cols[0])
        amount_col = next((c for c in cols if 'valor' in c.lower() or 'amount' in c.lower() or 'pago' in c.lower() or 'recebido' in c.lower()), cols[-1])

        transactions = []
        for _, row in df.iterrows():
            try:
                date_val = str(row[date_col])
                # Try common formats
                try:
                    date_obj = pd.to_datetime(date_val, dayfirst=True).to_pydatetime()
                except:
                    date_obj = datetime.now()

                amount = float(str(row[amount_col]).replace(',', '.'))
                
                transactions.append({
                    "date": date_obj,
                    "description": str(row[desc_col]),
                    "amount": abs(amount),
                    "type": "INCOME" if amount > 0 else "EXPENSE",
                    "category": "Importado (CSV)",
                    "status": "PAID"
                })
            except:
                continue
        return transactions
