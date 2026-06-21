import os
import json
import io
import re
import pdfplumber
import google.generativeai as genai
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from typing import List
from PIL import Image
import database, schemas
# 🔥 0. CONFIGURAR LA INTELIGENCIA ARTIFICIAL (GEMINI)
gemini_key = os.environ.get("GEMINI_API_KEY")
if gemini_key:
    # Quitar espacios en blanco por si se copiaron por error
gemini_key = gemini_key.strip()
genai.configure(api_key=gemini_key)
    
    # BUSCADOR AUTOMÁTICO DEL MODELO CORRECTO PARA TU CUENTA
modelo_exacto = 'gemini-1.5-flash' # Plan Z de emergencia
try:
for m in genai.list_models():
if 'generateContent' in m.supported_generation_methods and 'flash' in m.name:
modelo_exacto = m.name
break
modelo_vision = genai.GenerativeModel(modelo_exacto)
print(f"✅ IA CONECTADA USANDO EL MODELO EXACTO: {modelo_exacto}")
except Exception as e:
print(f"⚠️ Error al conectar con Google: {e}")
modelo_vision = None
else:
    modelo_vision = None
    print("⚠️ ADVERTENCIA: No se encontró la GEMINI_API_KEY en el servidor.")
# 1. CREAR BASE DE DATOS (Ahora en Supabase)
database.Base.metadata.create_all(bind=database.engine)

# 2. INICIAR LA APP
app = FastAPI(title="API CREAdesign")

# 3. ESCUDO CORS PARA VERCEL
app.add_middleware(
    CORSMiddleware, 
    allow_origins=["*"], 
    allow_credentials=True, 
    allow_methods=["*"], 
    allow_headers=["*"]
)

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
def obtener_materiales(db: Session = Depends(get_db)): 
    return db.query(database.Material).all()

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
def obtener_clientes(db: Session = Depends(get_db)): 
    return db.query(database.Cliente).all()

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
def obtener_cotizaciones(db: Session = Depends(get_db)): 
    return db.query(database.Cotizacion).all()

@app.delete("/cotizaciones/{cotizacion_id}")
def delete_cotizacion(cotizacion_id: int, db: Session = Depends(get_db)):
    db_cot = db.query(database.Cotizacion).filter(database.Cotizacion.id == cotizacion_id).first()
    if not db_cot:
        raise HTTPException(status_code=404, detail="Cotización no encontrada")
    db.delete(db_cot)
    db.commit()
    return {"mensaje": "Cotización eliminada correctamente"}

# --- ORDENES ---
@app.post("/ordenes/", response_model=schemas.OrdenTrabajoResponse)
def crear_orden_trabajo(orden: schemas.OrdenTrabajoCreate, db: Session = Depends(get_db)):
    nueva_orden = database.OrdenTrabajo(**orden.model_dump())
    db.add(nueva_orden)
    db.commit()
    db.refresh(nueva_orden)
    return nueva_orden

@app.get("/ordenes/", response_model=List[schemas.OrdenTrabajoResponse])
def obtener_ordenes_trabajo(db: Session = Depends(get_db)): 
    return db.query(database.OrdenTrabajo).all()

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
def obtener_movimientos(db: Session = Depends(get_db)): 
    return db.query(database.Movimiento).order_by(database.Movimiento.fecha.desc()).all()

@app.delete("/movimientos/{mov_id}")
def eliminar_movimiento(mov_id: int, db: Session = Depends(get_db)):
    db_mov = db.query(database.Movimiento).filter(database.Movimiento.id == mov_id).first()
    if db_mov: db.delete(db_mov); db.commit()
    return {"mensaje": "Movimiento eliminado"}

@app.put("/movimientos/{movimiento_id}")
def update_movimiento(movimiento_id: int, mov: schemas.MovimientoBase, db: Session = Depends(get_db)):
    db_mov = db.query(database.Movimiento).filter(database.Movimiento.id == movimiento_id).first()
    if not db_mov: raise HTTPException(status_code=404, detail="Movimiento no encontrado")
    
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

