# AWS Dual-Database Data Generator

## 1. Project Description

This repository contains a Python script designed to run on a private EC2 instance within an AWS VPC. Its primary function is to simulate a continuous stream of company data (sales and salaries), writing this information simultaneously to two different AWS databases:

1.  **AWS RDS (PostgreSQL):** As the primary, relational "source of truth."
2.  **AWS DynamoDB:** As a low-latency NoSQL cache for fast-read operations.

This script acts as the core "data producer" in a larger, event-driven cloud architecture.

## 2. Architectural Context

This script employs a **dual-write strategy**, ensuring that data is immediately available in both the primary transactional database and the high-speed caching layer. This avoids the need for a separate data synchronization service (like a polling Lambda).

The intended architecture is:

* **Private EC2 Instance:** Runs this generator script 24/7.
* **AWS RDS:** Stores the complete, authoritative data.
* **AWS DynamoDB:** Stores an identical, denormalized copy of the data for fast reads.
* **Downstream Consumers (e.g., Lambda + API Gateway):** An API backend can now query DynamoDB for "summary" data and query RDS for "detailed" reports, as both are kept in sync by this script.

## 3. Features

* **Dual-Database Writing:** Atomically generates data and writes to both RDS and DynamoDB in the same operation.
* **Automatic RDS Table Creation:** Uses SQLAlchemy to automatically create the `sales` and `salaries` tables in RDS if they do not exist.
* **Continuous Data Generation:** Runs as an infinite loop to simulate a real-time data feed.
* **Secure Configuration:** Loads all database credentials and resource names from a `.env` file.

## 4. Prerequisites

Before running this script, you must have the following AWS infrastructure and configuration in place:

1.  **VPC:** A VPC with public and private subnets, a NAT Gateway, and an Internet Gateway.
2.  **Bastion Host:** An EC2 instance in a public subnet to provide secure SSH access.
3.  **Private EC2 Instance:** An Amazon Linux instance in a private subnet where this script will run.
4.  **RDS Database:** A PostgreSQL database running in a private subnet.
5.  **DynamoDB Tables:** Two DynamoDB tables (e.g., `sales_cache` and `salaries_cache`) must be created.
6.  **IAM Role (Crucial):** The Private EC2 Instance **must** have an IAM Role attached with a policy granting `dynamodb:PutItem` permissions for your two DynamoDB tables.
7.  **Security Groups:**
    * The Bastion Host's Security Group must allow SSH (port 22) from your IP.
    * The Private Instance's Security Group must allow SSH (port 22) from the Bastion Host's Security Group.
    * The RDS Instance's Security Group must allow PostgreSQL (port 5432) from the Private Instance's Security Group.
8.  **Python 3.8+** installed on the private instance.

## 5. Installation and Setup

1.  Access your private instance via the Bastion Host.
2.  Clone this repository:
    ```bash
    git clone <your-repository-url>
    cd <repository-name>
    ```
3.  Create and activate a Python virtual environment:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```
4.  Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## 6. Configuration

Create a `.env` file in the root of the project directory. This file will store your sensitive credentials.

```bash
nano .env
```
You need to fill the .env file this this env

```bash
DB_HOST=your-rds-endpoint.xxxx.aws-region.rds.amazonaws.com
DB_PORT=3306
DB_USER=your_rds_user
DB_PASSWORD=your_rds_password
DB_NAME=your_rds_db_name

# --- DynamoDB Config ---
DYNAMO_SALES_TABLE=sales_cache
DYNAMO_SALARIES_TABLE=salaries_cache
```

Note: 

- The primary id for salaries table is "salary_id" with type is "number"
- The primary id for sales table is "sale_id" with type is "number"
## 7. Usage

You can run the script manually for testing or configure it as a system service for production use.

A. **Manual Execution**
From your terminal, simply run the Python script:

```bash
python data_generator.py
```