import os
import json
import boto3
import sqlalchemy
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, text
from decimal import Decimal # Penting untuk konversi data DynamoDB

# --- 1. INISIALISASI KONEKSI (DI LUAR HANDLER) ---
# ==========================================================

print("Inisialisasi di luar handler (cold start)...")

# Membaca environment variables
DB_HOST = os.environ["DB_HOST"]
DB_PORT = os.environ["DB_PORT"] # Ini harusnya 3306 dari Env Var
DB_USER = os.environ["DB_USER"]
DB_PASSWORD = os.environ["DB_PASSWORD"]
DB_NAME = os.environ["DB_NAME"]
DYNAMO_SALES_TABLE = os.environ["DYNAMO_SALES_TABLE"]
DYNAMO_SALARIES_TABLE = os.environ["DYNAMO_SALARIES_TABLE"]

# --- BARIS YANG DIUBAH ---
# Ini adalah string koneksi baru untuk PyMySQL
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
# -------------------------

try:
    # Inisialisasi Klien DynamoDB
    dynamodb = boto3.resource('dynamodb')
    sales_table_dynamo = dynamodb.Table(DYNAMO_SALES_TABLE)
    salaries_table_dynamo = dynamodb.Table(DYNAMO_SALARIES_TABLE)
    
    # Inisialisasi Koneksi RDS (SQLAlchemy)
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    print("Inisialisasi koneksi RDS (MySQL) dan DynamoDB berhasil.")

except Exception as e:
    print(f"ERROR: Gagal inisialisasi koneksi: {e}")
    raise e


# --- 2. FUNGSI HELPER ---
# ========================

class DecimalEncoder(json.JSONEncoder):
    """
    Helper class untuk mengubah objek Decimal dari DynamoDB 
    menjadi float agar bisa di-serialize oleh json.dumps().
    """
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        return super(DecimalEncoder, self).default(o)

def format_response(status_code, body_object):
    """
    Fungsi helper untuk memformat semua respons ke format
    yang diharapkan oleh API Gateway.
    """
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*' # Ganti '*' dengan domain frontend Anda
        },
        'body': json.dumps(body_object, cls=DecimalEncoder, default=str) 
        # default=str dipakai untuk handle objek datetime dari RDS
    }

# --- 3. FUNGSI LOGIKA (BUSINESS LOGIC) ---
# (TIDAK ADA YANG BERUBAH DI BAGIAN INI)
# =========================================

def get_fast_summary_from_dynamo():
    """
    JALUR CEPAT: Mengambil data "minim" dari DynamoDB.
    """
    print("LOGIC: Membaca dari DynamoDB (Cepat)")
    try:
        response_sales = sales_table_dynamo.scan(Limit=10)
        response_salaries = salaries_table_dynamo.scan(Limit=10)
        
        data = {
            "recent_sales": response_sales.get('Items', []),
            "recent_salaries": response_salaries.get('Items', [])
        }
        return format_response(200, data)
        
    except Exception as e:
        print(f"ERROR: Gagal membaca dari DynamoDB: {e}")
        return format_response(500, {"error": "Gagal mengambil data summary."})

def get_detailed_report_from_rds(report_type):
    """
    JALUR DETAIL: Mengambil data laporan lengkap dari RDS.
    """
    print(f"LOGIC: Membaca dari RDS (Detail) untuk '{report_type}'")
    
    if report_type not in ['sales', 'salaries']:
        return format_response(400, {"error": "Tipe laporan tidak valid."})
    
    db_session = SessionLocal()
    print("Koneksi RDS session dibuka.")
    
    try:
        # Query ini 100% sama, SQLAlchemy yang menerjemahkannya ke MySQL
        sql_query = text(f"SELECT * FROM {report_type} ORDER BY id DESC LIMIT 100")
        
        results = db_session.execute(sql_query).fetchall()
        data_list = [dict(row._mapping) for row in results]
        
        print(f"Berhasil mengambil {len(data_list)} baris dari RDS.")
        return format_response(200, data_list)
        
    except Exception as e:
        print(f"ERROR: Gagal membaca dari RDS: {e}")
        return format_response(500, {"error": "Gagal mengambil laporan detail."})
    finally:
        db_session.close()
        print("Koneksi RDS session ditutup.")


# --- 4. LAMBDA HANDLER (TITIK MASUK UTAMA) ---
# (TIDAK ADA YANG BERUBAH DI BAGIAN INI)
# ============================================

def lambda_handler(event, context):
    """
    Ini adalah fungsi utama yang dipanggil oleh API Gateway.
    Fungsi ini bertindak sebagai "Router".
    """
    
    print(f"Menerima event: {json.dumps(event)}")
    
    path = event.get('path', '/')
    
    try:
        if path == "/summary":
            return get_fast_summary_from_dynamo()
            
        elif path == "/report/salaries":
            return get_detailed_report_from_rds(report_type='salaries')
            
        elif path == "/report/sales":
            return get_detailed_report_from_rds(report_type='sales')
            
        else:
            body = {
                "message": "Endpoint tidak ditemukan. Coba endpoint yang valid:",
                "endpoints": [
                    "/summary",
                    "/report/sales",
                    "/report/salaries"
                ]
            }
            return format_response(404, body)

    except Exception as e:
        print(f"FATAL ERROR: {e}")
        return format_response(500, {"error": "Terjadi kesalahan internal pada server."})