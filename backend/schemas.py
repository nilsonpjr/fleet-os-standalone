"""
Este arquivo define os esquemas (schemas) de dados usando Pydantic.
Esses esquemas são usados para validação de entrada de dados (requisições) e
serialização de saída de dados (respostas) para a API. Eles garantem que
os dados enviados e recebidos pela API estejam em um formato consistente e válido.
"""

from pydantic import BaseModel, EmailStr, ConfigDict, Field
from pydantic.alias_generators import to_camel
from typing import Optional, List, Dict, Any
from datetime import datetime
# Importa os enums definidos nos modelos para uso nos schemas.
from backend.models import UserRole, OSStatus, ItemType, MovementType, DeliveryType, ComplexityType

# Configuração base para converter snake_case (Python) para camelCase (JavaScript/JSON)
# e permitir a criação de modelos a partir de instâncias ORM (from_attributes).
class CamelModel(BaseModel):
    """
    Classe base para todos os schemas Pydantic, configurando:
    - `alias_generator=to_camel`: Converte automaticamente nomes de campos de snake_case (Python)
      para camelCase (JSON), o padrão em muitas APIs e frontends JavaScript.
    - `populate_by_name=True`: Permite que os campos sejam preenchidos tanto pelo nome original (snake_case)
      quanto pelo alias (camelCase).
    - `from_attributes=True`: Permite que os modelos Pydantic sejam criados a partir de
      instâncias de objetos ORM (como os modelos SQLAlchemy).
    """
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True
    )

# --- USER SCHEMAS ---
# Esquemas para validação e serialização de dados relacionados a usuários.

class UserBase(CamelModel):
    """
    Schema base para um usuário, contendo os campos comuns.
    """
    email: EmailStr # Endereço de email, validado como um formato de email.
    name: str # Nome do usuário.
    role: UserRole # Papel do usuário, usando o Enum UserRole.
    client_id: Optional[int] = None # ID do cliente associado, opcional.

class UserCreate(UserBase):
    """
    Schema para criação de um novo usuário.
    Inclui o campo 'password', que não é retornado na leitura.
    """
    password: str # Senha do usuário (texto puro, será hashed antes de salvar).

class UserUpdate(CamelModel):
    """
    Schema para atualização de um usuário.
    Todos os campos são opcionais.
    """
    name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    role: Optional[UserRole] = None
    client_id: Optional[int] = None
    preferences: Optional[dict] = None

class User(UserBase):
    """
    Schema para representação completa de um usuário (para leitura/resposta da API).
    Inclui o 'id' gerado pelo banco de dados.
    """
    id: int # ID único do usuário.
    tenant_id: int # ID do tenant.
    tenant_plan: Optional[str] = "START" # NOVO: Plano do tenant para controle de features no frontend.
    preferences: Optional[dict] = {}

class TenantSignup(CamelModel):
    """
    Schema para cadastro de nova empresa (Tenant) + Usuário Admin.
    """
    company_name: str
    plan: str = "START"
    admin_name: str
    admin_email: EmailStr
    admin_password: str

class Token(CamelModel):
    """
    Schema para tokens de autenticação JWT.
    """
    access_token: str # O token de acesso.
    token_type: str # Tipo do token (ex: "bearer").

class TokenData(CamelModel):
    """
    Schema para os dados contidos dentro do token (payload).
    """
    email: Optional[str] = None # Email do usuário, opcionalmente incluído no token.

# --- SERVICE DEFINITION SCHEMAS ---
# Esquemas para o catálogo de serviços predefinidos.

class ServiceDefinitionBase(CamelModel):
    name: str # Nome do serviço.
    code: Optional[str] = None # Código do serviço (REFIT-*).
    category: Optional[str] = None # Categoria (Mecânica, Casco).
    description: Optional[str] = None # Descrição detalhada.
    default_price: float = 0 # Preço sugerido.
    suggested_parts: Optional[List[Dict[str, Any]]] = None # Peças sugeridas [{sku, qty}]

class ServiceDefinitionCreate(ServiceDefinitionBase):
    pass

