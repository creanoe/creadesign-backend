import csv
import database

# Abrimos la conexión a la base de datos
db = database.SessionLocal()

print("Iniciando la importación masiva de clientes...")

try:
    # Leemos el archivo indicando que el separador es el punto y coma (;)
    with open('lista de clientes.csv', mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file, delimiter=';')
        
        clientes_agregados = 0
        
        for row in reader:
            # Capturamos las columnas exactas de tu Excel
            razon_social = row.get('Razón Social', '').strip()
            rut = row.get('RUT', '').strip()
            correo = row.get('Correo', '').strip()
            telefono = row.get('Teléfono', '').strip()
            direccion = row.get('Dirección', '').strip()
            alias = row.get('Alias', '').strip()

            # Limpiamos los "N/A" para que tu sistema se vea profesional y limpio
            if correo == 'N/A': correo = ''
            if telefono == 'N/A': telefono = ''
            if direccion == 'N/A': direccion = ''
            if alias == 'N/A': alias = ''

            # Verificamos que el cliente no exista ya (buscando por RUT)
            existe = db.query(database.Cliente).filter(database.Cliente.rut == rut).first()
            
            if not existe and razon_social:
                nuevo_cliente = database.Cliente(
                    razon_social=razon_social,
                    rut=rut,
                    email=correo,
                    telefono=telefono,
                    direccion=direccion,
                    alias=alias  # <--- Aquí guardamos el Alias
                )
                db.add(nuevo_cliente)
                clientes_agregados += 1

        # Guardamos todos los cambios de golpe
        db.commit()
        print(f"✅ ¡Éxito total! Se importaron {clientes_agregados} clientes a tu ERP CREAdesign.")

except Exception as e:
    print(f"❌ Ocurrió un error al leer el archivo: {e}")
finally:
    db.close()