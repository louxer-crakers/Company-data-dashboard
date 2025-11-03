# AWS Lambda API Handler: RDS (MySQL) & DynamoDB Backend

## 1. Project Description

This repository contains the Python code for the `api-handler` AWS Lambda function. This function serves as the primary backend for the company dashboard, acting as an intelligent read-only API.

Its core responsibility is to receive HTTP requests from an Amazon API Gateway and route those requests to the most appropriate data source. This provides a "best of both worlds" architecture: high-speed, low-latency access for summary data (from DynamoDB) and high-fidelity, complex query access for detailed reports (from RDS).

## 2. Architectural Role

This function is the "Query" component in our architecture, complementing the EC2 `data-generator` ("Command") script. It does not write or modify data; it only reads.

This design pattern separates the read and write workloads:

* **Fast Path (DynamoDB):** When a user first loads the dashboard, this API serves "summary" data directly from the DynamoDB cache tables. This is extremely fast and scalable.
* **Detail Path (RDS):** When a user requests a full report or needs to see historical data, this API bypasses the cache and queries the primary RDS (MySQL) database directly for complete, authoritative information.

## 3. API Endpoint Specification

The function is designed to be triggered by an API Gateway using **Lambda Proxy Integration**. It routes requests based on the URL path.

| Method | Path | Data Source | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/summary` | **DynamoDB** | Retrieves a fast, limited summary of recent sales and salaries. Designed for high-speed dashboard widgets. |
| `GET` | `/report/sales` | **AWS RDS (SQL)** | Performs a detailed query to fetch the last 100 sales records directly from the primary database. |
| `GET` | `/report/salaries` | **AWS RDS (SQL)** | Performs a detailed query to fetch the last 100 salary payment records directly from the primary database. |

## 4. Deployment Prerequisites

### Lambda Layer

This function requires external Python libraries. You must create a Lambda Layer containing these dependencies and attach it to the function.

**Layer `requirements.txt`:**
```txt
sqlalchemy
PyMySQL
```

## 5. Deployment and Configuration

### Environment Variables

In the Lambda function's configuration, set the following environment variables. The script reads these to securely connect to the databases.

* `DB_HOST`: The private DNS endpoint of your RDS instance.
* `DB_PORT`: `3306`
* `DB_USER`: Your RDS database username.
* `DB_PASSWORD`: Your RDS database password.
* `DB_NAME`: The name of your database (e.g., `company_db`).
* `DYNAMO_SALES_TABLE`: The name of your DynamoDB sales table (e.g., `sales_cache`).
* `DYNAMO_SALARIES_TABLE`: The name of your DynamoDB salaries table (e.g., `salaries_cache`).

### API Gateway Integration

1.  Create a new **REST API** in the Amazon API Gateway console.
2.  Create the resources `/summary`, `/report`, `/report/sales`, and `/report/salaries`.
3.  Create a `GET` method for each endpoint listed in the API table above.
4.  For each `GET` method, set the **Integration type** to `Lambda Function`.
5.  **CRITICAL:** Check the box for **Use Lambda Proxy integration**. The code relies on this to receive the `event` object with the correct path information.
6.  Select your `api-handler` Lambda function.
7.  Deploy the API to a stage (e.g., `v1`). The resulting **Invoke URL** is your public API endpoint.