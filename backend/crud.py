"""
Este arquivo contém as funções CRUD (Create, Read, Update, Delete)
para interagir com o banco de dados. Cada função é responsável por
uma operação específica em um modelo SQLAlchemy, utilizando uma sessão de banco de dados.
"""

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, or_
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any
import re
import unicodedata

from backend import models
from backend import schemas
from backend.auth import get_password_hash
from backend.security import encrypt_value, decrypt_value # Importa funções de criptografia


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value or "")
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_value).strip("-").lower()
    return cleaned or "item"

# --- USER CRUD ---
# Funções para operações CRUD na tabela de usuários (models.User).

def register_tenant(db: Session, signup_data: schemas.TenantSignup):
    """
    Registra uma nova empresa (Tenant) e seu primeiro usuário Admin.
    Transação atômica.
    """
    # 1. Cria o Tenant
    db_tenant = models.Tenant(
        name=signup_data.company_name,
        plan=signup_data.plan
    )
    db.add(db_tenant)
    db.commit()
    db.refresh(db_tenant)
    
    # 2. Cria o Usuário Admin vinculado ao Tenant
    hashed_password = get_password_hash(signup_data.admin_password)
    db_user = models.User(
        email=signup_data.admin_email,
        name=signup_data.admin_name,
        hashed_password=hashed_password,
        role=models.UserRole.ADMIN, # Primeiro usuário é sempre admin
        tenant_id=db_tenant.id
    )
    db.add(db_user)
    
    # 3. Inicializa CompanyInfo para o Tenant
    db_company = models.CompanyInfo(
        tenant_id=db_tenant.id,
        company_name=signup_data.company_name # Já preenche a Razão Social com o nome informado
    )
    db.add(db_company)
    
    try:
        db.commit()
        db.refresh(db_user)
        return db_user
    except Exception as e:
        db.rollback()
        raise e


def get_user_by_email(db: Session, email: str):
    """
    Busca um usuário pelo endereço de email.
    Args:
        db (Session): Sessão do banco de dados.
        email (str): Endereço de email do usuário.
    Returns:
        models.User: O objeto usuário, se encontrado, ou None.
    """
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user: schemas.UserCreate, tenant_id: int):
    """
    Cria um novo usuário no banco de dados vinculado ao tenant.
    """
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        email=user.email,
        name=user.name,
        hashed_password=hashed_password,
        role=user.role,
        client_id=user.client_id,
        tenant_id=tenant_id
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# --- CLIENT CRUD ---
# Funções para operações CRUD na tabela de clientes (models.Client).

def get_clients(db: Session, tenant_id: int, skip: int = 0, limit: int = 100):
    """
    Retorna uma lista de clientes de um tenant.
    Args:
        db (Session): Sessão do banco de dados.
        tenant_id (int): ID do tenant.
        skip (int): Número de registros a pular (offset para paginação).
        limit (int): Número máximo de registros a retornar.
    Returns:
        List[models.Client]: Lista de objetos cliente.
    """
    return db.query(models.Client).filter(
        models.Client.tenant_id == tenant_id,
        models.Client.is_active == True
    ).offset(skip).limit(limit).all()

def get_client(db: Session, client_id: int, tenant_id: int):
    """
    Busca um cliente pelo ID e tenant_id.
    """
    return db.query(models.Client).filter(
        models.Client.id == client_id,
        models.Client.tenant_id == tenant_id
    ).first()

def get_client_by_phone(db: Session, phone: str, tenant_id: int):
    """
    Busca um cliente pelo número de telefone.
    """
    return db.query(models.Client).filter(
        models.Client.phone.like(f"%{phone}%"),
        models.Client.tenant_id == tenant_id
    ).first()

def create_client(db: Session, client: schemas.ClientCreate, tenant_id: int):
    """
    Cria um novo cliente no banco de dados.
    Args:
        db (Session): Sessão do banco de dados.
        client (schemas.ClientCreate): Dados do cliente para criação.
        tenant_id (int): ID do tenant.
    Returns:
        models.Client: O objeto cliente recém-criado.
    """
    client_data = client.model_dump()
    db_client = models.Client(**client_data, tenant_id=tenant_id)
    db.add(db_client)
    db.commit()
    db.refresh(db_client)
    return db_client

def update_client(db: Session, client_id: int, tenant_id: int, client_update: schemas.ClientUpdate):
    """
    Atualiza um cliente existente pertencente ao tenant.
    """
    db_client = get_client(db, client_id, tenant_id)
    if not db_client:
        return None
    
    update_data = client_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_client, key, value)
    
    db.commit()
    db.refresh(db_client)
    return db_client

def delete_client(db: Session, client_id: int, tenant_id: int):
    """
    Deleta um cliente pertencente ao tenant.
    """
    db_client = get_client(db, client_id, tenant_id)
    if not db_client:
        return None
        
    has_boats = db.query(models.Boat).filter(models.Boat.client_id == client_id).first() is not None
    has_orders = db.query(models.ServiceOrder).filter(models.ServiceOrder.client_id == client_id).first() is not None
    
    # Se o cliente tem barcos ou histório de ordens (mesmo as de outros barcos antigos), forçamos o soft-delete para não quebrar a base de faturamento ou relações.
    if has_boats or has_orders:
        db_client.is_active = False
        db.commit()
        db.refresh(db_client)
        raise ValueError("SOFT_DELETE")
        
    db.delete(db_client)
    db.commit()
    return db_client

# --- MARINA CRUD ---
# Funções para operações CRUD na tabela de marinas (models.Marina).

def get_marinas(db: Session, tenant_id: int):
    """
    Retorna uma lista de todas as marinas de um tenant.
    Args:
        db (Session): Sessão do banco de dados.
        tenant_id (int): ID do tenant.
    Returns:
        List[models.Marina]: Lista de objetos marina.
    """
    return db.query(models.Marina).filter(models.Marina.tenant_id == tenant_id).all()

def create_marina(db: Session, marina: schemas.MarinaCreate, tenant_id: int):
    """
    Cria uma nova marina no banco de dados.
    Args:
        db (Session): Sessão do banco de dados.
        marina (schemas.MarinaCreate): Dados da marina para criação.
        tenant_id (int): ID do tenant.
    Returns:
        models.Marina: O objeto marina recém-criada.
    """
    db_marina = models.Marina(**marina.model_dump(), tenant_id=tenant_id)
    db.add(db_marina)
    db.commit()
    db.refresh(db_marina)
    return db_marina

def get_marina(db: Session, marina_id: int, tenant_id: int):
    """Busca uma marina pelo ID e tenant."""
    return db.query(models.Marina).filter(
        models.Marina.id == marina_id,
        models.Marina.tenant_id == tenant_id
    ).first()