class ServiceDefinitionUpdate(CamelModel):
    name: Optional[str] = None
    code: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    default_price: Optional[float] = None
    suggested_parts: Optional[List[Dict[str, Any]]] = None

class ServiceDefinition(ServiceDefinitionBase):
    id: int
    tenant_id: int

# --- CLIENT SCHEMAS ---
# Esquemas para validação e serialização de dados relacionados a clientes.

class ClientBase(CamelModel):
    """
    Schema base para um cliente.
    """
    name: str # Nome ou Razão Social do cliente.
    document: str # CPF ou CNPJ do cliente.
    phone: Optional[str] = None # Telefone de contato.
    email: Optional[str] = None # Email do cliente.
    address: Optional[str] = None # Endereço completo.
    type: Optional[str] = None  # Tipo de cliente: PARTICULAR, EMPRESA, GOVERNO.
    telegram_id: Optional[str] = None # ID do Telegram.
    is_active: bool = True # Flag de soft-delete

class ClientCreate(ClientBase):
    """
    Schema para criação de um novo cliente. Atualmente, igual ao ClientBase.
    """
    pass

class ClientUpdate(CamelModel):
    """
    Schema para atualização de um cliente. Todos os campos são opcionais.
    """
    name: Optional[str] = None
    document: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    type: Optional[str] = None
    telegram_id: Optional[str] = None
    is_active: Optional[bool] = None

class Client(ClientBase):
    """
    Schema para representação completa de um cliente.
    """
    id: int # ID único do cliente.

# --- MARINA SCHEMAS ---
# Esquemas para validação e serialização de dados relacionados a marinas.

class MarinaBase(CamelModel):
    """
    Schema base para uma marina.
    """
    name: str # Nome da marina.
    address: Optional[str] = None # Endereço.
    contact_name: Optional[str] = None # Nome do contato.
    phone: Optional[str] = None # Telefone.
    coordinates: Optional[str] = None # Coordenadas geográficas.
    operating_hours: Optional[str] = None # Horário de funcionamento.

class MarinaCreate(MarinaBase):
    """
    Schema para criação de uma nova marina.
    """
    pass

class Marina(MarinaBase):
    """
    Schema para representação completa de uma marina.
    """
    id: int # ID único da marina.

# --- ENGINE SCHEMAS ---
# Esquemas para validação e serialização de dados relacionados a motores.

class EngineBase(CamelModel):
    """
    Schema base para um motor.
    """
    serial_number: str # Número de série do motor.
    motor_number: Optional[str] = None # Número do motor.
    model: str # Modelo do motor.
    sale_date: Optional[str] = None # Data de venda.
    warranty_status: Optional[str] = None # Status da garantia.
    warranty_validity: Optional[str] = None # Validade da garantia.
    client_name: Optional[str] = None # Nome do cliente.
    hours: int = 0 # Horas de uso.
    year: Optional[int] = None # Ano de fabricação.

class EngineCreate(EngineBase):
    """
    Schema para criação de um novo motor.
    """
    pass

class Engine(EngineBase):
    """
    Schema para representação completa de um motor.
    """
    id: int # ID único do motor.
    boat_id: int # ID da embarcação à qual pertence.

class EngineUpdate(CamelModel):
    """
    Schema para atualização de um motor. Todos os campos são opcionais.
    """
    id: Optional[int] = None # ID do motor a ser atualizado.
    serial_number: Optional[str] = None
    motor_number: Optional[str] = None
    model: Optional[str] = None
    sale_date: Optional[str] = None
    warranty_status: Optional[str] = None
    warranty_validity: Optional[str] = None
    client_name: Optional[str] = None
    hours: Optional[int] = None
    year: Optional[int] = None


# --- BOAT SCHEMAS ---
# Esquemas para validação e serialização de dados relacionados a embarcações.

class BoatBase(CamelModel):
    """
    Schema base para uma embarcação.
    """
    name: str # Nome da embarcação.
    hull_id: str # ID do casco.
    model: Optional[str] = None # Modelo da embarcação.
    usage_type: Optional[str] = None # Tipo de uso.
    client_id: int # ID do cliente proprietário.
    marina_id: Optional[int] = None # ID da marina.

