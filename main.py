from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import database, schemas
from fastapi import UploadFile, File
import pdfplumber
import io
import re

database.Base.metadata.create_all(bind=database.engine)
app = FastAPI(title="API CREAdesign")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

def get_db():
    db = database.SessionLocal()
    try: yield db
    finally: db.close()

# --- BODEGA ---
@app.post("/materiales/", response_model=schemas.MaterialResponse)
def crear_material(material: schemas.MaterialCreate, db: Session = Depends(get_db)):
    nuevo_material = database.Material(**material.model_dump())
    db.add(nuevo_material)
    db.commit()
    db.refresh(nuevo_material)
    return nuevo_material

@app.get("/materiales/", response_model=List[schemas.MaterialResponse])
def obtener_materiales(db: Session = Depends(get_db)): return db.query(database.Material).all()

@app.put("/materiales/{material_id}", response_model=schemas.MaterialResponse)
def actualizar_material(material_id: int, material: schemas.MaterialCreate, db: Session = Depends(get_db)):
    db_material = db.query(database.Material).filter(database.Material.id == material_id).first()
    if db_material:
        for key, value in material.model_dump().items(): setattr(db_material, key, value)
        db.commit()
        db.refresh(db_material)
    return db_material

@app.delete("/materiales/{material_id}")
def eliminar_material(material_id: int, db: Session = Depends(get_db)):
    db_material = db.query(database.Material).filter(database.Material.id == material_id).first()
    if db_material: db.delete(db_material); db.commit()
    return {"mensaje": "Material eliminado"}

# --- CLIENTES ---
@app.post("/clientes/", response_model=schemas.ClienteResponse)
def crear_cliente(cliente: schemas.ClienteCreate, db: Session = Depends(get_db)):
    nuevo_cliente = database.Cliente(**cliente.model_dump())
    db.add(nuevo_cliente)
    db.commit()
    db.refresh(nuevo_cliente)
    return nuevo_cliente

@app.get("/clientes/", response_model=List[schemas.ClienteResponse])
def obtener_clientes(db: Session = Depends(get_db)): return db.query(database.Cliente).all()

@app.put("/clientes/{cliente_id}", response_model=schemas.ClienteResponse)
def actualizar_cliente(cliente_id: int, cliente: schemas.ClienteCreate, db: Session = Depends(get_db)):
    db_cliente = db.query(database.Cliente).filter(database.Cliente.id == cliente_id).first()
    if db_cliente:
        for key, value in cliente.model_dump().items(): setattr(db_cliente, key, value)
        db.commit()
        db.refresh(db_cliente)
    return db_cliente

@app.delete("/clientes/{cliente_id}")
def eliminar_cliente(cliente_id: int, db: Session = Depends(get_db)):
    db_cliente = db.query(database.Cliente).filter(database.Cliente.id == cliente_id).first()
    if db_cliente: db.delete(db_cliente); db.commit()
    return {"mensaje": "Cliente eliminado"}

# --- COTIZACIONES ---
@app.post("/cotizaciones/", response_model=schemas.CotizacionResponse)
def crear_cotizacion(cotizacion: schemas.CotizacionCreate, db: Session = Depends(get_db)):
    nueva_cotizacion = database.Cotizacion(cliente_id=cotizacion.cliente_id, fecha_vencimiento=cotizacion.fecha_vencimiento, subtotal=cotizacion.subtotal, iva=cotizacion.iva, total=cotizacion.total, estado=cotizacion.estado)
    db.add(nueva_cotizacion)
    db.commit()
    db.refresh(nueva_cotizacion)
    for d in cotizacion.detalles:
        nuevo_d = database.CotizacionDetalle(cotizacion_id=nueva_cotizacion.id, cantidad=d.cantidad, detalle_del_trabajo=d.detalle_del_trabajo, precio_unitario=d.precio_unitario, total_item=d.total_item)
        db.add(nuevo_d)
    db.commit()
    db.refresh(nueva_cotizacion)
    return nueva_cotizacion

@app.get("/cotizaciones/", response_model=List[schemas.CotizacionResponse])
def obtener_cotizaciones(db: Session = Depends(get_db)): return db.query(database.Cotizacion).all()

# --- ORDENES ---
@app.post("/ordenes/", response_model=schemas.OrdenTrabajoResponse)
def crear_orden_trabajo(orden: schemas.OrdenTrabajoCreate, db: Session = Depends(get_db)):
    nueva_orden = database.OrdenTrabajo(**orden.model_dump())
    db.add(nueva_orden)
    db.commit()
    db.refresh(nueva_orden)
    return nueva_orden