def update_marina(db: Session, marina_id: int, tenant_id: int, marina_update: schemas.MarinaCreate):
    db_marina = get_marina(db, marina_id, tenant_id)
    if not db_marina:
        return None
    
    update_data = marina_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_marina, key, value)
    
    db.commit()
    db.refresh(db_marina)
    return db_marina

def delete_marina(db: Session, marina_id: int, tenant_id: int):
    db_marina = get_marina(db, marina_id, tenant_id)
    if db_marina:
        db.delete(db_marina)
        db.commit()
    return db_marina

# --- BOAT CRUD ---
# Funções para operações CRUD na tabela de embarcações (models.Boat).

def get_boats(db: Session, tenant_id: int, client_id: Optional[int] = None):
    """
    Retorna uma lista de embarcações, filtrada por tenant e opcionalmente por ID do cliente.
    Args:
        db (Session): Sessão do banco de dados.
        tenant_id (int): ID do tenant.
        client_id (Optional[int]): ID do cliente para filtrar as embarcações.
    Returns:
        List[models.Boat]: Lista de objetos embarcação.
    """
    query = db.query(models.Boat).filter(models.Boat.tenant_id == tenant_id)
    if client_id:
        query = query.filter(models.Boat.client_id == client_id)
    return query.all()

def get_boat(db: Session, boat_id: int, tenant_id: int):
    """
    Busca uma embarcação pelo ID e tenant_id.
    """
    return db.query(models.Boat).filter(
        models.Boat.id == boat_id,
        models.Boat.tenant_id == tenant_id
    ).first()

def create_boat(db: Session, boat: schemas.BoatCreate, tenant_id: int):
    """
    Cria uma nova embarcação no banco de dados.
    """
    # Separa os dados da embarcação dos dados dos motores (se houver).
    boat_data = boat.model_dump()
    engines_data = boat_data.pop("engines", [])
    
    # Cria a embarcação com o tenant_id
    db_boat = models.Boat(**boat_data, tenant_id=tenant_id)
    db.add(db_boat)
    db.commit()
    db.refresh(db_boat)
    
    # Cria os motores associados, se houver.
    for engine_data in engines_data:
        db_engine = models.Engine(**engine_data, boat_id=db_boat.id, tenant_id=tenant_id)
        db.add(db_engine)
    
    if engines_data:
        db.commit()
        db.refresh(db_boat)
        
    return db_boat

def update_boat(db: Session, boat_id: int, tenant_id: int, boat_update: schemas.BoatUpdate):
    """
    Atualiza os dados de uma embarcação pertencente ao tenant.
    """
    db_boat = get_boat(db, boat_id, tenant_id)
    if not db_boat:
        return None

    update_data = boat_update.model_dump(exclude_unset=True, exclude={'engines'})
    for key, value in update_data.items():
        setattr(db_boat, key, value)

    # Sincronização de motores (garantindo tenant_id)
    if boat_update.engines is not None:
        existing_engine_ids = {engine.id for engine in db_boat.engines}
        incoming_engine_ids = {engine.id for engine in boat_update.engines if engine.id}

        # Deleta motores sumidos apenas quando eles nao possuem historico
        # em ordens de servico. Isso evita quebrar chaves estrangeiras ao
        # editar um barco que ja teve OS vinculada a um motor antigo.
        for engine_id in existing_engine_ids - incoming_engine_ids:
            engine_to_delete = db.query(models.Engine).filter(
                models.Engine.id == engine_id,
                models.Engine.tenant_id == tenant_id
            ).first()
            if engine_to_delete:
                has_service_orders = db.query(models.ServiceOrder.id).filter(
                    models.ServiceOrder.engine_id == engine_id,
                    models.ServiceOrder.tenant_id == tenant_id
                ).first() is not None

                if not has_service_orders:
                    db.delete(engine_to_delete)

        # Atualiza ou cria
        for engine_data in boat_update.engines:
            if engine_data.id:
                db_engine = db.query(models.Engine).filter(
                    models.Engine.id == engine_data.id,
                    models.Engine.tenant_id == tenant_id
                ).first()
                if db_engine:
                    for key, value in engine_data.model_dump(exclude_unset=True).items():
                        setattr(db_engine, key, value)
            else:
                new_engine = models.Engine(**engine_data.model_dump(exclude={'id'}), boat_id=db_boat.id, tenant_id=tenant_id)
                db.add(new_engine)

    db.commit()
    db.refresh(db_boat)
    return db_boat

def delete_boat(db: Session, boat_id: int, tenant_id: int):
    """
    Deleta uma embarcação pertencente ao tenant.
    """
    db_boat = get_boat(db, boat_id, tenant_id)
    if not db_boat:
        return False
    
    db.delete(db_boat)
    db.commit()
    return True

# --- SERVICE DEFINITION CRUD ---
# Cadastro de catálogo de serviços (Mão de Obra).

def get_service_definitions(db: Session, tenant_id: int):
    """Retorna o catálogo de serviços de um tenant."""
    return db.query(models.ServiceDefinition).filter(models.ServiceDefinition.tenant_id == tenant_id).all()

def get_service_definition(db: Session, service_id: int, tenant_id: int):
    """Busca um serviço pelo ID e tenant."""
    return db.query(models.ServiceDefinition).filter(
        models.ServiceDefinition.id == service_id,
        models.ServiceDefinition.tenant_id == tenant_id
    ).first()

def create_service_definition(db: Session, service: schemas.ServiceDefinitionCreate, tenant_id: int):
    """Cria um novo serviço no catálogo."""
    db_service = models.ServiceDefinition(**service.model_dump(), tenant_id=tenant_id)
    db.add(db_service)
    db.commit()
    db.refresh(db_service)
    return db_service

def update_service_definition(db: Session, service_id: int, tenant_id: int, service_update: schemas.ServiceDefinitionUpdate):
    """Atualiza um serviço do catálogo pertencente ao tenant."""
    db_service = get_service_definition(db, service_id, tenant_id)
    if not db_service:
        return None
    
    update_data = service_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_service, key, value)
    
    db.commit()
    db.refresh(db_service)
    return db_service

def delete_service_definition(db: Session, service_id: int, tenant_id: int):
    """Deleta um serviço do catálogo pertencente ao tenant."""
    db_service = get_service_definition(db, service_id, tenant_id)
    if db_service:
        db.delete(db_service)
        db.commit()
    return db_service

# --- PART CRUD ---
# Funções para operações CRUD na tabela de peças (models.Part).