class BoatCreate(BoatBase):
    """
    Schema para criação de uma nova embarcação.
    Inclui uma lista de motores para serem criados junto com a embarcação.
    """
    engines: List[EngineCreate] = [] # Lista de motores para a embarcação.

class BoatUpdate(CamelModel):
    """
    Schema para atualização de uma embarcação.
    Permite atualizar dados da embarcação e a lista de motores.
    """
    name: Optional[str] = None
    hull_id: Optional[str] = None
    model: Optional[str] = None
    usage_type: Optional[str] = None
    client_id: Optional[int] = None
    marina_id: Optional[int] = None
    engines: List[EngineUpdate] = [] # Lista de motores a serem atualizados.

class Boat(BoatBase):
    """
    Schema para representação completa de uma embarcação.
    """
    id: int # ID único da embarcação.
    engines: List[Engine] = [] # Lista completa de motores associados.

# --- PART SCHEMAS ---
# Esquemas para validação e serialização de dados relacionados a peças.

class PartBase(CamelModel):
    """
    Schema base para uma peça.
    """
    sku: str # SKU da peça.
    name: str # Nome da peça.
    barcode: Optional[str] = None # Código de barras.
    quantity: float = 0 # Quantidade em estoque.
    cost: float = 0 # Custo da peça.
    price: float = 0 # Preço de venda.
    min_stock: float = 0 # Estoque mínimo.
    location: Optional[str] = None # Localização no estoque.
    manufacturer: Optional[str] = None # Fabricante (ex: Mercury).
    group: Optional[str] = None
    subgroup: Optional[str] = None
    compatibility: Optional[List[str]] = None
    is_published: bool = False
    public_title: Optional[str] = None
    public_description: Optional[str] = None
    public_price: Optional[float] = None
    public_compare_at_price: Optional[float] = None
    public_image_url: Optional[str] = None
    public_category: Optional[str] = None
    public_slug: Optional[str] = None
    is_featured: bool = False
    show_stock_publicly: bool = False
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None

class PartCreate(PartBase):
    """
    Schema para criação de uma nova peça.
    """
    pass

class PartUpdate(CamelModel):
    """
    Schema para atualização de uma peça. Todos os campos são opcionais.
    """
    name: Optional[str] = None
    quantity: Optional[float] = None
    cost: Optional[float] = None
    price: Optional[float] = None
    min_stock: Optional[float] = None
    location: Optional[str] = None
    manufacturer: Optional[str] = None
    sku: Optional[str] = None
    barcode: Optional[str] = None
    group: Optional[str] = None
    subgroup: Optional[str] = None
    compatibility: Optional[List[str]] = None
    is_published: Optional[bool] = None
    public_title: Optional[str] = None
    public_description: Optional[str] = None
    public_price: Optional[float] = None
    public_compare_at_price: Optional[float] = None
    public_image_url: Optional[str] = None
    public_category: Optional[str] = None
    public_slug: Optional[str] = None
    is_featured: Optional[bool] = None
    show_stock_publicly: Optional[bool] = None
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None

class Part(PartBase):
    """
    Schema para representação completa de uma peça.
    """
    id: int # ID único da peça.
    last_price_updated_at: Optional[datetime] = None # Data última atualização automática.

class BulkPublishRequest(CamelModel):
    """
    Schema para requisição de publicação em massa.
    """
    part_ids: List[int]
    is_published: bool

# --- SERVICE ITEM SCHEMAS ---
# Esquemas para validação e serialização de dados relacionados a itens de serviço.

class ServiceItemBase(CamelModel):
    """
    Schema base para um item de serviço (peça ou mão de obra).
    """
    type: ItemType # Tipo do item (PART ou LABOR).
    description: str # Descrição do item.
    part_id: Optional[int] = None # ID da peça (se for uma peça).
    quantity: float = 1 # Quantidade utilizada.
    unit_cost: float = 0 # Custo unitário.
    unit_price: float # Preço de venda unitário.
    total: float # Valor total (quantidade * preço unitário).
    category: Optional[str] = None # Categoria do serviço
    subcategory: Optional[str] = None # Subcategoria do serviço