# --- LECTORES INTELIGENTES ---
@app.post("/upload-cartola/")
async def leer_cartola(file: UploadFile = File(...)):
    try:
        content = await file.read()
        pdf_file = io.BytesIO(content)
        sugerencias = []
        
        with pdfplumber.open(pdf_file) as pdf:
            texto_completo = ""
            for page in pdf.pages:
                t = page.extract_text()
                if t: texto_completo += t.upper() + " "
            
            banco_detectado = "BancoEstado"
            if "SANTANDER" in texto_completo or "WWW.SANTANDER.CL" in texto_completo or "BANSANDER" in texto_completo:
                banco_detectado = "Santander"

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
                    
                    if any(x in linea_upper for x in ["FECHA", "CARGO", "ABONO", "SALDO"]): continue
                        
                    montos = re.findall(r'\$\s*-?\s*([\d\.]+)', linea_upper)
                    
                    if len(montos) >= 3 and any(x in linea_upper for x in ["TEF", "COMPRA", "GIRO", "COMISION", "IMPUESTO"]):
                        cargo = int(montos[-3].replace('.', ''))
                        abono = int(montos[-2].replace('.', ''))
                        if cargo > 0:
                            tipo, monto = "Gasto", cargo
                        elif abono > 0:
                            tipo, categoria, monto = "Ingreso", "Otros Ingresos", abono
                            
                    elif len(montos) > 0:
                        if "$-" in linea_upper:
                            tipo, monto = "Gasto", int(montos[0].replace('.', ''))
                        elif any(x in linea_upper for x in ["TRANSF DE", "ABONO"]):
                            tipo, categoria, monto = "Ingreso", "Otros Ingresos", int(montos[0].replace('.', ''))
                        elif any(x in linea_upper for x in ["COMPRA", "TRANSF A", "INTERES", "COMISION", "IMPUESTO", "MANTENCION", "SOBREGIRO"]):
                            tipo, monto = "Gasto", int(montos[0].replace('.', ''))

                    if monto == 0: continue 

                    if any(x in linea_upper for x in ["COMISION", "INTERES", "MANTENCION", "IMPUESTO", "SOBREGIRO"]):
                        categoria, es_cobro_banco, linea = "Otros Gastos", True, f"[Cobro Banco] {linea}" 

                    if not es_cobro_banco:
                        if any(x in linea_upper for x in ["COPEC", "SHELL", "PETROBRAS", "ARAMCO"]): categoria = "Combustible y Peajes"
                        elif any(x in linea_upper for x in ["PREVIRED", "IMPOSICIONES"]): categoria = "Sueldos e Imposiciones"
                        elif any(x in linea_upper for x in ["STARKEN", "CHILEXPRESS", "REPARTIDOR"]): categoria = "Transporte y Encomiendas"
                        elif any(x in linea_upper for x in ["SODIMAC", "EASY", "IMPERIAL", "FERREHOGAR"]): categoria = "Materiales y Sustratos"
                        elif any(x in linea_upper for x in ["RESTAURANT", "JUMBO", "STA ISABEL", "CARNES", "FINA ESTAMPA", "TOTTUS"]): categoria = "Colaciones en Terreno"
                        elif "ARRIENDO" in linea_upper and "MAQUINARIA" in linea_upper: categoria = "Arriendo de Maquinarias"

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
    