def get_parts(db: Session, tenant_id: int):
    """
    Retorna uma lista de todas as peças de um tenant.
    Args:
        db (Session): Sessão do banco de dados.
        tenant_id (int): ID do tenant.
    Returns:
        List[models.Part]: Lista de objetos peça.
    """
    return db.query(models.Part).filter(models.Part.tenant_id == tenant_id).all()

def get_part(db: Session, part_id: int, tenant_id: int, lock: bool = False):
    """
    Busca uma peça pelo ID e tenant_id, com opção de lock para transações.
    """
    query = db.query(models.Part).filter(
        models.Part.id == part_id,
        models.Part.tenant_id == tenant_id
    )
    if lock:
        query = query.with_for_update()
    return query.first()

def get_part_by_sku(db: Session, sku: str, tenant_id: Optional[int] = None):
    """
    Busca uma peça pelo SKU.
    Args:
        db (Session): Sessão do banco de dados.
        sku (str): SKU da peça.
        tenant_id (Optional[int]): Se informado, restringe a busca ao tenant.
    Returns:
        models.Part: O objeto peça, se encontrado, ou None.
    """
    query = db.query(models.Part).filter(models.Part.sku == sku)
    if tenant_id is not None:
        query = query.filter(models.Part.tenant_id == tenant_id)
    return query.first()

def create_part(db: Session, part: schemas.PartCreate, tenant_id: int):
    """
    Cria uma nova peça no inventário.
    """
    part_data = part.model_dump()
    public_slug = part_data.get("public_slug")
    if not public_slug:
        public_slug = slugify(part_data.get("public_title") or part_data.get("name") or part_data.get("sku"))
    part_data["public_slug"] = public_slug

    db_part = models.Part(**part_data, tenant_id=tenant_id)
    db.add(db_part)
    db.commit()
    db.refresh(db_part)
    return db_part

def update_part(db: Session, part_id: int, tenant_id: int, part_update: schemas.PartUpdate):
    """
    Atualiza os dados de uma peça pertencente ao tenant.
    """
    db_part = get_part(db, part_id, tenant_id)
    if not db_part:
        return None
    
    update_data = part_update.model_dump(exclude_unset=True)
    if "public_slug" not in update_data and (
        "public_title" in update_data or "name" in update_data or db_part.public_slug in (None, "")
    ):
        update_data["public_slug"] = slugify(
            update_data.get("public_title") or update_data.get("name") or db_part.public_title or db_part.name or db_part.sku
        )
    for key, value in update_data.items():
        setattr(db_part, key, value)
    
    db.commit()
    db.refresh(db_part)
    return db_part

def delete_part(db: Session, part_id: int, tenant_id: int):
    """
    Deleta uma peça do estoque pertencente ao tenant.
    """
    db_part = get_part(db, part_id, tenant_id)
    if not db_part:
        return False
    
    db.delete(db_part)
    db.commit()
    return True

# --- SERVICE ORDER CRUD ---
# Funções para operações CRUD na tabela de ordens de serviço (models.ServiceOrder).

def get_orders(db: Session, tenant_id: int, status: Optional[str] = None):
    """
    Retorna uma lista de ordens de serviço de um tenant, opcionalmente filtrada por status.
    Carrega os itens e notas relacionadas para evitar N+1 queries.
    Args:
        db (Session): Sessão do banco de dados.
        tenant_id (int): ID do tenant.
        status (Optional[str]): Status da OS para filtrar.
    Returns:
        List[models.ServiceOrder]: Lista de objetos ordem de serviço.
    """
    query = db.query(models.ServiceOrder).filter(models.ServiceOrder.tenant_id == tenant_id).options(
        joinedload(models.ServiceOrder.items), # Carrega os itens da OS
        joinedload(models.ServiceOrder.notes) # Carrega as notas da OS
    ).order_by(desc(models.ServiceOrder.created_at)) # Ordena pelas mais recentes
    if status:
        query = query.filter(models.ServiceOrder.status == status)
    return query.all()

def get_order(db: Session, order_id: int, tenant_id: int, lock: bool = False):
    """
    Busca uma ordem de serviço pelo ID e tenant_id, com opção de lock.
    """
    from sqlalchemy.orm import joinedload
    query = db.query(models.ServiceOrder).options(
        joinedload(models.ServiceOrder.items),
        joinedload(models.ServiceOrder.notes),
        joinedload(models.ServiceOrder.boat).joinedload(models.Boat.owner)
    ).filter(
        models.ServiceOrder.id == order_id,
        models.ServiceOrder.tenant_id == tenant_id
    )
    if lock:
        query = query.with_for_update()
    return query.first()

def create_order(db: Session, order: schemas.ServiceOrderCreate, tenant_id: int):
    """
    Cria uma nova ordem de serviço.
    """
    # Define o dono atual do barco no momento da OS para efeitos de snapshot legal
    db_boat = db.query(models.Boat).filter(models.Boat.id == order.boat_id).first()
    client_id = db_boat.client_id if db_boat else None

    db_order = models.ServiceOrder(
        **order.model_dump(), 
        tenant_id=tenant_id,
        client_id=client_id
    )
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return db_order

def update_order(db: Session, order_id: int, tenant_id: int, order_update: schemas.ServiceOrderUpdate):
    """
    Atualiza os dados de uma ordem de serviço pertencente ao tenant.
    """
    db_order = get_order(db, order_id, tenant_id)
    if not db_order:
        return None
    
    update_data = order_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_order, key, value)
    
    db.commit()
    db.refresh(db_order)
    return db_order

def add_order_item(db: Session, order_id: int, tenant_id: int, item: schemas.ServiceItemCreate):
    """
    Adiciona um item a uma OS do tenant e recalcula total.
    """
    # Verifica se a OS pertence ao tenant
    db_order = get_order(db, order_id, tenant_id)
    if not db_order:
        return None

    db_item = models.ServiceItem(**item.model_dump(), order_id=order_id)
    db.add(db_item)
    db.commit()
    
    # Recalcula
    db_order.total_value = sum(i.total for i in db_order.items)
    db.commit()
    db.refresh(db_order)
    
    return db_order

def remove_order_item(db: Session, order_id: int, tenant_id: int, item_id: int):
    """
    Remove um item de uma OS do tenant e recalcula total.
    """
    # Verifica OS e Tenant
    db_order = get_order(db, order_id, tenant_id)
    if not db_order:
        return None

    db_item = db.query(models.ServiceItem).filter(
        models.ServiceItem.id == item_id,
        models.ServiceItem.order_id == order_id
    ).first()
    
    if not db_item:
        return None
        
    db.delete(db_item)
    db.commit()
    
    # Recalcula
    db_order.total_value = sum(i.total for i in db_order.items)
    db.commit()
    db.refresh(db_order)
        
    return db_order