class ServiceItemCreate(ServiceItemBase):
    """
    Schema para criação de um novo item de serviço.
    """
    pass

class ServiceItemUpdate(CamelModel):
    """
    Schema para atualização de um item de serviço. Todos os campos são opcionais.
    """
    type: Optional[ItemType] = None
    description: Optional[str] = None
    part_id: Optional[int] = None
    quantity: Optional[float] = None
    unit_cost: Optional[float] = None
    unit_price: Optional[float] = None
    total: Optional[float] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None

class ServiceItem(ServiceItemBase):
    """
    Schema para representação completa de um item de serviço.
    """
    id: int # ID único do item.
    order_id: int # ID da Ordem de Serviço à qual pertence.

# --- ORDER NOTE SCHEMAS ---
# Esquemas para validação e serialização de dados relacionados a notas de ordem de serviço.

class OrderNoteBase(CamelModel):
    """
    Schema base para uma nota de ordem de serviço.
    """
    text: str # Conteúdo da nota.
    user_name: Optional[str] = None # Nome do usuário que adicionou a nota.

class OrderNoteCreate(OrderNoteBase):
    """
    Schema para criação de uma nova nota de ordem de serviço.
    """
    pass

class OrderNote(OrderNoteBase):
    """
    Schema para representação completa de uma nota de ordem de serviço.
    """
    id: int # ID único da nota.
    order_id: int # ID da Ordem de Serviço.
    created_at: datetime # Data e hora de criação.

# --- SERVICE ORDER SCHEMAS ---
# Esquemas para validação e serialização de dados relacionados a ordens de serviço.

class ServiceOrderBase(CamelModel):
    """
    Schema base para uma ordem de serviço.
    """
    boat_id: int # ID da embarcação.
    engine_id: Optional[int] = None # ID do motor.
    description: str # Descrição do serviço.
    diagnosis: Optional[str] = None # Diagnóstico.
    status: OSStatus = OSStatus.PENDING # Status da OS.
    requester: Optional[str] = None # Solicitante.
    technician_name: Optional[str] = None # Técnico responsável.
    scheduled_at: Optional[datetime] = None # Data agendada.
    estimated_duration: Optional[int] = None # Duração estimada em horas.
    checklist: Optional[List[Dict[str, Any]]] = [] # Checklist de itens
    technician_id: Optional[int] = None # ID do técnico associado


class ServiceOrderCreate(ServiceOrderBase):
    """
    Schema para criação de uma nova ordem de serviço.
    """
    pass

class ServiceOrderUpdate(CamelModel):
    """
    Schema para atualização de uma ordem de serviço.
    """
    description: Optional[str] = None
    diagnosis: Optional[str] = None
    status: Optional[OSStatus] = None
    technician_name: Optional[str] = None
    technician_id: Optional[int] = None
    scheduled_at: Optional[datetime] = None
    estimated_duration: Optional[int] = None
    checklist: Optional[List[Dict[str, Any]]] = None

class ServiceOrder(ServiceOrderBase):
    """
    Schema para representação completa de uma ordem de serviço.
    """
    id: int # ID único da OS.
    total_value: float # Valor total da OS.
    created_at: datetime # Data de criação.
    items: Optional[List[ServiceItem]] = [] # Lista de itens de serviço.
    notes: Optional[List[OrderNote]] = [] # Lista de notas.
    checklist: Optional[List[Dict[str, Any]]] = []
    
    # Novos campos para enriquecimento embutidos (calculados)
    boat_name: Optional[str] = None
    client_name: Optional[str] = None
    client_phone: Optional[str] = None
    client_email: Optional[str] = None
    client_telegram_id: Optional[str] = None
    
    # Aliases para compatibilidade com n8n legado
    email: Optional[str] = None
    phone: Optional[str] = None


# --- TRANSACTION SCHEMAS ---
# Esquemas para validação e serialização de dados relacionados a transações financeiras.