@app.get("/ordenes/", response_model=List[schemas.OrdenTrabajoResponse])
def obtener_ordenes_trabajo(db: Session = Depends(get_db)): return db.query(database.OrdenTrabajo).all()

@app.put("/ordenes/{orden_id}", response_model=schemas.OrdenTrabajoResponse)
def actualizar_estado_orden(orden_id: int, orden: schemas.OrdenTrabajoCreate, db: Session = Depends(get_db)):
    db_orden = db.query(database.OrdenTrabajo).filter(database.OrdenTrabajo.id == orden_id).first()
    if db_orden:
        for key, value in orden.model_dump().items(): setattr(db_orden, key, value)
        db.commit()
        db.refresh(db_orden)
    return db_orden

@app.delete("/ordenes/{orden_id}")
def eliminar_orden_trabajo(orden_id: int, db: Session = Depends(get_db)):
    db_orden = db.query(database.OrdenTrabajo).filter(database.OrdenTrabajo.id == orden_id).first()
    if db_orden: db.delete(db_orden); db.commit()
    return {"mensaje": "Orden eliminada"}

# --- FINANZAS ---
@app.post("/movimientos/", response_model=schemas.MovimientoResponse)
def crear_movimiento(movimiento: schemas.MovimientoCreate, db: Session = Depends(get_db)):
    nuevo_movimiento = database.Movimiento(**movimiento.model_dump())
    db.add(nuevo_movimiento)
    db.commit()
    db.refresh(nuevo_movimiento)
    return nuevo_movimiento

@app.get("/movimientos/", response_model=List[schemas.MovimientoResponse])
def obtener_movimientos(db: Session = Depends(get_db)): return db.query(database.Movimiento).order_by(database.Movimiento.fecha.desc()).all()

@app.delete("/movimientos/{mov_id}")
def eliminar_movimiento(mov_id: int, db: Session = Depends(get_db)):
    db_mov = db.query(database.Movimiento).filter(database.Movimiento.id == mov_id).first()
    if db_mov: db.delete(db_mov); db.commit()
    return {"mensaje": "Movimiento eliminado"}

@app.put("/movimientos/{movimiento_id}")
def update_movimiento(movimiento_id: int, mov: schemas.MovimientoBase, db: Session = Depends(get_db)):
    # Buscamos en "database" en lugar de "models"
    db_mov = db.query(database.Movimiento).filter(database.Movimiento.id == movimiento_id).first()
    
    if not db_mov:
        raise HTTPException(status_code=404, detail="Movimiento no encontrado")
        
    db_mov.tipo = mov.tipo
    db_mov.categoria = mov.categoria
    db_mov.monto = mov.monto
    db_mov.concepto = mov.concepto
    db_mov.fecha = mov.fecha
    db_mov.estado_pago = mov.estado_pago
    db_mov.medio_pago = mov.medio_pago
    
    db.commit()
    db.refresh(db_mov)
    return db_mov