def add_order_note(db: Session, order_id: int, tenant_id: int, note: schemas.OrderNoteCreate):
    """
    Adiciona uma nota a uma OS do tenant.
    """
    # Verifica OS e Tenant
    db_order = get_order(db, order_id, tenant_id)
    if not db_order:
        return None

    db_note = models.OrderNote(**note.model_dump(), order_id=order_id)
    db.add(db_note)
    db.commit()
    db.refresh(db_note)
    return db_note

def complete_order(db: Session, order_id: int, tenant_id: int):
    """
    Completa uma ordem de serviço:
    - Muda o status da OS para "Concluído".
    - Baixa as peças do estoque.
    - Registra os movimentos de estoque.
    - Gera uma transação de receita.
    Args:
        db (Session): Sessão do banco de dados.
        order_id (int): ID da ordem de serviço a ser completada.
        tenant_id (int): ID do tenant (empresa) para registrar movimentos e transações.
    Returns:
        models.ServiceOrder: A ordem de serviço completada, ou None se não encontrada ou já completada.
    """
    # Busca a ordem com LOCK para evitar modificações simultâas
    db_order = get_order(db, order_id, tenant_id, lock=True)
    if not db_order or db_order.status == models.OSStatus.COMPLETED:
        return None
    
    # Muda o status da ordem de serviço para CONCLUÍDO.
    db_order.status = models.OSStatus.COMPLETED
    
    # Baixa o estoque das peças utilizadas na ordem de serviço.
    for item in db_order.items:
        if item.type == models.ItemType.PART and item.part_id:
            # Registra o movimento de saída no estoque usando a função centralizada (com lock implícito no get_part interno se necessário, mas aqui travamos a OS)
            # Para máxima segurança, o get_part dentro do create_stock_movement também poderia dar lock.
            movement = schemas.StockMovementCreate(
                part_id=item.part_id,
                type=models.MovementType.OUT_OS,
                quantity=item.quantity,
                description=f"Saída OS #{order_id}",
                reference_id=str(order_id)
            )
            # Chamamos com commit=False para manter a atomicidade da conclusão da OS
            crud.create_stock_movement(db, movement, user_name="Sistema", tenant_id=tenant_id, commit=False)
    
    # Gera uma transação financeira de receita para a ordem de serviço.
    transaction = models.Transaction(
        tenant_id=tenant_id,
        type="INCOME",
        category="Serviços",
        description=f"Recebimento OS #{order_id}",
        amount=db_order.total_value,
        date=datetime.now(timezone.utc),
        status="PENDING",
        order_id=order_id
    )
    db.add(transaction)
    
    db.commit()
    db.refresh(db_order)
    return db_order

def reopen_order(db: Session, order_id: int, tenant_id: int):
    """
    Reabre uma ordem de serviço concluída.
    """
    db_order = get_order(db, order_id, tenant_id, lock=True)
    if not db_order or db_order.status != models.OSStatus.COMPLETED:
        return None
    
    # Muda status de volta para Em Execução
    db_order.status = models.OSStatus.IN_PROGRESS
    
    # Devolve estoque das peças utilizadas
    for item in db_order.items:
        if item.type == models.ItemType.PART and item.part_id:
            # Registra o movimento de retorno no estoque
            movement = schemas.StockMovementCreate(
                part_id=item.part_id,
                type=models.MovementType.RETURN_OS,
                quantity=item.quantity,
                description=f"Retorno OS #{order_id} (Reabertura)",
                reference_id=str(order_id)
            )
            create_stock_movement(db, movement, user_name="Sistema", tenant_id=tenant_id, commit=False)
                
    # Remove as transações financeiras vinculadas que ainda estão pendentes
    # Isso evita duplicidade quando a OS for concluída novamente
    db.query(models.Transaction).filter(
        models.Transaction.order_id == order_id,
        models.Transaction.status == "PENDING",
        models.Transaction.type == "INCOME"
    ).delete()

    db.commit()
    db.refresh(db_order)
    return db_order


# --- TRANSACTION CRUD ---
# Funções para operações CRUD na tabela de transações (models.Transaction).

def get_transactions(db: Session, tenant_id: int):
    """
    Retorna uma lista de todas as transações financeiras de um tenant, ordenadas por data.
    Args:
        db (Session): Sessão do banco de dados.
        tenant_id (int): ID do tenant.
    Returns:
        List[models.Transaction]: Lista de objetos transação.
    """
    return db.query(models.Transaction).filter(models.Transaction.tenant_id == tenant_id).order_by(desc(models.Transaction.date)).all()

def create_transaction(db: Session, transaction: schemas.TransactionCreate, tenant_id: int):
    """
    Cria uma nova transação financeira no banco de dados.
    Args:
        db (Session): Sessão do banco de dados.
        transaction (schemas.TransactionCreate): Dados da transação para criação.
        tenant_id (int): ID do tenant.
    Returns:
        models.Transaction: O objeto transação recém-criado.
    """
    db_transaction = models.Transaction(**transaction.model_dump(), tenant_id=tenant_id)
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction

# --- STOCK MOVEMENT CRUD ---
# Funções para operações CRUD na tabela de movimentos de estoque (models.StockMovement).

def get_movements(db: Session, tenant_id: int, part_id: Optional[int] = None):
    """
    Retorna uma lista de movimentos de estoque de um tenant, opcionalmente filtrada por ID da peça.
    Args:
        db (Session): Sessão do banco de dados.
        tenant_id (int): ID do tenant.
        part_id (Optional[int]): ID da peça para filtrar os movimentos.
    Returns:
        List[models.StockMovement]: Lista de objetos movimento de estoque.
    """
    query = db.query(models.StockMovement).filter(models.StockMovement.tenant_id == tenant_id).order_by(desc(models.StockMovement.date))
    if part_id:
        query = query.filter(models.StockMovement.part_id == part_id)
    return query.all()

def create_stock_movement(db: Session, movement: schemas.StockMovementCreate, user_name: str, tenant_id: int, commit: bool = True):
    """
    Registra um movimento de estoque e atualiza a quantidade da peça.
    """
    # 1. Cria o registro de movimento
    movement_data = movement.model_dump()
    if 'user' in movement_data:
        del movement_data['user']
    db_movement = models.StockMovement(**movement_data, user=user_name, tenant_id=tenant_id) # Campo user é string (nome)
    db.add(db_movement)
    
    # 2. Atualiza a quantidade da peça
    part = get_part(db, movement.part_id, tenant_id)
    if part:
        if movement.type in [models.MovementType.IN_INVOICE, models.MovementType.RETURN_OS, models.MovementType.ADJUSTMENT_PLUS]:
            part.quantity += movement.quantity
        elif movement.type in [models.MovementType.OUT_OS, models.MovementType.SALE_DIRECT, models.MovementType.ADJUSTMENT_MINUS]:
            part.quantity -= movement.quantity
        
        db.add(part)
    
    if commit:
        db.commit()
        db.refresh(db_movement)
    return db_movement