class TransactionBase(CamelModel):
    """
    Schema base para uma transação financeira.
    """
    type: str  # Tipo de transação: INCOME (receita) ou EXPENSE (despesa).
    category: str # Categoria da transação.
    description: str # Descrição.
    amount: float # Valor.
    date: datetime # Data da transação.
    status: str = "PENDING"  # Status: PAID, PENDING, CANCELED.
    order_id: Optional[int] = None # ID da OS relacionada (opcional).
    document_number: Optional[str] = None # Número do documento.

class TransactionCreate(TransactionBase):
    """
    Schema para criação de uma nova transação.
    """
    pass

class Transaction(TransactionBase):
    """
    Schema para representação completa de uma transação.
    """
    id: int # ID único da transação.

# --- STOCK MOVEMENT SCHEMAS ---
# Esquemas para validação e serialização de dados relacionados a movimentos de estoque.

class StockMovementBase(CamelModel):
    """
    Schema base para um movimento de estoque.
    """
    part_id: int # ID da peça movimentada.
    type: MovementType # Tipo de movimento (entrada, saída, ajuste), usando o Enum MovementType.
    quantity: float # Quantidade movimentada.
    description: str # Descrição do movimento.
    reference_id: Optional[str] = None # Referência (ex: NFe, OS).
    user: Optional[str] = None # Usuário responsável.

class StockMovementCreate(StockMovementBase):
    """
    Schema para criação de um novo movimento de estoque.
    """
    pass

class StockMovement(StockMovementBase):
    """
    Schema para representação completa de um movimento de estoque.
    """
    id: int # ID único do movimento.
    date: datetime # Data e hora do movimento.

# --- CONFIG SCHEMAS ---
# Esquemas para validação e serialização de dados relacionados à configuração da aplicação.

class ModelBase(CamelModel):
    """
    Schema base para um modelo de embarcação ou motor.
    """
    name: str # Nome do modelo.

class ModelCreate(ModelBase):
    """
    Schema para criação de um novo modelo.
    """
    pass

class Model(ModelBase):
    """
    Schema para representação completa de um modelo.
    """
    id: int # ID único do modelo.
    manufacturer_id: int # ID do fabricante associado.

class ManufacturerBase(CamelModel):
    """
    Schema base para um fabricante.
    """
    name: str # Nome do fabricante.
    type: str # Tipo do fabricante: "BOAT" ou "ENGINE".

class ManufacturerCreate(ManufacturerBase):
    """
    Schema para criação de um novo fabricante.
    """
    pass

class Manufacturer(ManufacturerBase):
    """
    Schema para representação completa de um fabricante.
    """
    id: int # ID único do fabricante.
    models: List[Model] = [] # Lista de modelos associados a este fabricante.

class HomeCarouselSlide(CamelModel):
    image: str
    eyebrow: str
    title: str
    text: str

class HomeMaintenancePoint(CamelModel):
    hours: str
    title: str
    description: str

class HomeContent(CamelModel):
    carousel_slides: List[HomeCarouselSlide] = []
    highlights: List[str] = []
    maintenance_roadmap: List[HomeMaintenancePoint] = []
    curiosities: List[str] = []
    identity_title: Optional[str] = None
    identity_text: Optional[str] = None

