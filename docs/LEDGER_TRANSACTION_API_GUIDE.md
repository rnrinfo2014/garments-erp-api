# Ledger Transaction API Documentation

## Overview

The Ledger Transaction API provides comprehensive double-entry bookkeeping functionality for the Garments ERP system. It supports financial transactions, batch processing, templates, and detailed reporting with proper integration to the Accounts Master.

## API Base URL
```
http://localhost:8000/api/ledger-transactions
```

## Authentication
All endpoints require JWT Token Authentication. Include the token in the Authorization header:
```
Authorization: Bearer <your_jwt_token>
```

To get a token, authenticate at:
```
POST /api/auth/login
```

---

## Data Models

### LedgerTransaction
The main transaction model supporting double-entry bookkeeping:

```typescript
interface LedgerTransaction {
  id: number;
  transaction_number: string;      // Unique transaction number
  transaction_date: string;        // ISO date format
  account_code: string;           // Reference to AccountsMaster
  description: string;            // Transaction description
  reference_type?: string;        // PURCHASE_ORDER, SALE, PAYMENT, etc.
  reference_id?: string;          // Source document ID
  debit_amount: number;          // Debit amount (decimal)
  credit_amount: number;         // Credit amount (decimal)
  voucher_type: string;          // JV, PV, RV, SV, PurchaseV
  voucher_number?: string;       // Voucher number
  party_type?: string;           // CUSTOMER, SUPPLIER, VENDOR, EMPLOYEE
  party_id?: string;             // Party ID
  party_name?: string;           // Party name
  is_reconciled: boolean;        // Reconciliation status
  reconciled_date?: string;      // Reconciliation date
  is_active: boolean;            // Active status
  is_posted: boolean;            // Posted status
  notes?: string;                // Additional notes
  created_by: string;            // Created by user
  updated_by?: string;           // Updated by user
  created_at: string;            // Creation timestamp
  updated_at: string;            // Update timestamp
}
```

### Enums

```typescript
enum VoucherType {
  JOURNAL = "JV",
  PAYMENT = "PV", 
  RECEIPT = "RV",
  SALES = "SV",
  PURCHASE = "PurchaseV"
}

enum ReferenceType {
  PURCHASE_ORDER = "PURCHASE_ORDER",
  SALE = "SALE",
  PAYMENT = "PAYMENT",
  RECEIPT = "RECEIPT",
  JOURNAL = "JOURNAL"
}

enum PartyType {
  CUSTOMER = "CUSTOMER",
  SUPPLIER = "SUPPLIER", 
  VENDOR = "VENDOR",
  EMPLOYEE = "EMPLOYEE"
}
```

---

## API Endpoints

### 1. Create Ledger Transaction
**POST** `/api/ledger-transactions/`

Creates a new ledger transaction.

#### Request Body:
```json
{
  "transaction_number": "JV202508250001",
  "transaction_date": "2025-08-25T10:00:00",
  "account_code": "CASH001",
  "description": "Cash sale transaction",
  "reference_type": "SALE",
  "reference_id": "SALE-001",
  "debit_amount": 1000.00,
  "credit_amount": 0.00,
  "voucher_type": "SV",
  "voucher_number": "SV-001",
  "party_type": "CUSTOMER",
  "party_id": "CUST001",
  "party_name": "ABC Customer",
  "is_posted": true,
  "notes": "Cash sale for products",
  "created_by": "user123"
}
```

#### Response:
```json
{
  "id": 1,
  "transaction_number": "JV202508250001",
  "transaction_date": "2025-08-25T10:00:00",
  "account_code": "CASH001",
  "description": "Cash sale transaction",
  "debit_amount": 1000.00,
  "credit_amount": 0.00,
  "transaction_amount": 1000.00,
  "transaction_type": "DEBIT",
  "balance_effect": 1000.00,
  "created_by": "user123",
  "created_at": "2025-08-25T10:00:00",
  "updated_at": "2025-08-25T10:00:00"
}
```

### 2. Get Ledger Transactions
**GET** `/api/ledger-transactions/`

Retrieves ledger transactions with filtering options.