# --- CONFIG CRUD ---
# Funções para operações CRUD relacionadas a configurações (fabricantes, modelos, informações da empresa).

def get_manufacturers(db: Session, tenant_id: int, type: Optional[str] = None):
    """
    Retorna uma lista de fabricantes de um tenant, opcionalmente filtrada por tipo (BOAT ou ENGINE).
    Carrega os modelos relacionados para evitar N+1 queries.
    Args:
        db (Session): Sessão do banco de dados.
        tenant_id (int): ID do tenant.
        type (Optional[str]): Tipo do fabricante para filtrar.
    Returns:
        List[models.Manufacturer]: Lista de objetos fabricante.
    """
    query = db.query(models.Manufacturer).filter(models.Manufacturer.tenant_id == tenant_id).options(joinedload(models.Manufacturer.models))
    if type:
        query = query.filter(models.Manufacturer.type == type)
    return query.all()

def create_manufacturer(db: Session, manufacturer: schemas.ManufacturerCreate, tenant_id: int):
    """
    Cria um novo fabricante no banco de dados.
    Args:
        db (Session): Sessão do banco de dados.
        manufacturer (schemas.ManufacturerCreate): Dados do fabricante para criação.
        tenant_id (int): ID do tenant.
    Returns:
        models.Manufacturer: O objeto fabricante recém-criado.
    """
    db_manufacturer = models.Manufacturer(name=manufacturer.name, type=manufacturer.type, tenant_id=tenant_id)
    db.add(db_manufacturer)
    db.commit()
    db.refresh(db_manufacturer)
    return db_manufacturer

def delete_manufacturer(db: Session, manufacturer_id: int, tenant_id: int):
    """
    Deleta um fabricante pelo ID e tenant_id.
    """
    db_manufacturer = db.query(models.Manufacturer).filter(
        models.Manufacturer.id == manufacturer_id,
        models.Manufacturer.tenant_id == tenant_id
    ).first()
    if db_manufacturer:
        db.delete(db_manufacturer)
        db.commit()
    return db_manufacturer

def create_model(db: Session, manufacturer_id: int, tenant_id: int, model: schemas.ModelCreate):
    """
    Cria um novo modelo validando se o fabricante pertence ao tenant.
    """
    # Valida fabricante
    man = db.query(models.Manufacturer).filter(
        models.Manufacturer.id == manufacturer_id,
        models.Manufacturer.tenant_id == tenant_id
    ).first()
    if not man:
        return None

    db_model = models.Model(name=model.name, manufacturer_id=manufacturer_id)
    db.add(db_model)
    db.commit()
    db.refresh(db_model)
    return db_model

def delete_model(db: Session, model_id: int, tenant_id: int):
    """
    Deleta um modelo validando o tenant através do fabricante.
    """
    db_model = db.query(models.Model).join(models.Manufacturer).filter(
        models.Model.id == model_id,
        models.Manufacturer.tenant_id == tenant_id
    ).first()
    if db_model:
        db.delete(db_model)
        db.commit()
    return db_model

def get_company_info(db: Session, tenant_id: int):
    """
    Retorna as informações da empresa filtrando pelo tenant_id.
    Args:
        db (Session): Sessão do banco de dados.
        tenant_id (int): ID do tenant.
    Returns:
        models.CompanyInfo: O objeto com as informações da empresa, ou None.
    """
    db_info = db.query(models.CompanyInfo).filter(models.CompanyInfo.tenant_id == tenant_id).first()
    return db_info

def update_company_info(db: Session, info: schemas.CompanyInfoCreate, tenant_id: int):
    """
    Atualiza as informações da empresa para o tenant específico.
    Se não existirem informações, uma nova entrada é criada associada ao tenant.
    Args:
        db (Session): Sessão do banco de dados.
        info (schemas.CompanyInfoCreate): Dados para atualização.
        tenant_id (int): ID do tenant.
    Returns:
        models.CompanyInfo: O objeto atualizado.
    """
    db_info = get_company_info(db, tenant_id)
    if not db_info:
        # Se não houver informações da empresa, cria uma nova.
        db_info = models.CompanyInfo(tenant_id=tenant_id)
        db.add(db_info)

    # Atualiza os atributos do objeto do banco de dados com os dados do schema.
    update_data = info.model_dump(exclude_unset=True)
    
    # Se cert_base64 for fornecido, salvamos ele no campo cert_file_path
    # OBS: Requer que o campo cert_file_path no banco seja TEXT ou grande o suficiente
    if 'cert_base64' in update_data:
        cert_content = update_data.pop('cert_base64')
        if cert_content:
             # Em ambiente serverless/container efêmero, salvamos o conteúdo base64 no banco
             # em vez de salvar em arquivo físico. O Service Provider deverá saber ler isso.
             # Reutilizamos o campo 'cert_file_path' para guardar o conteúdo (prefixo b64:)
             setattr(db_info, 'cert_file_path', f"base64:{cert_content}")
    
    for key, value in update_data.items():
        if key != 'cert_base64': # Ja tratado acima
            setattr(db_info, key, value)
            
    db.commit()
    db.refresh(db_info)
    return db_info


def resolve_tenant_by_slug(db: Session, tenant_slug: str) -> Optional[models.Tenant]:
    normalized_slug = slugify(tenant_slug)
    
    # Busca todos os tenants ativos (ou com is_active NULL, tratando como ativo por padrão)
    tenants = db.query(models.Tenant)\
        .filter((models.Tenant.is_active == True) | (models.Tenant.is_active.is_(None)))\
        .all()

    for tenant in tenants:
        candidates = {
            slugify(tenant.subdomain or ""),
            slugify(tenant.name or ""),
        }
        
        # Também busca informações da empresa para ver se o nome fantasia bate
        company = db.query(models.CompanyInfo).filter(models.CompanyInfo.tenant_id == tenant.id).first()
        if company:
            candidates.add(slugify(company.trade_name or ""))
            candidates.add(slugify(company.company_name or ""))
            
        if normalized_slug in candidates:
            return tenant
    return None


