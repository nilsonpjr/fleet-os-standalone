"""
backend/models.py — Model Hub
=============================
This file consolidates all models from modular packages to support legacy 
imports like 'from backend import models' in crud.py.
"""

from modules.auth.models import User, Tenant, UserRole
from modules.clients.models import Client, Marina
from modules.boats.models import Boat, Engine
from modules.inventory.models import (
    Part, StockMovement, Invoice, MaintenanceKit, MaintenanceKitItem,
    MovementType, ItemType
)
from modules.orders.models import (
    ServiceOrder, ServiceItem, OrderNote, TechnicalDelivery,
    OSStatus, DeliveryType
)
from modules.fiscal.models import FiscalInvoice
from modules.partners.models import Partner, PartnerQuote
from modules.config.models import (
    CompanyInfo, ServiceDefinition, ServiceCategory, ServiceSubcategory,
    ServiceCatalog, Manufacturer, Model, ComplexityType
)
from modules.notifications.models import Notification
from modules.fleet.models import (
    FleetRequest, FleetRequestMessage, TechnicalInspection, 
    InspectionChecklistItem, MaintenanceSchedule, InspectionStatus,
    ChecklistItemSeverity, QuoteStatus
)
from modules.lgpd.models import AuditLog, ConsentRecord, ErasureRequest