#### Query Parameters:
- `skip` (int, optional): Number of records to skip (default: 0)
- `limit` (int, optional): Maximum records to return (default: 100, max: 1000)
- `account_code` (string, optional): Filter by account code
- `voucher_type` (VoucherType, optional): Filter by voucher type
- `reference_type` (ReferenceType, optional): Filter by reference type
- `reference_id` (string, optional): Filter by reference ID
- `party_type` (PartyType, optional): Filter by party type
- `party_id` (string, optional): Filter by party ID
- `date_from` (date, optional): Filter from date (YYYY-MM-DD)
- `date_to` (date, optional): Filter to date (YYYY-MM-DD)
- `is_posted` (boolean, optional): Filter by posted status
- `is_reconciled` (boolean, optional): Filter by reconciled status

#### Example Request:
```bash
GET /api/ledger-transactions/?account_code=CASH001&date_from=2025-08-01&date_to=2025-08-31&limit=50
```

#### Response:
```json
[
  {
    "id": 1,
    "transaction_number": "JV202508250001",
    "transaction_date": "2025-08-25T10:00:00",
    "account_code": "CASH001",
    "description": "Cash sale transaction",
    "debit_amount": 1000.00,
    "credit_amount": 0.00,
    "transaction_amount": 1000.00,
    "transaction_type": "DEBIT",
    "balance_effect": 1000.00,
    "voucher_type": "SV",
    "is_posted": true,
    "created_by": "user123",
    "created_at": "2025-08-25T10:00:00"
  }
]
```

### 3. Get Specific Transaction
**GET** `/api/ledger-transactions/{transaction_id}`

Retrieves a specific ledger transaction by ID.

#### Response:
```json
{
  "id": 1,
  "transaction_number": "JV202508250001",
  "transaction_date": "2025-08-25T10:00:00",
  "account_code": "CASH001",
  "description": "Cash sale transaction",
  "debit_amount": 1000.00,
  "credit_amount": 0.00,
  "voucher_type": "SV",
  "party_type": "CUSTOMER",
  "party_name": "ABC Customer",
  "is_posted": true,
  "notes": "Cash sale for products"
}
```

### 4. Update Transaction
**PUT** `/api/ledger-transactions/{transaction_id}`

Updates a ledger transaction. Only non-posted transactions can be updated.

#### Request Body:
```json
{
  "description": "Updated cash sale transaction",
  "notes": "Updated notes",
  "updated_by": "user123"
}
```

### 5. Delete Transaction
**DELETE** `/api/ledger-transactions/{transaction_id}`

Soft deletes a ledger transaction. Only non-posted transactions can be deleted.

#### Response: 204 No Content

### 6. Create Bulk Transactions
**POST** `/api/ledger-transactions/bulk`

Creates multiple transactions as a batch with double-entry validation.

#### Request Body:
```json
{
  "batch_number": "BATCH20250825001",
  "batch_date": "2025-08-25T10:00:00",
  "batch_description": "Sales transaction with tax",
  "transactions": [
    {
      "transaction_number": "SV202508250001",
      "transaction_date": "2025-08-25T10:00:00",
      "account_code": "CASH001",
      "description": "Cash received from customer",
      "debit_amount": 1180.00,
      "credit_amount": 0.00,
      "voucher_type": "SV",
      "created_by": "user123"
    },
    {
      "transaction_number": "SV202508250002",
      "transaction_date": "2025-08-25T10:00:00",
      "account_code": "SALES001",
      "description": "Sales revenue",
      "debit_amount": 0.00,
      "credit_amount": 1000.00,
      "voucher_type": "SV",
      "created_by": "user123"
    },
    {
      "transaction_number": "SV202508250003",
      "transaction_date": "2025-08-25T10:00:00",
      "account_code": "TAX001",
      "description": "GST output tax",
      "debit_amount": 0.00,
      "credit_amount": 180.00,
      "voucher_type": "SV",
      "created_by": "user123"
    }
  ],
  "created_by": "user123"
}
```

### 7. Account Balance Report
**GET** `/api/ledger-transactions/reports/account-balance`

Generates account balance report.

#### Query Parameters:
- `account_code` (string, optional): Specific account code
- `account_type` (string, optional): Filter by account type
- `date_from` (date, optional): Calculate balance from date
- `date_to` (date, optional): Calculate balance to date