def get_public_site_config(db: Session, tenant_slug: str) -> Optional[schemas.PublicSiteConfig]:
    normalized_slug = slugify(tenant_slug)
    tenant = resolve_tenant_by_slug(db, tenant_slug)
    if not tenant:
        return None

    company = db.query(models.CompanyInfo).filter(models.CompanyInfo.tenant_id == tenant.id).first()
    address_parts = []
    if company:
        address_parts = [
            company.street,
            company.number,
            company.neighborhood,
            company.city,
            company.state,
            company.zip_code,
        ]

    address = ", ".join([part for part in address_parts if part])
    return schemas.PublicSiteConfig(
        tenant_slug=normalized_slug,
        store_name=(company.trade_name if company and company.trade_name else None) or (company.company_name if company else None) or tenant.name,
        whatsapp=company.whatsapp if company else None,
        phone=company.phone if company else None,
        instagram=company.instagram if company else None,
        address=address or None,
        hero_title=company.hero_title if company and company.hero_title else f"{tenant.name} no comando da sua próxima navegação",
        hero_subtitle=company.hero_subtitle if company else None,
        hero_image_url=company.hero_image_url if company else None,
        home_content=company.home_content if company else None,
    )


def get_public_catalog(db: Session, tenant_slug: str, search: Optional[str] = None, page: int = 1, limit: int = 12) -> schemas.PublicCatalogResponse:
    tenant = resolve_tenant_by_slug(db, tenant_slug)
    if not tenant:
        return schemas.PublicCatalogResponse(items=[], total=0, page=page, limit=limit, total_pages=0)

    query = db.query(models.Part).filter(
        models.Part.tenant_id == tenant.id,
        models.Part.is_published == True
    )

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                models.Part.name.ilike(search_term),
                models.Part.public_title.ilike(search_term),
                models.Part.sku.ilike(search_term),
                models.Part.public_category.ilike(search_term),
                models.Part.group.ilike(search_term)
            )
        )

    total = query.count()
    total_pages = (total + limit - 1) // limit

    parts = query.order_by(desc(models.Part.is_featured), models.Part.name.asc()).offset((page - 1) * limit).limit(limit).all()

    items = []
    for part in parts:
        available = (part.quantity or 0) > 0
        stock_label = None
        if part.show_stock_publicly:
            stock_label = "Em estoque" if available else "Sob consulta"

        items.append(
            schemas.PublicCatalogItem(
                sku=part.sku,
                slug=part.public_slug or slugify(part.public_title or part.name or part.sku),
                title=part.public_title or part.name,
                description=part.public_description or part.name,
                image_url=part.public_image_url,
                price=part.public_price if part.public_price is not None else (part.price or 0),
                compare_at_price=part.public_compare_at_price,
                category=part.public_category or part.group,
                available=available,
                stock_label=stock_label,
                featured=bool(part.is_featured),
            )
        )
    return schemas.PublicCatalogResponse(items=items, total=total, page=page, limit=limit, total_pages=total_pages)


def get_public_catalog_item(db: Session, tenant_slug: str, slug: str) -> Optional[schemas.PublicCatalogItem]:
    tenant = resolve_tenant_by_slug(db, tenant_slug)
    if not tenant:
        return None

    part = db.query(models.Part).filter(
        models.Part.tenant_id == tenant.id,
        models.Part.is_published == True,
        models.Part.public_slug == slug
    ).first()

    if not part:
        # Fallback to verify if any other item matches slugified name
        parts = db.query(models.Part).filter(
            models.Part.tenant_id == tenant.id,
            models.Part.is_published == True
        ).all()
        for p in parts:
            gen_slug = p.public_slug or slugify(p.public_title or p.name or p.sku)
            if gen_slug == slug:
                part = p
                break

    if not part:
        return None

    available = (part.quantity or 0) > 0
    stock_label = None
    if part.show_stock_publicly:
        stock_label = "Em estoque" if available else "Sob consulta"

    return schemas.PublicCatalogItem(
        sku=part.sku,
        slug=slug,
        title=part.public_title or part.name,
        description=part.public_description or part.name,
        image_url=part.public_image_url,
        price=part.public_price if part.public_price is not None else (part.price or 0),
        compare_at_price=part.public_compare_at_price,
        category=part.public_category or part.group,
        available=available,
        stock_label=stock_label,
        featured=bool(part.is_featured),
    )


