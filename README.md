# 🏦 Credit Approval System

This project is a Django-based Credit Approval System that allows customer registration, eligibility checks, loan creation, and loan viewing through REST APIs. It uses PostgreSQL for database and Docker for containerization. Initial customer and loan data are loaded from Excel files.

---

## 🚀 Features

- Customer registration with auto-approved credit limit
- Loan eligibility checking based on historical credit behavior
- Loan creation with approval/rejection logic
- View individual loan details
- Excel data ingestion (`customer_data.xlsx`, `loan_data.xlsx`)
- Dockerized setup

---

## 🐳 Setup Instructions

1. **Clone the repository:**

   ```bash
   git clone https://github.com/your-username/credit-approve-system.git
   cd credit-approve-system

2. **Add Excel data files:**

   - `customer_data.xlsx`
   - `loan_data.xlsx`
   - Place both files in the root directory of the project.

3. **Start the project using Docker:**

   ```bash
   docker-compose up --build
4. Load initial data into the database:

   ```bash

    docker-compose exec web python manage.py load_initial_data

## 📂 API Endpoints
1. /register
Method: POST
Registers a new customer and calculates approved credit limit.

Request Body:
{
  "first_name": "John",
  "last_name": "Doe",
  "age": 30,
  "monthly_income": 50000,
  "phone_number": "9876543210"
}

Response:
{
  "customer_id": 301,
  "name": "John Doe",
  "age": 30,
  "monthly_income": 50000,
  "approved_limit": 1800000,
  "phone_number": "9876543210"
}


2. /check-eligibility
Method: POST
Checks if a customer is eligible for a loan based on credit score logic.

Request Body:
{
  "customer_id": 301,
  "loan_amount": 100000,
  "interest_rate": 14.5,
  "tenure": 12
}

Response (Approved):
{
  "customer_id": 301,
  "approval": true,
  "interest_rate": 14.5,
  "corrected_interest_rate": 14.5,
  "tenure": 12,
  "monthly_installment": 9025.68
}

Response (Rejected):
{
  "customer_id": 301,
  "approval": false,
  "interest_rate": 10.5,
  "corrected_interest_rate": 16,
  "tenure": 12,
  "monthly_installment": 9048.45,
  "message": "Loan denied: low credit score"
}


3. /create-loan
Method: POST
Creates and approves/rejects a loan based on eligibility rules.

Request Body:

{
  "customer_id": 301,
  "loan_amount": 100000,
  "interest_rate": 14.5,
  "tenure": 12
}

Response:
{
  "loan_id": 5,
  "customer_id": 301,
  "loan_approved": true,
  "message": "Loan approved",
  "monthly_installment": 9025.68
}


4. /view-loan/<loan_id>
Method: GET
Fetch details of a specific loan by ID.
Response:

{
  "loan_id": 5,
  "customer": {
    "id": 301,
    "first_name": "John",
    "last_name": "Doe",
    "phone_number": "9876543210",
    "age": 30
  },
  "loan_amount": 100000,
  "interest_rate": 14.5,
  "monthly_installment": 9025.68,
  "tenure": 12
}


## 🧠 Credit Score Logic
Credit score (out of 100) is calculated based on:
Past EMIs paid on time
Number of past loans
Recent loan activity in the current year
Total approved loan volume
If current debt > approved limit → score = 0

## ✅ Loan Approval Rules
Credit Score	Decision<br>
> 50	✅ Approve<br>
30 – 50	✅ Approve if interest rate ≥ 12%<br>
10 – 30	✅ Approve if interest rate ≥ 16%<br>
< 10	❌ Reject<br>
EMI > 50% of income	❌ Reject<br>

If given interest is too low for the score slab, corrected interest rate will be returned.


## ⚙️ Tech Stack
Django + Django REST Framework
PostgreSQL
Docker & Docker Compose
Excel data via openpyxl