#### Response:
```json
[
  {
    "account_code": "CASH001",
    "account_name": "Cash in Hand",
    "account_type": "Asset",
    "total_debits": 5000.00,
    "total_credits": 3000.00,
    "net_balance": 2000.00,
    "transaction_count": 15,
    "last_transaction_date": "2025-08-25T15:30:00"
  }
]
```

### 8. Transaction Batches
**GET** `/api/ledger-transactions/batches/`

Retrieves transaction batches.

#### Query Parameters:
- `skip` (int, optional): Records to skip
- `limit` (int, optional): Maximum records
- `date_from` (date, optional): Filter from date
- `date_to` (date, optional): Filter to date
- `is_posted` (boolean, optional): Filter by posted status

### 9. Transaction Templates
**GET** `/api/ledger-transactions/templates/`

Retrieves transaction templates.

**POST** `/api/ledger-transactions/templates/`

Creates new transaction template.

---

## Integration Examples

### Frontend Integration (React/Vue.js)

#### 1. Create a Cash Sale Transaction
```javascript
const createCashSaleTransaction = async (saleData) => {
  const token = localStorage.getItem('jwt_token');
  
  const transactions = [
    {
      transaction_date: new Date().toISOString(),
      account_code: 'CASH001',
      description: `Cash sale - ${saleData.customer_name}`,
      debit_amount: saleData.total_amount,
      credit_amount: 0.00,
      voucher_type: 'SV',
      reference_type: 'SALE',
      reference_id: saleData.sale_id,
      party_type: 'CUSTOMER',
      party_id: saleData.customer_id,
      party_name: saleData.customer_name,
      created_by: saleData.user_id
    },
    {
      transaction_date: new Date().toISOString(),
      account_code: 'SALES001',
      description: `Sales revenue - ${saleData.customer_name}`,
      debit_amount: 0.00,
      credit_amount: saleData.net_amount,
      voucher_type: 'SV',
      reference_type: 'SALE',
      reference_id: saleData.sale_id,
      party_type: 'CUSTOMER',
      party_id: saleData.customer_id,
      party_name: saleData.customer_name,
      created_by: saleData.user_id
    }
  ];

  // Add tax transaction if applicable
  if (saleData.tax_amount > 0) {
    transactions.push({
      transaction_date: new Date().toISOString(),
      account_code: 'TAX001',
      description: `GST - ${saleData.customer_name}`,
      debit_amount: 0.00,
      credit_amount: saleData.tax_amount,
      voucher_type: 'SV',
      reference_type: 'SALE',
      reference_id: saleData.sale_id,
      party_type: 'CUSTOMER',
      party_id: saleData.customer_id,
      party_name: saleData.customer_name,
      created_by: saleData.user_id
    });
  }

  const response = await fetch('/api/ledger-transactions/bulk', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
      batch_date: new Date().toISOString(),
      batch_description: `Cash sale transaction for ${saleData.customer_name}`,
      transactions: transactions,
      created_by: saleData.user_id
    })
  });

  return response.json();
};
```

#### 2. Get Account Balance
```javascript
const getAccountBalance = async (accountCode, dateFrom, dateTo) => {
  const token = localStorage.getItem('jwt_token');
  
  const params = new URLSearchParams();
  if (accountCode) params.append('account_code', accountCode);
  if (dateFrom) params.append('date_from', dateFrom);
  if (dateTo) params.append('date_to', dateTo);

  const response = await fetch(`/api/ledger-transactions/reports/account-balance?${params}`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });

  return response.json();
};
```