@app.post("/upload-factura/")
async def leer_factura(file: UploadFile = File(...)):
    try:
        content = await file.read()
        filename = file.filename.lower()
        proveedor = {"rut": "", "razon_social": ""}
        items_detectados = []
        total_factura = 0

        if filename.endswith('.xml'):
            texto_xml = content.decode('utf-8', errors='ignore')
            rut_match = re.search(r'<RUTEmisor>([^<]+)</RUTEmisor>', texto_xml)
            if rut_match: proveedor["rut"] = rut_match.group(1)
            
            rz_match = re.search(r'<RznSoc>([^<]+)</RznSoc>', texto_xml)
            if rz_match: proveedor["razon_social"] = rz_match.group(1)[:60].strip()
            
            tot_match = re.search(r'<MntTotal>([^<]+)</MntTotal>', texto_xml)
            if tot_match: 
                try: total_factura = int(tot_match.group(1))
                except: pass
            
            detalles = re.findall(r'<Detalle>(.*?)</Detalle>', texto_xml, re.DOTALL)
            for det in detalles:
                nombre = "Item sin nombre"
                n_match = re.search(r'<NmbItem>([^<]+)</NmbItem>', det)
                if n_match: nombre = n_match.group(1)[:80].strip()
                
                cantidad = 1
                q_match = re.search(r'<QtyItem>([^<]+)</QtyItem>', det)
                if q_match:
                    try: cantidad = int(float(q_match.group(1)))
                    except: pass
                    
                um = "UN"
                u_match = re.search(r'<UnmdItem>([^<]+)</UnmdItem>', det)
                if u_match: um = u_match.group(1)[:4].upper()
                
                codigo = ""
                c_match = re.search(r'<VlrCodigo>([^<]+)</VlrCodigo>', det)
                if c_match: codigo = c_match.group(1)[:15]
                else:
                    palabras = [p for p in nombre.split() if len(p) > 2 and not any(c.isdigit() for c in p)]
                    if len(palabras) >= 2: codigo = f"{palabras[0][:3]}-{palabras[1][:3]}".upper()
                    else: codigo = f"MAT-{cantidad}"
                    
                items_detectados.append({
                    "codigo": codigo, "nombre": nombre, "categoria": "Insumos Varios",
                    "unidad_medida": um, "cantidad_ingresar": cantidad
                })

        elif filename.endswith('.pdf'):
            pdf_file = io.BytesIO(content)
            with pdfplumber.open(pdf_file) as pdf:
                texto_completo = ""
                for page in pdf.pages:
                    t = page.extract_text()
                    if t: texto_completo += t + "\n"
                    
                lineas = [l.strip() for l in texto_completo.split('\n') if l.strip()]
                
                basura_sii = ["DOCUMENTO", "ELECTRÓNICO", "ELECTRONICO", "RECIBIDO", "FACTURA", "R.U.T", "RUT:", "S.I.I", "COPIA", "CEDIBLE", "TIMBRE", "RESOLUCION", "FOLIO", "EMISIÓN", "SEÑOR(ES)"]
                for linea in lineas[:25]:
                    lin_up = linea.upper()
                    if any(b in lin_up for b in basura_sii) or re.search(r'\d{1,2}\.\d{3}\.\d{3}', lin_up): continue
                    if lin_up.startswith("GIRO") or lin_up.startswith("DIRECCION") or lin_up.startswith("COMUNA") or lin_up.startswith("CONTACTO"): continue
                    if len(lin_up) > 3 and not re.match(r'^\d+$', lin_up):
                        if not proveedor["razon_social"]:
                            proveedor["razon_social"] = linea[:60].strip()
                            break 
                
                for linea in lineas:
                    rut_match = re.search(r'(\d{1,2}\.\d{3}\.\d{3}-[\dKk])', linea)
                    if rut_match:
                        proveedor["rut"] = rut_match.group(1)
                        break

                for linea in reversed(lineas):
                    lin_limpia = linea.upper().replace(' ', '')
                    if "MONTOTOTAL" in lin_limpia or "TOTALEXENTO" in lin_limpia or "TOTAL$" in lin_limpia or lin_limpia.startswith("TOTAL"):
                        montos = re.findall(r'\d{1,3}(?:\.\d{3})*', linea) 
                        if not montos: montos = re.findall(r'\d+', lin_limpia)
                        if montos:
                            try:
                                total_factura = int(montos[-1].replace('.', ''))
                                if total_factura > 0: break
                            except: pass

                leyendo_items = False
                for linea in lineas:
                    lin_up = linea.upper()
                    tiene_cantidad = any(p in lin_up for p in ["CANTIDAD", "CANT."])
                    tiene_detalle = any(p in lin_up for p in ["DESCRIPCION", "DETALLE", "CODIGO", "ARTÍCULO", "ARTICULO"])
                    
                    if (tiene_cantidad and tiene_detalle) or ("ARTÍCULO" in lin_up and "VALOR" in lin_up):
                        leyendo_items = True
                        continue
                        
                    if any(p in lin_up for p in ["MONTO NETO", "SUBTOTAL", "IVA 19", "SON:", "TIMBRE", "REFERENCIAS"]):
                        leyendo_items = False
                        
                    if leyendo_items:
                        match_um = re.search(r'\b(\d+[\.,]?\d*)\s+(UN|MT|ML|RL|KG|LTS|PAR|CJA|M2|SET|PL|C/U|TIRA|X)\b', lin_up)
                        if match_um:
                            cantidad_str = match_um.group(1).replace(',', '.')
                            try: cantidad = int(float(cantidad_str))
                            except: cantidad = 1
                            if cantidad <= 0: cantidad = 1
                            um = match_um.group(2)
                            if um == 'X': um = 'UN'
                            
                            inicio_match, fin_match = match_um.start(), match_um.end()
                            antes_str, despues_str = linea[:inicio_match].strip(), linea[fin_match:].strip()
                            despues_limpio = re.sub(r'(\s+\$?\d+[\.,]?\d*\s*[%$]*)+$', '', despues_str).strip()
                            
                            codigo, desc = "", ""
                            if re.search(r'[A-Za-z]{3,}', despues_limpio):
                                desc = despues_limpio
                                partes_antes = antes_str.split()
                                if partes_antes: codigo = partes_antes[-1]
                            else:
                                antes_limpio = re.sub(r'^\d+\s+', '', antes_str).strip()
                                desc = antes_limpio
                                cod_match = re.search(r'^([A-Za-z0-9\-]{3,10})\b', antes_limpio)
                                if cod_match: codigo = cod_match.group(1)
                                
                            if len(desc) < 3 or "PAGINA" in desc.upper(): continue
                                
                            if not codigo:
                                palabras = [p for p in desc.split() if len(p) > 2 and not any(c.isdigit() for c in p)]
                                if len(palabras) >= 2: codigo = f"{palabras[0][:3]}-{palabras[1][:3]}".upper()
                                else: codigo = f"MAT-{cantidad}"
                                
                            items_detectados.append({
                                "codigo": codigo[:15], "nombre": desc[:80], "categoria": "Insumos Varios",
                                "unidad_medida": um, "cantidad_ingresar": cantidad
                            })
        else: return {"error": "Sube un archivo PDF o XML."}

        if not proveedor["razon_social"]: proveedor["razon_social"] = "Proveedor Desconocido"
        if not items_detectados: items_detectados.append({"codigo": "GEN-01", "nombre": "Materiales Varios", "categoria": "Sustratos", "unidad_medida": "UN", "cantidad_ingresar": 1})

        return {"proveedor": proveedor, "total": total_factura, "items": items_detectados}
    except Exception as e:
        return {"error": str(e)}