def create_public_lead(db: Session, tenant_slug: str, payload: schemas.PublicLeadCreate) -> Optional[models.PublicLead]:
    tenant = resolve_tenant_by_slug(db, tenant_slug)
    if not tenant:
        return None

    lead = models.PublicLead(
        tenant_id=tenant.id,
        name=payload.name,
        phone=payload.phone,
        email=payload.email,
        message=payload.message,
        source=payload.source or "site-publico",
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead


def create_public_cart_request(db: Session, tenant_slug: str, payload: schemas.PublicCartRequestCreate) -> Optional[models.PublicCartRequest]:
    tenant = resolve_tenant_by_slug(db, tenant_slug)
    if not tenant:
        return None

    request = models.PublicCartRequest(
        tenant_id=tenant.id,
        customer=payload.customer.model_dump(),
        boat=payload.boat.model_dump() if payload.boat else None,
        engine=payload.engine.model_dump() if payload.engine else None,
        items=[item.model_dump() for item in payload.items],
        notes=payload.notes,
        source=payload.source or "site-publico",
        channel_preference=payload.channel_preference or "whatsapp",
    )
    db.add(request)
    db.commit()
    db.refresh(request)
    return request


def get_public_leads(db: Session, tenant_id: int, limit: int = 100) -> List[models.PublicLead]:
    return (
        db.query(models.PublicLead)
        .filter(models.PublicLead.tenant_id == tenant_id)
        .order_by(desc(models.PublicLead.created_at))
        .limit(limit)
        .all()
    )


def get_public_cart_requests(db: Session, tenant_id: int, limit: int = 100) -> List[models.PublicCartRequest]:
    return (
        db.query(models.PublicCartRequest)
        .filter(models.PublicCartRequest.tenant_id == tenant_id)
        .order_by(desc(models.PublicCartRequest.created_at))
        .limit(limit)
        .all()
    )


def get_public_interactions_overview(db: Session, tenant_id: int) -> schemas.PublicInteractionsOverview:
    leads = get_public_leads(db, tenant_id=tenant_id, limit=500)
    cart_requests = get_public_cart_requests(db, tenant_id=tenant_id, limit=500)
    return schemas.PublicInteractionsOverview(
        total_leads=len(leads),
        total_cart_requests=len(cart_requests),
        new_leads=len([lead for lead in leads if lead.status == "NEW"]),
        new_cart_requests=len([request for request in cart_requests if request.status == "NEW"]),
        latest_lead_at=leads[0].created_at if leads else None,
        latest_cart_request_at=cart_requests[0].created_at if cart_requests else None,
    )

# --- MAINTENANCE KIT CRUD ---

def get_maintenance_kits(db: Session, tenant_id: int):
    """
    Retorna a lista de kits de manutenção do tenant.
    """
    return db.query(models.MaintenanceKit).filter(models.MaintenanceKit.tenant_id == tenant_id).options(
        joinedload(models.MaintenanceKit.items).joinedload(models.MaintenanceKitItem.part)
    ).all()

# --- SUBSCRIPTION CRUD ---

def get_tenant_subscription(db: Session, tenant_id: int):
    tenant = db.query(models.Tenant).filter(models.Tenant.id == tenant_id).first()
    if not tenant:
        return None
    
    # Mock data based on plan
    price_map = {
        "START": 197.00,
        "PRO": 497.00,
        "MARINA": 997.00,
        "ENTERPRISE": 0.0
    }
    
    plan_display_map = {
        "START": "Mecânico PRO",
        "PRO": "Oficina Team",
        "MARINA": "Marina Full",
        "ENTERPRISE": "Enterprise"
    }
    
    features_map = {
        "START": ["Agenda Básica", "Ordens de Serviço", "Cadastro de Clientes", "App do Mecânico"],
        "PRO": ["Inclui plano Start +", "Gestão de Estoque", "Finanças", "Múltiplos Usuários", "Relatórios"],
        "MARINA": ["Inclui plano Pro +", "Mapa da Marina", "CRM Avançado", "Gestão de Pátio", "Emissor Fiscal"],
        "ENTERPRISE": ["Tudo incluído", "Suporte Dedicado", "Customizações"]
    }

    current_plan_key = tenant.plan if tenant.plan in price_map else "START"
    
    return {
        "plan_name": plan_display_map.get(tenant.plan, tenant.plan),
        "price": price_map.get(tenant.plan, 0.0),
        "features": features_map.get(tenant.plan, []),
        "status": "Ativo" if tenant.is_active else "Inativo",
        "next_billing_date": (datetime.now() + timedelta(days=30)).strftime("%d/%m/%Y")
    }
    
def create_maintenance_kit(db: Session, kit: schemas.MaintenanceKitCreate, tenant_id: int):
    """
    Cria um novo kit de manutenção e seus itens.
    """
    kit_data = kit.model_dump()
    items_data = kit_data.pop("items", [])
    
    db_kit = models.MaintenanceKit(**kit_data, tenant_id=tenant_id)
    db.add(db_kit)
    db.commit()
    db.refresh(db_kit)
    
    for item_data in items_data:
        db_item = models.MaintenanceKitItem(**item_data, kit_id=db_kit.id)
        db.add(db_item)
        
    db.commit()
    db.refresh(db_kit)
    return db_kit

def delete_maintenance_kit(db: Session, kit_id: int, tenant_id: int):
    """
    Remove um kit de manutenção pertencente ao tenant.
    """
    db_kit = db.query(models.MaintenanceKit).filter(
        models.MaintenanceKit.id == kit_id,
        models.MaintenanceKit.tenant_id == tenant_id
    ).first()
    if db_kit:
        db.delete(db_kit)
        db.commit()
    return db_kit



# --- PARTNER CRUD ---
# Funções para operações CRUD na tabela de parceiros.

def get_partners(db: Session, tenant_id: int, active_only: bool = False):
    """
    Retorna todos os parceiros de um tenant.
    """
    query = db.query(models.Partner).filter(models.Partner.tenant_id == tenant_id)
    if active_only:
        query = query.filter(models.Partner.active == True)
    return query.order_by(models.Partner.name).all()

def get_partner(db: Session, partner_id: int, tenant_id: int):
    """
    Retorna um parceiro pelo ID e tenant_id.
    """
    return db.query(models.Partner).filter(
        models.Partner.id == partner_id,
        models.Partner.tenant_id == tenant_id
    ).first()

def create_partner(db: Session, partner: schemas.PartnerCreate, tenant_id: int):
    """
    Cria um novo parceiro.
    """
    db_partner = models.Partner(**partner.model_dump(), tenant_id=tenant_id)
    db.add(db_partner)
    db.commit()
    db.refresh(db_partner)
    return db_partner

def update_partner(db: Session, partner_id: int, tenant_id: int, partner_update: schemas.PartnerUpdate):
    """
    Atualiza um parceiro pertencente ao tenant.
    """
    db_partner = get_partner(db, partner_id, tenant_id)
    if not db_partner:
        return None
    
    update_data = partner_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_partner, key, value)
    
    db.commit()
    db.refresh(db_partner)
    return db_partner

def delete_partner(db: Session, partner_id: int, tenant_id: int):
    """
    Deleta um parceiro pertencente ao tenant.
    """
    db_partner = get_partner(db, partner_id, tenant_id)
    if not db_partner:
        return False
    
    db.delete(db_partner)
    db.commit()
    return True

def rate_partner(db: Session, partner_id: int, tenant_id: int, new_rating: float):
    """
    Atualiza a avaliação de um parceiro pertencente ao tenant.
    """
    db_partner = get_partner(db, partner_id, tenant_id)
    if not db_partner:
        return None
    
    # Calcula nova média
    total_ratings = db_partner.total_jobs
    if total_ratings == 0:
        db_partner.rating = new_rating
    else:
        current_total = db_partner.rating * total_ratings
        db_partner.rating = (current_total + new_rating) / (total_ratings + 1)
    
    db_partner.total_jobs += 1
    db.commit()
    db.refresh(db_partner)
    return db_partner


# --- TECHNICAL INSPECTION CRUD ---

def get_inspections(db: Session, tenant_id: int, boat_id: int = None):
    """
    Retorna inspeções de um tenant, opcionalmente filtradas por boat_id.
    """
    query = db.query(models.TechnicalInspection).filter(models.TechnicalInspection.tenant_id == tenant_id)
    if boat_id:
        query = query.filter(models.TechnicalInspection.boat_id == boat_id)
    return query.order_by(models.TechnicalInspection.created_at.desc()).all()

def get_inspection(db: Session, inspection_id: int, tenant_id: int):
    """
    Retorna uma inspeção pelo ID e tenant_id.
    """
    return db.query(models.TechnicalInspection).filter(
        models.TechnicalInspection.id == inspection_id,
        models.TechnicalInspection.tenant_id == tenant_id
    ).first()

def create_inspection(db: Session, inspection: schemas.TechnicalInspectionCreate, tenant_id: int):
    """
    Cria uma nova inspeção técnica.
    """
    db_inspection = models.TechnicalInspection(**inspection.model_dump(), tenant_id=tenant_id)
    db.add(db_inspection)
    db.commit()
    db.refresh(db_inspection)
    return db_inspection