#### 3. Create Purchase Payment Transaction
```javascript
const createPurchasePayment = async (paymentData) => {
  const token = localStorage.getItem('jwt_token');
  
  const transactions = [
    {
      transaction_date: new Date().toISOString(),
      account_code: 'CREDITORS001', // Accounts Payable
      description: `Payment to ${paymentData.supplier_name}`,
      debit_amount: paymentData.payment_amount,
      credit_amount: 0.00,
      voucher_type: 'PV',
      reference_type: 'PAYMENT',
      reference_id: paymentData.payment_id,
      party_type: 'SUPPLIER',
      party_id: paymentData.supplier_id,
      party_name: paymentData.supplier_name,
      created_by: paymentData.user_id
    },
    {
      transaction_date: new Date().toISOString(),
      account_code: paymentData.payment_mode === 'CASH' ? 'CASH001' : 'BANK001',
      description: `Payment via ${paymentData.payment_mode} to ${paymentData.supplier_name}`,
      debit_amount: 0.00,
      credit_amount: paymentData.payment_amount,
      voucher_type: 'PV',
      reference_type: 'PAYMENT',
      reference_id: paymentData.payment_id,
      party_type: 'SUPPLIER',
      party_id: paymentData.supplier_id,
      party_name: paymentData.supplier_name,
      created_by: paymentData.user_id
    }
  ];

  const response = await fetch('/api/ledger-transactions/bulk', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
      batch_date: new Date().toISOString(),
      batch_description: `Payment to supplier ${paymentData.supplier_name}`,
      transactions: transactions,
      created_by: paymentData.user_id
    })
  });

  return response.json();
};
```

---

## Error Handling

### Common Error Responses

#### 400 Bad Request
```json
{
  "detail": "Either debit_amount or credit_amount must be greater than 0"
}
```

#### 404 Not Found
```json
{
  "detail": "Account with code INVALID001 not found"
}
```

#### 422 Validation Error
```json
{
  "detail": [
    {
      "loc": ["body", "debit_amount"],
      "msg": "ensure this value is greater than or equal to 0",
      "type": "value_error.number.not_ge"
    }
  ]
}
```

#### 500 Internal Server Error
```json
{
  "detail": "Error creating transaction: Database connection failed"
}
```

---

## Best Practices

### 1. Double-Entry Bookkeeping
Always ensure that for every transaction batch, the total debits equal total credits:
- **Debit**: Increases Assets and Expenses, Decreases Liabilities and Income
- **Credit**: Increases Liabilities and Income, Decreases Assets and Expenses

### 2. Transaction Numbering
The system automatically generates unique transaction numbers in the format:
- `{VoucherType}{YYYYMMDD}{0001}`
- Example: `JV202508250001`, `PV202508250002`

### 3. Reference Management
Use `reference_type` and `reference_id` to link transactions to source documents:
- Purchase Orders: `reference_type: "PURCHASE_ORDER"`, `reference_id: "PO-123"`
- Sales: `reference_type: "SALE"`, `reference_id: "SALE-456"`

### 4. Party Information
Include party details for better reporting and reconciliation:
```json
{
  "party_type": "SUPPLIER",
  "party_id": "SUPP001",
  "party_name": "ABC Textiles Ltd"
}
```

### 5. Bulk Transactions
Use bulk transaction endpoint for complex operations that involve multiple accounts:
- Sales with tax
- Purchase with multiple expenses  
- Salary payments with deductions

### 6. Reconciliation
Mark transactions as reconciled when they match with bank statements or other external documents:
```json
{
  "is_reconciled": true,
  "reconciled_date": "2025-08-25T15:30:00"
}
```

---

## Testing

### Sample Test Data

#### Create a Simple Cash Sale
```bash
curl -X POST "http://localhost:8000/api/ledger-transactions/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_date": "2025-08-25T10:00:00",
    "account_code": "CASH001",
    "description": "Cash sale to customer",
    "debit_amount": 1000.00,
    "credit_amount": 0.00,
    "voucher_type": "SV",
    "reference_type": "SALE",
    "reference_id": "SALE-001",
    "created_by": "testuser"
  }'
```

#### Get Account Balance
```bash
curl -X GET "http://localhost:8000/api/ledger-transactions/reports/account-balance?account_code=CASH001" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## Database Schema

The ledger transaction system uses three main tables:

1. **ledger_transactions**: Main transaction records
2. **transaction_batches**: Batch processing for multiple transactions  
3. **transaction_templates**: Predefined transaction templates

All tables include proper foreign key constraints to `accounts_master` and audit fields for tracking changes.

---

## Support

For API support and integration assistance, please refer to:
- API Documentation: `/docs` (Swagger UI)
- Technical Support: Contact your system administrator
- Database Schema: Review the model definitions in the codebase