# 🔥 NUEVO: ESCÁNER DE BOLETAS CON CÁMARA USANDO GEMINI
@app.post("/upload-boleta/")
async def upload_boleta(file: UploadFile = File(...)):
    if not modelo_vision:
        raise HTTPException(status_code=500, detail="Gemini API Key no configurada en el servidor.")
        
    try:
        image_data = await file.read()
        img = Image.open(io.BytesIO(image_data))

        prompt = """
        Eres el asistente contable de CREAdesign. 
        Analiza esta boleta, comprobante de pago o factura de compra.
        Devuelve ÚNICAMENTE un objeto JSON válido con la siguiente estructura. No incluyas markdown ni comillas adicionales:
        {
            "proveedor": "Nombre del negocio o comercio",
            "fecha": "Fecha de la compra en formato YYYY-MM-DD",
            "total": Monto total pagado (solo números, sin símbolos ni puntos),
            "categoria": "Elige solo una de estas: Materiales y Sustratos, Tintas e Insumos, Herramientas y Repuestos, Servicios Básicos, Combustible y Peajes, Colaciones en Terreno, Otros Gastos"
        }
        """

        respuesta = modelo_vision.generate_content([prompt, img])
        texto_limpio = respuesta.text.replace("```json", "").replace("```", "").strip()
        
        datos = json.loads(texto_limpio)
        return datos

    except json.JSONDecodeError:
        print("La IA no devolvió un JSON válido:", respuesta.text)
        raise HTTPException(status_code=500, detail="Error al decodificar la lectura de la boleta.")
    except Exception as e:
        print(f"Error interno al procesar la boleta: {str(e)}")
        raise HTTPException(status_code=500, detail="No se pudo procesar la imagen de la boleta.")