class CompanyInfoBase(CamelModel):
    """
    Schema base para informações da empresa.
    """
    company_name: Optional[str] = None # Razão social.
    trade_name: Optional[str] = None # Nome fantasia.
    cnpj: Optional[str] = None # CNPJ.
    ie: Optional[str] = None # Inscrição Estadual.
    im: Optional[str] = None # Inscrição Municipal.
    phone: Optional[str] = None
    whatsapp: Optional[str] = None
    instagram: Optional[str] = None
    street: Optional[str] = None # Rua.
    number: Optional[str] = None # Número.
    neighborhood: Optional[str] = None # Bairro.
    city: Optional[str] = None # Cidade.
    state: Optional[str] = None # Estado.
    zip_code: Optional[str] = None # CEP. # Alterado de 'zip' para 'zip_code' para consistência.
    crt: Optional[str] = None # Código de Regime Tributário.
    environment: Optional[str] = None # Ambiente (production ou homologation)
    mercury_username: Optional[str] = Field(None, alias="mercuryUsername")
    mercury_password: Optional[str] = Field(None, alias="mercuryPassword")
    
    # Fiscal Proprio
    cert_file_path: Optional[str] = None
    cert_base64: Optional[str] = None # Campo transitorio para upload via base64
    cert_password: Optional[str] = None
    fiscal_environment: Optional[str] = "homologation"
    sequence_nfe: Optional[int] = 1
    series_nfe: Optional[int] = 1
    city_code: Optional[str] = "4118204"
    n8n_webhook_url: Optional[str] = Field(None, alias="n8nWebhookUrl")
    
    # Pix
    pix_enabled: Optional[bool] = False
    pix_key: Optional[str] = None
    pix_key_type: Optional[str] = None
    pix_bank_name: Optional[str] = None
    pix_merchant_name: Optional[str] = None
    pix_merchant_city: Optional[str] = None
    hero_title: Optional[str] = None
    hero_subtitle: Optional[str] = None
    hero_image_url: Optional[str] = None
    labor_rate_low: Optional[float] = 0
    labor_rate_medium: Optional[float] = 0
    labor_rate_high: Optional[float] = 0
    home_content: Optional[HomeContent] = None

class CompanyInfoCreate(CompanyInfoBase):
    """
    Schema para criação de informações da empresa.
    """
    pass

class CompanyInfo(CompanyInfoBase):
    """
    Schema para representação completa das informações da empresa.
    """
    id: int # ID único.


class PublicCatalogItem(CamelModel):
    sku: str
    slug: str
    title: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    price: float
    compare_at_price: Optional[float] = None
    category: Optional[str] = None
    available: bool = True
    stock_label: Optional[str] = None
    featured: bool = False


class PublicCatalogResponse(CamelModel):
    items: List[PublicCatalogItem]
    total: int
    page: int
    limit: int
    total_pages: int



class PublicSiteConfig(CamelModel):
    tenant_slug: str
    store_name: str
    whatsapp: Optional[str] = None
    phone: Optional[str] = None
    instagram: Optional[str] = None
    address: Optional[str] = None
    hero_title: Optional[str] = None
    hero_subtitle: Optional[str] = None
    hero_image_url: Optional[str] = None
    labor_rate_low: Optional[float] = 0
    labor_rate_medium: Optional[float] = 0
    labor_rate_high: Optional[float] = 0
    home_content: Optional[HomeContent] = None


class PublicLeadCreate(CamelModel):
    name: str
    phone: str
    email: Optional[EmailStr] = None
    message: Optional[str] = None
    source: Optional[str] = None


class PublicCartCustomer(CamelModel):
    name: str
    phone: str
    email: Optional[EmailStr] = None


class PublicBoatInfo(CamelModel):
    name: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None


class PublicEngineInfo(CamelModel):
    brand: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None


class PublicCartItem(CamelModel):
    sku: str
    slug: Optional[str] = None
    title: str
    quantity: int = 1
    price: float
    service_requested: bool = False


class PublicCartRequestCreate(CamelModel):
    customer: PublicCartCustomer
    boat: Optional[PublicBoatInfo] = None
    engine: Optional[PublicEngineInfo] = None
    items: List[PublicCartItem]
    notes: Optional[str] = None
    source: Optional[str] = None
    channel_preference: Optional[str] = None


class PublicSubmissionResponse(CamelModel):
    status: str
    id: int
    service_order_id: Optional[int] = None
    order_error_message: Optional[str] = None


class PublicLeadAdmin(CamelModel):
    id: int
    name: str
    phone: str
    email: Optional[str] = None
    message: Optional[str] = None
    source: Optional[str] = None
    status: str
    created_at: datetime


class PublicCartRequestAdmin(CamelModel):
    id: int
    customer: Dict[str, Any]
    boat: Optional[Dict[str, Any]] = None
    engine: Optional[Dict[str, Any]] = None
    items: List[Dict[str, Any]]
    notes: Optional[str] = None
    source: Optional[str] = None
    channel_preference: Optional[str] = None
    service_order_id: Optional[int] = None
    order_error_message: Optional[str] = None
    status: str
    created_at: datetime