def update_inspection(db: Session, inspection_id: int, tenant_id: int, inspection_update: schemas.TechnicalInspectionUpdate):
    """
    Atualiza uma inspeção pertencente ao tenant.
    """
    db_inspection = get_inspection(db, inspection_id, tenant_id)
    if not db_inspection:
        return None
    
    update_data = inspection_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_inspection, key, value)
    
    db.commit()
    db.refresh(db_inspection)
    return db_inspection

def add_checklist_item(db: Session, inspection_id: int, tenant_id: int, item: schemas.InspectionChecklistItemCreate):
    """
    Adiciona um item ao checklist de uma inspeção validando o tenant.
    """
    inspection = get_inspection(db, inspection_id, tenant_id)
    if not inspection:
        return None
        
    db_item = models.InspectionChecklistItem(**item.model_dump(), inspection_id=inspection_id)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


# --- PARTNER QUOTE CRUD ---

def get_partner_quotes(db: Session, tenant_id: int, inspection_id: int = None, partner_id: int = None):
    """
    Retorna orçamentos, opcionalmente filtrados por inspeção ou parceiro.
    """
    query = db.query(models.PartnerQuote).filter(models.PartnerQuote.tenant_id == tenant_id)
    if inspection_id:
        query = query.filter(models.PartnerQuote.inspection_id == inspection_id)
    if partner_id:
        query = query.filter(models.PartnerQuote.partner_id == partner_id)
    return query.order_by(models.PartnerQuote.created_at.desc()).all()

def get_partner_quote(db: Session, quote_id: int, tenant_id: int):
    """
    Retorna um orçamento pelo ID e tenant_id.
    """
    return db.query(models.PartnerQuote).filter(
        models.PartnerQuote.id == quote_id,
        models.PartnerQuote.tenant_id == tenant_id
    ).first()

def create_partner_quote(db: Session, quote: schemas.PartnerQuoteCreate, tenant_id: int):
    """
    Cria uma solicitação de orçamento para um parceiro.
    """
    db_quote = models.PartnerQuote(**quote.model_dump(), tenant_id=tenant_id)
    db.add(db_quote)
    db.commit()
    db.refresh(db_quote)
    return db_quote

def update_partner_quote(db: Session, quote_id: int, tenant_id: int, quote_update: schemas.PartnerQuoteUpdate):
    """
    Atualiza um orçamento pertencente ao tenant.
    """
    db_quote = get_partner_quote(db, quote_id, tenant_id)
    if not db_quote:
        return None
    
    update_data = quote_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_quote, key, value)
    
    # Se foi respondido, atualiza data
    if quote_update.quoted_value and not db_quote.response_date:
        db_quote.response_date = datetime.now(timezone.utc)
    
    db.commit()
    db.refresh(db_quote)
    return db_quote

# --- TECHNICAL DELIVERY CRUD ---

def get_technical_delivery(db: Session, order_id: int, tenant_id: int):
    """Busca entrega técnica por OS, garantindo tenant isolation."""
    return db.query(models.TechnicalDelivery).join(models.ServiceOrder).filter(
        models.TechnicalDelivery.service_order_id == order_id,
        models.ServiceOrder.tenant_id == tenant_id
    ).first()

def create_technical_delivery(db: Session, delivery: schemas.TechnicalDeliveryCreate, technician_id: int, tenant_id: int):
    db_delivery = models.TechnicalDelivery(
        **delivery.model_dump(),
        technician_id=technician_id,
        tenant_id=tenant_id
    )
    db.add(db_delivery)
    db.commit()
    db.refresh(db_delivery)
    return db_delivery

def update_technical_delivery(db: Session, delivery_id: int, tenant_id: int, delivery_update: schemas.TechnicalDeliveryUpdate):
    """Atualiza uma entrega técnica garantindo que pertença ao tenant do usuário."""
    db_delivery = db.query(models.TechnicalDelivery).filter(
        models.TechnicalDelivery.id == delivery_id,
        models.TechnicalDelivery.tenant_id == tenant_id
    ).first()
    if not db_delivery:
        return None
    
    update_data = delivery_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_delivery, key, value)
    
    db.commit()
    db.refresh(db_delivery)
    return db_delivery

# --- SERVICE CATALOG CRUD ---

def get_service_categories(db: Session, tenant_id: int):
    return db.query(models.ServiceCategory)\
        .options(joinedload(models.ServiceCategory.subcategories).joinedload(models.ServiceSubcategory.services))\
        .filter(models.ServiceCategory.tenant_id == tenant_id).all()

def create_service_category(db: Session, category: schemas.ServiceCategoryCreate, tenant_id: int):
    db_category = models.ServiceCategory(**category.model_dump(), tenant_id=tenant_id)
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

def get_service_subcategories(db: Session, tenant_id: int, category_id: Optional[int] = None):
    query = db.query(models.ServiceSubcategory)\
        .options(joinedload(models.ServiceSubcategory.services))\
        .filter(models.ServiceSubcategory.tenant_id == tenant_id)
    if category_id:
        query = query.filter(models.ServiceSubcategory.category_id == category_id)
    return query.all()

def create_service_subcategory(db: Session, subcategory: schemas.ServiceSubcategoryCreate, tenant_id: int):
    db_subcategory = models.ServiceSubcategory(**subcategory.model_dump(), tenant_id=tenant_id)
    db.add(db_subcategory)
    db.commit()
    db.refresh(db_subcategory)
    return db_subcategory

def get_service_catalog(db: Session, tenant_id: int, subcategory_id: Optional[int] = None):
    query = db.query(models.ServiceCatalog).filter(models.ServiceCatalog.tenant_id == tenant_id)
    if subcategory_id:
        query = query.filter(models.ServiceCatalog.subcategory_id == subcategory_id)
    return query.all()

def create_service_catalog_item(db: Session, item: schemas.ServiceCatalogCreate, tenant_id: int):
    db_item = models.ServiceCatalog(**item.model_dump(), tenant_id=tenant_id)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def update_service_catalog_item(db: Session, item_id: int, tenant_id: int, item_update: schemas.ServiceCatalogUpdate):
    db_item = db.query(models.ServiceCatalog).filter(
        models.ServiceCatalog.id == item_id,
        models.ServiceCatalog.tenant_id == tenant_id
    ).first()
    if not db_item:
        return None
    update_data = item_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_item, key, value)
    db.commit()
    db.refresh(db_item)
    return db_item

def delete_service_catalog_item(db: Session, item_id: int, tenant_id: int):
    db_item = db.query(models.ServiceCatalog).filter(
        models.ServiceCatalog.id == item_id,
        models.ServiceCatalog.tenant_id == tenant_id
    ).first()
    if db_item:
        db.delete(db_item)
        db.commit()
    return db_item