# ==========================================
# GESTIÓN DE USUARIOS (BLINDAJE TOTAL SQL)
# ==========================================
class UsuarioCreate(BaseModel):
    username: str
    password: str
    rol: str

class UsuarioUpdate(BaseModel):
    password: str = None
    rol: str = None

class LoginRequest(BaseModel):
    username: str
    password: str

@app.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    # 🔑 LA LLAVE MAESTRA
    if req.username.lower() == "francho" and req.password == "creadesign2026":
        return {"username": "Francho (Dios)", "rol": "Admin"}
        
    usuario = db.execute(
        text("SELECT username, rol FROM usuarios WHERE username = :u AND password = :p"), 
        {"u": req.username.lower(), "p": req.password}
    ).fetchone()
    
    if usuario:
        return {"username": usuario[0], "rol": usuario[1]}
        
    # Salva-vidas para usuarios viejos
    if req.username.lower() in ["admin", "taller"]:
        return {"username": req.username.capitalize(), "rol": "Admin" if req.username.lower() == "admin" else "Taller"}
        
    raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")

@app.get("/usuarios/")
def leer_usuarios(db: Session = Depends(get_db)):
    rows = db.execute(text("SELECT id, username, rol FROM usuarios")).fetchall()
    return [{"id": r[0], "username": r[1], "rol": r[2]} for r in rows]

@app.post("/usuarios/")
def crear_usuario(user: UsuarioCreate, db: Session = Depends(get_db)):
    try:
        db.execute(
            text("INSERT INTO usuarios (username, password, rol) VALUES (:u, :p, :r)"), 
            {"u": user.username.lower(), "p": user.password, "r": user.rol}
        )
        db.commit()
        return {"msg": "Usuario creado"}
    except:
        db.rollback()
        raise HTTPException(status_code=400, detail="El usuario ya existe")

@app.put("/usuarios/{id}")
def editar_usuario(id: int, user: UsuarioUpdate, db: Session = Depends(get_db)):
    if user.password:
        db.execute(text("UPDATE usuarios SET password = :p WHERE id = :id"), {"p": user.password, "id": id})
    if user.rol:
        db.execute(text("UPDATE usuarios SET rol = :r WHERE id = :id"), {"r": user.rol, "id": id})
    db.commit()
    return {"msg": "Actualizado"}

@app.delete("/usuarios/{id}")
def borrar_usuario(id: int, db: Session = Depends(get_db)):
    db.execute(text("DELETE FROM usuarios WHERE id = :id"), {"id": id})
    db.commit()
    return {"msg": "Borrado"}
    # ==========================================
# GESTIÓN DE APUNTES Y PENDIENTES (SINCRO NUBE)
# ==========================================
class TareaCreate(BaseModel):
    texto: str
    fecha: str = None

@app.get("/tareas/")
def leer_tareas(db: Session = Depends(get_db)):
    # Escudo: Crea la tabla automáticamente en Supabase si no existe
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS tareas (
            id SERIAL PRIMARY KEY,
            texto TEXT NOT NULL,
            fecha TEXT,
            lista BOOLEAN DEFAULT FALSE
        )
    """))
    db.commit()
    
    rows = db.execute(text("SELECT id, texto, fecha, lista FROM tareas ORDER BY id DESC")).fetchall()
    return [{"id": r[0], "texto": r[1], "fecha": r[2], "lista": r[3]} for r in rows]

@app.post("/tareas/")
def crear_tarea(tarea: TareaCreate, db: Session = Depends(get_db)):
    db.execute(
        text("INSERT INTO tareas (texto, fecha, lista) VALUES (:t, :f, FALSE)"),
        {"t": tarea.texto, "f": tarea.fecha}
    )
    db.commit()
    return {"msg": "Tarea guardada en la nube"}

@app.put("/tareas/{id}")
def toggle_tarea(id: int, db: Session = Depends(get_db)):
    db.execute(text("UPDATE tareas SET lista = NOT lista WHERE id = :id"), {"id": id})
    db.commit()
    return {"msg": "Estado de tarea actualizado"}

@app.delete("/tareas/{id}")
def borrar_tarea(id: int, db: Session = Depends(get_db)):
    db.execute(text("DELETE FROM tareas WHERE id = :id"), {"id": id})
    db.commit()
    return {"msg": "Tarea eliminada"}