class PublicInteractionsOverview(CamelModel):
    total_leads: int
    total_cart_requests: int
    new_leads: int
    new_cart_requests: int
    latest_lead_at: Optional[datetime] = None
    latest_cart_request_at: Optional[datetime] = None


# --- MAINTENANCE KIT SCHEMAS ---

class MaintenanceKitItemBase(CamelModel):
    type: ItemType
    part_id: Optional[int] = None
    item_description: str
    quantity: float = 1
    unit_price: float = 0

class MaintenanceKitItemCreate(MaintenanceKitItemBase):
    pass

class MaintenanceKitItem(MaintenanceKitItemBase):
    id: int
    kit_id: int
    part: Optional[Part] = None

class MaintenanceKitBase(CamelModel):
    name: str
    brand: Optional[str] = None
    engine_model: Optional[str] = None
    interval_hours: Optional[int] = None
    description: Optional[str] = None

class MaintenanceKitCreate(MaintenanceKitBase):
    items: List[MaintenanceKitItemCreate] = []

class MaintenanceKitUpdate(CamelModel):
    name: Optional[str] = None
    brand: Optional[str] = None
    engine_model: Optional[str] = None
    interval_hours: Optional[int] = None
    description: Optional[str] = None
    items: Optional[List[MaintenanceKitItemCreate]] = None

class MaintenanceKit(MaintenanceKitBase):
    id: int
    created_at: datetime
    items: List[MaintenanceKitItem] = []


# --- QUICK SALE SCHEMAS ---
class QuickSaleItem(CamelModel):
    part_id: int
    quantity: float
    discount_percent: float = 0.0

class QuickSaleRequest(CamelModel):
    items: List[QuickSaleItem]
    payment_method: Optional[str] = "DINHEIRO"
    notes: Optional[str] = None
    client_name: Optional[str] = "CONSUMIDOR"
    client_doc: Optional[str] = None



# --- PARTNER SCHEMAS ---
# Schemas para rede de parceiros (Fase 3)

# Importar novos enums
from backend.models import PartnerType, InspectionStatus, ChecklistItemSeverity, QuoteStatus

class PartnerBase(CamelModel):
    """Schema base para um parceiro."""
    name: str
    partner_type: PartnerType
    phone: str
    email: Optional[str] = None
    company_name: Optional[str] = None
    document: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None

class PartnerCreate(PartnerBase):
    """Schema para criação de um novo parceiro."""
    pass

class PartnerUpdate(CamelModel):
    """Schema para atualização de um parceiro."""
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    company_name: Optional[str] = None
    document: Optional[str] = None
    address: Optional[str] = None
    partner_type: Optional[PartnerType] = None
    active: Optional[bool] = None
    notes: Optional[str] = None

class Partner(PartnerBase):
    """Schema de resposta para um parceiro."""
    id: int
    rating: float
    total_jobs: int
    active: bool
    created_at: datetime
    updated_at: datetime


# --- TECHNICAL INSPECTION SCHEMAS ---

class InspectionChecklistItemBase(CamelModel):
    """Schema base para item de checklist de inspeção."""
    category: str
    item_description: str
    severity: ChecklistItemSeverity
    notes: Optional[str] = None
    photo_url: Optional[str] = None
    estimated_cost: Optional[float] = None
    recommended_partner_type: Optional[PartnerType] = None

class InspectionChecklistItemCreate(InspectionChecklistItemBase):
    """Schema para criação de item de checklist."""
    pass

class InspectionChecklistItem(InspectionChecklistItemBase):
    """Schema de resposta para item de checklist."""
    id: int
    inspection_id: int
    created_at: datetime


class TechnicalInspectionBase(CamelModel):
    """Schema base para inspeção técnica."""
    boat_id: int
    inspector_user_id: int
    scheduled_date: Optional[datetime] = None
    general_notes: Optional[str] = None

class TechnicalInspectionCreate(TechnicalInspectionBase):
    """Schema para criação de inspeção."""
    pass

