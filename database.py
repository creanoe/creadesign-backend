from sqlalchemy import create_engine, Column, Integer, String, Float, Date, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import date

# 🚨 REEMPLAZA ESTE TEXTO CON EL LINK EXACTO DE SUPABASE 🚨
# Recuerda cambiar donde dice [YOUR-PASSWORD] por la contraseña que creaste en el paso 1
DATABASE_URL = "postgresql://postgres:[YOUR-PASSWORD]@db.gnmwboatdirrnwzcrihu.supabase.co:5432/postgres"

# El motor nuevo, listo para la nube (sin la configuración antigua de SQLite)
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ... de aquí para abajo, tus clases Cliente, Material, etc. siguen igual ...
class Material(Base):
    __tablename__ = "materiales"
    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String, unique=True, index=True)
    nombre = Column(String)
    categoria = Column(String)
    unidad_medida = Column(String)
    stock_actual = Column(Float, default=0.0)
    costo_unitario = Column(Integer)

class Cliente(Base):
    __tablename__ = "clientes"
    id = Column(Integer, primary_key=True, index=True)
    razon_social = Column(String)
    rut = Column(String, index=True)
    alias = Column(String, nullable=True)
    email = Column(String, nullable=True)
    telefono = Column(String, nullable=True)
    direccion = Column(String, nullable=True)

class Cotizacion(Base):
    __tablename__ = "cotizaciones"
    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"))
    fecha_creacion = Column(Date, default=date.today)
    fecha_vencimiento = Column(Date)
    subtotal = Column(Integer)
    iva = Column(Integer)
    total = Column(Integer)
    estado = Column(String, default="Borrador")
    cliente = relationship("Cliente")
    detalles = relationship("CotizacionDetalle", back_populates="cotizacion")

class CotizacionDetalle(Base):
    __tablename__ = "cotizaciones_detalles"
    id = Column(Integer, primary_key=True, index=True)
    cotizacion_id = Column(Integer, ForeignKey("cotizaciones.id"))
    cantidad = Column(Float)
    detalle_del_trabajo = Column(String)
    precio_unitario = Column(Integer)
    total_item = Column(Integer)
    cotizacion = relationship("Cotizacion", back_populates="detalles")

class OrdenTrabajo(Base):
    __tablename__ = "ordenes_trabajo"
    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"))
    cotizacion_id = Column(Integer, ForeignKey("cotizaciones.id"), nullable=True)
    descripcion = Column(Text)
    fecha_entrega = Column(Date)
    estado = Column(String, default="Pendiente")
    link_diseno = Column(String, nullable=True) # <--- NUEVA COLUMNA PARA EL LINK
    fecha_creacion = Column(Date, default=date.today)
    cliente = relationship("Cliente")
    cotizacion = relationship("Cotizacion")

class Movimiento(Base):
    __tablename__ = "movimientos"
    id = Column(Integer, primary_key=True, index=True)
    tipo = Column(String) 
    categoria = Column(String)
    monto = Column(Integer)
    concepto = Column(String)
    fecha = Column(Date, default=date.today)
    estado_pago = Column(String, default="Pagado")
    medio_pago = Column(String, default="Transferencia") # <--- NUEVA COLUMNA

class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True)
    password = Column(String) # Para este nivel usaremos texto plano, luego le ponemos hash
    rol = Column(String) # 'Admin' o 'Taller'
        
