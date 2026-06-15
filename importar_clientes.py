import csv
import urllib.request
import json
import ssl

# La dirección de la nube de tu Cerebro
API_URL = "https://creadesign-backend.onrender.com/clientes/"
ARCHIVO_CSV = "lista de clientes.csv"

# Ignorar advertencias de SSL al enviar datos
context = ssl._create_unverified_context()

print("🚀 Conectando con la nube de CREAdesign...")

try:
    # Intenta abrir el archivo. Si tu Excel usa punto y coma, cambia delimiter="," por delimiter=";"
    with open(ARCHIVO_CSV, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file, delimiter=",")
        
        agregados = 0
        for row in reader:
            # Capturamos los datos del CSV (si una columna no existe, queda en blanco)
            cliente_data = {
                "alias": row.get("Alias", ""),
                "razon_social": row.get("Razon Social", ""),
                "rut": row.get("RUT", ""),
                "email": row.get("Email", ""),
                "telefono": row.get("Telefono", ""),
                "direccion": row.get("Direccion", "")
            }
            
            # Solo subir si hay Razón Social o RUT
            if cliente_data["razon_social"] or cliente_data["rut"]:
                print(f"Subiendo a: {cliente_data['razon_social']}...")
                
                # Convertir a JSON y enviar a la nube
                data_codificada = json.dumps(cliente_data).encode('utf-8')
                req = urllib.request.Request(API_URL, data=data_codificada, headers={'Content-Type': 'application/json'}, method='POST')
                
                try:
                    urllib.request.urlopen(req, context=context)
                    agregados += 1
                except Exception as e:
                    print(f"❌ Error al subir {cliente_data['razon_social']}: {e}")

        print(f"🎉 ¡Proceso terminado! Se subieron {agregados} clientes a la base de datos oficial.")
        
except FileNotFoundError:
    print("🚨 ERROR: No se encontró el archivo 'lista de clientes.csv'. Verifica que se llame exactamente así.")
