from pydantic import BaseModel
from typing import List, Optional
from datetime import date

# --- NUEVOS SCHEMAS DE USUARIO ---
class UsuarioBase(BaseModel):
    username: str
    password: str
    rol: str

class LoginRequest(BaseModel):
    username: str
    password: str

# --- SCHEMAS EXISTENTES ---
class MaterialBase(BaseModel):
    codigo: str
    nombre: str
    categoria: str
    unidad_medida: str
    stock_actual: float = 0.0
    costo_unitario: int

class MaterialCreate(MaterialBase): pass
class MaterialResponse(MaterialBase):
    id: int
    class Config: from_attributes = True

class ClienteBase(BaseModel):
    razon_social: str
    rut: str
    alias: Optional[str] = None
    email: Optional[str] = None
    telefono: Optional[str] = None
    direccion: Optional[str] = None

class ClienteCreate(ClienteBase): pass
class ClienteResponse(ClienteBase):
    id: int
    class Config: from_attributes = True

class CotizacionDetalleBase(BaseModel):
    cantidad: float
    detalle_del_trabajo: str
    precio_unitario: int
    total_item: int

class CotizacionDetalleCreate(CotizacionDetalleBase): pass
class CotizacionDetalleResponse(CotizacionDetalleBase):
    id: int
    cotizacion_id: int
    class Config: from_attributes = True

class CotizacionBase(BaseModel):
    cliente_id: int
    fecha_vencimiento: date
    subtotal: int
    iva: int
    total: int
    estado: str = "Borrador"

class CotizacionCreate(CotizacionBase):
    detalles: List[CotizacionDetalleCreate]
class CotizacionResponse(CotizacionBase):
    id: int
    fecha_creacion: date
    cliente: ClienteResponse
    detalles: List[CotizacionDetalleResponse]
    class Config: from_attributes = True

class OrdenTrabajoBase(BaseModel):
    cliente_id: int
    cotizacion_id: Optional[int] = None
    descripcion: str
    fecha_entrega: date
    estado: str = "Pendiente"
    link_diseno: Optional[str] = None # <--- NUEVA COLUMNA EN EL ESQUEMA

class OrdenTrabajoCreate(OrdenTrabajoBase): pass
class OrdenTrabajoResponse(OrdenTrabajoBase):
    id: int
    fecha_creacion: date
    cliente: ClienteResponse
    class Config: from_attributes = True

class MovimientoBase(BaseModel):
    tipo: str
    categoria: str
    monto: int
    concepto: str
    fecha: date
    estado_pago: str = "Pagado"
    medio_pago: str = "Transferencia" 
    # 🔥 AQUI VAN LOS GUARDIAS NUEVOS PARA FACTURAS, OT Y F29 🔥
    tipo_doc: str = "Boleta"
    num_factura: Optional[str] = None
    ot_id: Optional[str] = None
    locked: bool = False

class MovimientoCreate(MovimientoBase): pass
class MovimientoResponse(MovimientoBase):
    id: int
    class Config: from_attributes = True