@app.post("/login")
def login(req: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = db.query(database.Usuario).filter(database.Usuario.username == req.username).first()
    if not user or user.password != req.password:
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    return {"username": user.username, "rol": user.rol}

@app.delete("/cotizaciones/{cotizacion_id}")
def delete_cotizacion(cotizacion_id: int, db: Session = Depends(get_db)):
    # Buscamos la cotización en la base de datos
    db_cot = db.query(database.Cotizacion).filter(database.Cotizacion.id == cotizacion_id).first()
    
    if not db_cot:
        raise HTTPException(status_code=404, detail="Cotización no encontrada")
        
    db.delete(db_cot)
    db.commit()
    return {"mensaje": "Cotización eliminada correctamente"}

@app.post("/upload-cartola/")
async def leer_cartola(file: UploadFile = File(...)):
    try:
        content = await file.read()
        pdf_file = io.BytesIO(content)
        sugerencias = []
        
        with pdfplumber.open(pdf_file) as pdf:
            # 1. Leer TODO el texto oculto para descubrir el banco sin fallar
            texto_completo = ""
            for page in pdf.pages:
                t = page.extract_text()
                if t: texto_completo += t.upper() + " "
            
            banco_detectado = "BancoEstado" # Por defecto
            if "SANTANDER" in texto_completo or "WWW.SANTANDER.CL" in texto_completo or "BANSANDER" in texto_completo:
                banco_detectado = "Santander"
            elif "BANCOESTADO" in texto_completo or "BANCO ESTADO" in texto_completo:
                banco_detectado = "BancoEstado"

            for page in pdf.pages:
                texto = page.extract_text()
                if not texto: continue
                
                lineas = texto.split('\n')
                for linea in lineas:
                    linea_upper = linea.upper()
                    categoria = "Otros Gastos"
                    tipo = "Gasto"
                    monto = 0
                    es_cobro_banco = False
                    
                    if "FECHA" in linea_upper or "CARGO" in linea_upper or "ABONO" in linea_upper or "SALDO" in linea_upper:
                        continue
                        
                    montos = re.findall(r'\$\s*-?\s*([\d\.]+)', linea_upper)
                    
                    # --- LÓGICA BANCOESTADO --- 
                    if len(montos) >= 3 and ("TEF" in linea_upper or "COMPRA" in linea_upper or "GIRO" in linea_upper or "COMISION" in linea_upper or "IMPUESTO" in linea_upper):
                        cargo = int(montos[-3].replace('.', ''))
                        abono = int(montos[-2].replace('.', ''))
                        if cargo > 0:
                            tipo = "Gasto"
                            monto = cargo
                        elif abono > 0:
                            tipo = "Ingreso"
                            categoria = "Otros Ingresos"
                            monto = abono
                            
                    # --- LÓGICA SANTANDER --- 
                    elif len(montos) > 0:
                        if "$-" in linea_upper:
                            tipo = "Gasto"
                            monto = int(montos[0].replace('.', ''))
                        elif "TRANSF DE" in linea_upper or "ABONO" in linea_upper:
                            tipo = "Ingreso"
                            categoria = "Otros Ingresos"
                            monto = int(montos[0].replace('.', ''))
                        elif "COMPRA" in linea_upper or "TRANSF A" in linea_upper or "INTERES" in linea_upper or "COMISION" in linea_upper or "IMPUESTO" in linea_upper or "MANTENCION" in linea_upper or "SOBREGIRO" in linea_upper:
                            tipo = "Gasto"
                            monto = int(montos[0].replace('.', ''))

                    if monto == 0:
                        continue 

                    # --- DETECCIÓN DE COBROS BANCARIOS INAMOVIBLES ---
                    if "COMISION" in linea_upper or "INTERES" in linea_upper or "MANTENCION" in linea_upper or "IMPUESTO" in linea_upper or "SOBREGIRO" in linea_upper:
                        categoria = "Otros Gastos"
                        es_cobro_banco = True
                        linea = f"[Cobro Banco] {linea}" 

                    # --- TU CEREBRO BANCARIO ---
                    if not es_cobro_banco:
                        if "COPEC" in linea_upper or "SHELL" in linea_upper or "PETROBRAS" in linea_upper or "ARAMCO" in linea_upper:
                            categoria = "Combustible y Peajes"
                        elif "PREVIRED" in linea_upper or "IMPOSICIONES" in linea_upper:
                            categoria = "Sueldos e Imposiciones"
                        elif "STARKEN" in linea_upper or "CHILEXPRESS" in linea_upper or "REPARTIDOR" in linea_upper:
                            categoria = "Transporte y Encomiendas"
                        elif "SODIMAC" in linea_upper or "EASY" in linea_upper or "IMPERIAL" in linea_upper or "FERREHOGAR" in linea_upper:
                            categoria = "Materiales y Sustratos"
                        elif "RESTAURANT" in linea_upper or "JUMBO" in linea_upper or "STA ISABEL" in linea_upper or "CARNES" in linea_upper or "FINA ESTAMPA" in linea_upper or "TOTTUS" in linea_upper:
                            categoria = "Colaciones en Terreno"
                        elif "ARRIENDO" in linea_upper and "MAQUINARIA" in linea_upper:
                            categoria = "Arriendo de Maquinarias"

                    concepto = linea
                    concepto = re.sub(r'^\d{2}/\d{2}/\d{4}', '', concepto) 
                    concepto = re.sub(r'^\d{2}/\d{2}', '', concepto) 
                    concepto = re.sub(r'STGO\.PRINCIPAL', '', concepto, flags=re.IGNORECASE) 
                    concepto = re.sub(r'\$\s*-?\s*[\d\.]+', '', concepto) 
                    concepto = re.sub(r'\b\d{6,}\b', '', concepto) 
                    
                    sugerencias.append({
                        "concepto": concepto[:60].strip(),
                        "monto": monto,
                        "categoria": categoria,
                        "tipo": tipo,
                        "banco_detectado": banco_detectado,
                        "locked": es_cobro_banco
                    })
                            
        return {"sugerencias": sugerencias}
    except Exception as e:
        return {"error": str(e)}