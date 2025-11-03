import os
import time
import random
import datetime
import boto3
import json
from decimal import Decimal # Penting untuk DynamoDB
from dotenv import load_dotenv
from faker import Faker
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, MetaData
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import OperationalError

# --- 1. Setup Awal ---
load_dotenv()

# Konfigurasi Database RDS
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

# --- BARIS YANG DIUBAH ---
# Ini adalah string koneksi baru untuk PyMySQL
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
# -------------------------

# Konfigurasi DynamoDB
DYNAMO_SALES_TABLE = os.getenv("DYNAMO_SALES_TABLE")
DYNAMO_SALARIES_TABLE = os.getenv("DYNAMO_SALARIES_TABLE")

# Inisialisasi Klien (di luar loop)
fake = Faker('id_ID')
dynamodb = boto3.resource('dynamodb')
sales_table = dynamodb.Table(DYNAMO_SALES_TABLE)
salaries_table = dynamodb.Table(DYNAMO_SALARIES_TABLE)


DEPARTMENTS = ['Sales', 'Engineering', 'HR', 'Marketing', 'Support']
PRODUCTS = ['Laptop Pro', 'Mouse Wireless', 'Keyboard Mekanik', 'Monitor 4K', 'Webcam HD']

# --- 2. Definisi Model Database RDS (Sama) ---
# SQLAlchemy otomatis menerjemahkan ini ke sintaks MySQL
Base = declarative_base()

class Sale(Base):
    __tablename__ = 'sales'
    id = Column(Integer, primary_key=True, index=True)
    product_name = Column(String(100))
    quantity = Column(Integer)
    total_amount = Column(Float)
    sale_time = Column(DateTime, default=datetime.datetime.now(datetime.UTC))

class Salary(Base):
    __tablename__ = 'salaries'
    id = Column(Integer, primary_key=True, index=True)
    employee_name = Column(String(100))
    department = Column(String(50))
    salary_amount = Column(Float)
    payment_time = Column(DateTime, default=datetime.datetime.now(datetime.UTC))

# --- 3. Fungsi Database ---
def setup_database_rds():
    """Mencoba konek ke RDS dan membuat tabel jika belum ada."""
    print(f"Mencoba terhubung ke database RDS (MySQL) di {DB_HOST}...")
    try:
        engine = create_engine(DATABASE_URL)
        # Baris ini yang otomatis membuat tabel
        Base.metadata.create_all(bind=engine)
        print("Koneksi RDS (MySQL) sukses. Tabel telah dicek/dibuat.")
        return engine
    except OperationalError as e:
        print(f"Koneksi RDS GAGAL: {e}")
        print("Pastikan port 3306 dibuka di Security Group RDS untuk EC2 ini.")
        exit(1)

def write_to_dynamo(sale_payload, salary_payload):
    """Menulis data payload ke tabel DynamoDB."""
    try:
        # Konversi float ke Decimal agar diterima DynamoDB
        sale_payload['total_amount'] = Decimal(str(sale_payload['total_amount']))
        salary_payload['salary_amount'] = Decimal(str(salary_payload['salary_amount']))
        
        sales_table.put_item(Item=sale_payload)
        print(f"DYNAMO-WRITE: Berhasil menulis Sale ID: {sale_payload['sale_id']}")
        
        salaries_table.put_item(Item=salary_payload)
        print(f"DYNAMO-WRITE: Berhasil menulis Salary ID: {salary_payload['salary_id']}")
        
    except Exception as e:
        print(f"DYNAMO-ERROR: Gagal menulis ke DynamoDB: {e}")

def generate_and_save(session):
    """Membuat data palsu, menyimpan ke RDS, dan menyimpan ke DynamoDB."""
    try:
        # 1. Buat data Gaji palsu
        new_salary = Salary(
            employee_name=fake.name(),
            department=random.choice(DEPARTMENTS),
            salary_amount=round(random.uniform(5000000, 15000000), 2),
            payment_time=datetime.datetime.now(datetime.UTC)
        )
        session.add(new_salary)

        # 2. Buat data Penjualan palsu
        new_sale = Sale(
            product_name=random.choice(PRODUCTS),
            quantity=random.randint(1, 10),
            total_amount=round(random.uniform(500000, 25000000), 2),
            sale_time=datetime.datetime.now(datetime.UTC)
        )
        session.add(new_sale)

        # 3. Simpan perubahan ke RDS
        session.commit()
        print(f"RDS-WRITE: Berhasil commit Sale '{new_sale.product_name}' dan Gaji '{new_salary.employee_name}'")

        # 4. Ambil ID yang baru dibuat oleh RDS
        session.refresh(new_salary)
        session.refresh(new_sale)

        # 5. Siapkan payload untuk DynamoDB
        salary_payload = {
            'salary_id': new_salary.id,
            'employee_name': new_salary.employee_name,
            'department': new_salary.department,
            'salary_amount': new_salary.salary_amount,
            'payment_time': new_salary.payment_time.isoformat()
        }
        sale_payload = {
            'sale_id': new_sale.id,
            'product_name': new_sale.product_name,
            'quantity': new_sale.quantity,
            'total_amount': new_sale.total_amount,
            'sale_time': new_sale.sale_time.isoformat()
        }
        
        # 6. Tulis ke DynamoDB
        write_to_dynamo(sale_payload, salary_payload)

    except Exception as e:
        print(f"RDS-ERROR: Error saat menyimpan data ke RDS: {e}")
        session.rollback() # Batalkan transaksi jika ada error

# --- 4. Eksekusi Script ---
if __name__ == "__main__":
    if not all([DYNAMO_SALES_TABLE, DYNAMO_SALARIES_TABLE]):
        print("Error: Pastikan DYNAMO_SALES_TABLE dan DYNAMO_SALARIES_TABLE ada di .env.")
        exit(1)
        
    engine = setup_database_rds()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    print("\n--- Memulai Data Generator (Tulis Ganda: RDS-MySQL + DynamoDB) ---")
    
    try:
        while True:
            db_session = LocalSession()
            try:
                generate_and_save(db_session)
                sleep_time = random.randint(5, 10) # Jeda acak
                print(f"--- Tidur selama {sleep_time} detik... ---\n")
                time.sleep(sleep_time)
            finally:
                db_session.close()
    except KeyboardInterrupt:
        print("\n--- Data Generator Dihentikan ---")