class TechnicalInspectionUpdate(CamelModel):
    """Schema para atualização de inspeção."""
    status: Optional[InspectionStatus] = None
    scheduled_date: Optional[datetime] = None
    completed_date: Optional[datetime] = None
    general_notes: Optional[str] = None

class TechnicalInspection(TechnicalInspectionBase):
    """Schema de resposta para inspeção."""
    id: int
    status: InspectionStatus
    completed_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    checklist_items: List[InspectionChecklistItem] = []


# --- PARTNER QUOTE SCHEMAS ---

class PartnerQuoteBase(CamelModel):
    """Schema base para orçamento de parceiro."""
    inspection_id: int
    partner_id: int
    service_description: str

class PartnerQuoteCreate(PartnerQuoteBase):
    """Schema para solicitação de orçamento."""
    pass

class PartnerQuoteUpdate(CamelModel):
    """Schema para atualização de orçamento (pelo parceiro ou interno)."""
    quoted_value: Optional[float] = None
    estimated_days: Optional[int] = None
    status: Optional[QuoteStatus] = None
    partner_notes: Optional[str] = None
    internal_notes: Optional[str] = None
    rating: Optional[float] = None
    rating_comment: Optional[str] = None

class PartnerQuote(PartnerQuoteBase):
    """Schema de resposta para orçamento."""
    id: int
    status: QuoteStatus
    quoted_value: Optional[float]
    estimated_days: Optional[int]
    requested_date: datetime
    response_date: Optional[datetime]
    partner_notes: Optional[str]
    internal_notes: Optional[str]
    rating: Optional[float]
    rating_comment: Optional[str]
    created_at: datetime
    updated_at: datetime
# --- SUBSCRIPTION SCHEMAS ---

class ApiSubscription(CamelModel):
    plan_name: str
    price: float
    features: List[str]
    status: str
    next_billing_date: str

# --- TECHNICAL DELIVERY SCHEMAS ---

class TechnicalDeliveryBase(CamelModel):
    type: str # OUTBOARD or STERNDRIVE
    status: Optional[str] = "DRAFT"
    location: Optional[str] = None
    customer_name: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    technician_signature_url: Optional[str] = None
    customer_signature_url: Optional[str] = None

class TechnicalDeliveryCreate(TechnicalDeliveryBase):
    service_order_id: int

class TechnicalDeliveryUpdate(CamelModel):
    status: Optional[str] = None
    location: Optional[str] = None
    customer_name: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    technician_signature_url: Optional[str] = None
    customer_signature_url: Optional[str] = None

class TechnicalDelivery(TechnicalDeliveryBase):
    id: int
    service_order_id: int
    technician_id: Optional[int] = None
    date: datetime
    created_at: datetime
    updated_at: datetime

# --- SERVICE CATALOG SCHEMAS ---

class ServiceCategoryBase(CamelModel):
    name: str

class ServiceCategoryCreate(ServiceCategoryBase):
    pass

class ServiceCatalogBase(CamelModel):
    name: str
    description: Optional[str] = ""
    standard_time_minutes: Optional[int] = 0
    complexity: ComplexityType
    reference_manufacturer: Optional[str] = None
    subcategory_id: int

class ServiceCatalogCreate(ServiceCatalogBase):
    pass

class ServiceCatalog(ServiceCatalogBase):
    id: int
    class Config:
        from_attributes = True

class ServiceSubcategoryBase(CamelModel):
    name: str
    category_id: int

class ServiceSubcategoryCreate(ServiceSubcategoryBase):
    pass

class ServiceSubcategory(ServiceSubcategoryBase):
    id: int
    services: List[ServiceCatalog] = []
    class Config:
        from_attributes = True

class ServiceCategory(ServiceCategoryBase):
    id: int
    subcategories: List[ServiceSubcategory] = []
    class Config:
        from_attributes = True

class ServiceCatalogUpdate(CamelModel):
    name: Optional[str] = None
    description: Optional[str] = None
    standard_time_minutes: Optional[int] = None
    complexity: Optional[ComplexityType] = None
    reference_manufacturer: Optional[str] = None
    subcategory_id: Optional[int] = None
