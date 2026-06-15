import csv
import urllib.request
import json
import ssl

# La dirección de la nube de tu ERP
API_URL = "https://creadesign-backend.onrender.com/clientes/"
ARCHIVO_CSV = "lista de clientes.csv"

# Ignorar advertencias de SSL
context = ssl._create_unverified_context()

print("🚀 Conectando con la nube de CREAdesign...")

try:
    # Leemos con utf-8-sig para evitar basura de Excel
    with open(ARCHIVO_CSV, mode="r", encoding="utf-8-sig") as file:
        # AQUI ESTA LA MAGIA: Le decimos que use el punto y coma de tu Excel
        reader = csv.DictReader(file, delimiter=";")
        
        agregados = 0
        for row in reader:
            # Buscamos exactamente los títulos con tildes que tienes en tu foto
            cliente_data = {
                "alias": row.get("Alias", "").strip() if row.get("Alias") else "",
                "razon_social": row.get("Razón Social", "").strip() if row.get("Razón Social") else "",
                "rut": row.get("RUT", "").strip() if row.get("RUT") else "",
                "email": row.get("Email", "").strip() if row.get("Email") else "",
                "telefono": row.get("Teléfono", "").strip() if row.get("Teléfono") else "",
                "direccion": row.get("Dirección", "").strip() if row.get("Dirección") else ""
            }
            
            # Solo subir si hay Razón Social o RUT validos
            if cliente_data["razon_social"] or cliente_data["rut"]:
                print(f"Subiendo: {cliente_data['razon_social']}...")
                
                try:
                    data_codificada = json.dumps(cliente_data).encode('utf-8')
                    req = urllib.request.Request(API_URL, data=data_codificada, headers={'Content-Type': 'application/json'}, method='POST')
                    urllib.request.urlopen(req, context=context)
                    agregados += 1
                except Exception as e:
                    print(f"❌ Error al subir {cliente_data['razon_social']}: {e}")

        print(f"🎉 ¡Éxito! Se subieron {agregados} clientes a tu base de datos.")
        
except FileNotFoundError:
    print("🚨 ERROR: No se encontró el archivo 'lista de clientes.csv'.")
except Exception as e:
    print(f"🚨 ERROR INESPERADO: {e}")
