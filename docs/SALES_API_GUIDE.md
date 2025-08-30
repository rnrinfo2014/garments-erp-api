# Sales Management API Guide

## Overview
The Sales Management API provides comprehensive functionality for managing sales transactions, including sales orders, items, payments, stock management, and accounting integration.

## Features
- **Sales Management**: Create, update, and track sales orders
- **Item Management**: Add/modify items within sales orders
- **Payment Tracking**: Record and track payments against sales
- **Stock Integration**: Automatic stock deduction upon sale confirmation
- **Accounting Integration**: Automatic ledger entries for sales and payments
- **Reporting**: Sales summaries and performance reports

## API Endpoints

### Sales Management

#### Create Sale
```
POST /api/sales/sales/
```

**Request Body:**
```json
{
  "customer_id": 1,
  "sale_date": "2025-08-26",
  "sale_type": "regular",
  "reference_number": "REF-001",
  "notes": "Sample sale",
  "discount_amount": 100.00,
  "tax_amount": 50.00,
  "sale_items": [
    {
      "product_variant_id": 1,
      "item_description": "Smart Plus - Size 36 - Full Sleeve",
      "quantity": 5,
      "unit_price": 500.00,
      "discount_percentage": 5.0,
      "tax_percentage": 12.0
    }
  ]
}
```

**Response:**
```json
{
  "id": 1,
  "sale_number": "SAL-2025-0001",
  "customer_id": 1,
  "sale_date": "2025-08-26",
  "sale_type": "regular",
  "subtotal": 2500.00,
  "discount_amount": 125.00,
  "tax_amount": 285.00,
  "total_amount": 2660.00,
  "payment_status": "pending",
  "paid_amount": 0.00,
  "balance_amount": 2660.00,
  "status": "draft",
  "sale_items": [...],
  "sale_payments": []
}
```

#### List Sales
```
GET /api/sales/sales/
```

**Query Parameters:**
- `skip`: Number of records to skip (default: 0)
- `limit`: Number of records to return (default: 100)
- `search_filter`: General search filter
- `customer_id`: Filter by customer ID
- `status`: Filter by status (draft, confirmed, shipped, completed, cancelled)
- `payment_status`: Filter by payment status (pending, partial, paid)
- `sale_date_from`: Filter from date (YYYY-MM-DD)
- `sale_date_to`: Filter to date (YYYY-MM-DD)
- `is_active`: Filter active sales (default: true)

**Response:**
```json
{
  "sales": [
    {
      "id": 1,
      "sale_number": "SAL-2025-0001",
      "customer_name": "John Doe",
      "customer_code": "CUST-001",
      "total_amount": 2660.00,
      "payment_status": "pending",
      "status": "draft",
      "sale_date": "2025-08-26",
      "creator_name": "admin"
    }
  ],
  "total": 1,
  "page": 1,
  "size": 100,
  "pages": 1
}
```

#### Get Sale Details
```
GET /api/sales/sales/{sale_id}
```

#### Update Sale
```
PUT /api/sales/sales/{sale_id}
```

#### Confirm Sale
```
POST /api/sales/sales/{sale_id}/confirm
```

This endpoint:
- Changes sale status from "draft" to "confirmed"
- Deducts stock for all sale items
- Creates stock ledger entries

### Payment Management

#### Create Payment
```
POST /api/sales/sales/{sale_id}/payments/
```

**Request Body:**
```json
{
  "payment_date": "2025-08-26",
  "payment_amount": 1000.00,
  "payment_method": "cash",
  "payment_reference": "CASH-001",
  "bank_account_id": 1,
  "notes": "Partial payment"
}
```

**Response:**
```json
{
  "id": 1,
  "sale_id": 1,
  "payment_date": "2025-08-26",
  "payment_amount": 1000.00,
  "payment_method": "cash",
  "payment_status": "received",
  "transaction_id": 101,
  "created_at": "2025-08-26T10:00:00"
}
```

#### List Sale Payments
```
GET /api/sales/sales/{sale_id}/payments/
```

### Reporting

#### Sales Summary
```
GET /api/sales/sales/reports/summary
```

**Response:**
```json
{
  "total_sales": 150,
  "total_amount": 125000.00,
  "paid_amount": 100000.00,
  "pending_amount": 25000.00,
  "today_sales": 5,
  "today_amount": 12500.00,
  "month_sales": 45,
  "month_amount": 37500.00
}
```

#### Sales Status Summary
```
GET /api/sales/sales/reports/status-summary
```

**Response:**
```json
{
  "draft": 10,
  "confirmed": 25,
  "shipped": 20,
  "completed": 85,
  "cancelled": 10,
  "total": 150
}
```

## Data Models

### Sale Model
```json
{
  "id": "integer",
  "sale_number": "string (unique)",
  "sale_date": "date",
  "customer_id": "integer (foreign key)",
  "subtotal": "decimal",
  "tax_amount": "decimal",
  "discount_amount": "decimal", 
  "total_amount": "decimal",
  "payment_status": "enum (pending, partial, paid)",
  "paid_amount": "decimal",
  "balance_amount": "decimal",
  "sale_type": "enum (regular, wholesale, retail)",
  "reference_number": "string",
  "notes": "text",
  "status": "enum (draft, confirmed, shipped, completed, cancelled)",
  "is_active": "boolean",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### Sale Item Model
```json
{
  "id": "integer",
  "sale_id": "integer (foreign key)",
  "product_variant_id": "integer (foreign key)",
  "item_description": "string",
  "quantity": "decimal",
  "unit_price": "decimal",
  "subtotal": "decimal",
  "discount_percentage": "decimal",
  "discount_amount": "decimal",
  "tax_percentage": "decimal", 
  "tax_amount": "decimal",
  "total_amount": "decimal",
  "stock_deducted": "boolean"
}
```

### Sale Payment Model
```json
{
  "id": "integer",
  "sale_id": "integer (foreign key)",
  "payment_date": "date",
  "payment_amount": "decimal",
  "payment_method": "enum (cash, bank, cheque, online, card)",
  "payment_reference": "string",
  "bank_account_id": "integer (foreign key)",
  "cheque_number": "string",
  "cheque_date": "date",
  "payment_status": "enum (received, bounced, cancelled)",
  "transaction_id": "integer (foreign key to ledger_transaction)",
  "notes": "text"
}
```

## Integration Features

### Stock Management Integration
When a sale is confirmed (`POST /api/sales/sales/{sale_id}/confirm`):
1. Stock is automatically deducted for each sale item
2. Product stock ledger entries are created
3. Sale item `stock_deducted` flag is set to true

### Accounting Integration
The system automatically creates accounting transactions:

1. **Sale Entry** (when sale is created):
   - Debit: Customer Account
   - Credit: Sales Revenue Account
   - Amount: Total sale amount

2. **Payment Entry** (when payment is recorded):
   - Debit: Cash/Bank Account
   - Credit: Customer Account
   - Amount: Payment amount

### Business Logic

#### Sale Number Generation
- Format: `SAL-YYYY-XXXX`
- Example: `SAL-2025-0001`
- Auto-incremented sequence per year

#### Payment Status Logic
- `pending`: No payments received
- `partial`: Some payment received, balance remaining
- `paid`: Full amount paid

#### Sale Status Workflow
1. `draft` → `confirmed` (via confirm endpoint)
2. `confirmed` → `shipped` (manual update)
3. `shipped` → `completed` (manual update)
4. Any status → `cancelled` (manual update)

## Error Handling

Common HTTP status codes:
- `200`: Success
- `201`: Created successfully
- `400`: Bad request (validation errors)
- `404`: Resource not found
- `500`: Internal server error

Example error response:
```json
{
  "detail": "Customer not found"
}
```

## Authentication
All endpoints require JWT authentication:
```
Authorization: Bearer <your_jwt_token>
```

## Examples

### Complete Sale Flow

1. **Create Sale:**
```bash
curl -X POST "http://localhost:8000/api/sales/sales/" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": 1,
    "sale_date": "2025-08-26",
    "sale_items": [
      {
        "product_variant_id": 1,
        "quantity": 5,
        "unit_price": 500.00
      }
    ]
  }'
```

2. **Confirm Sale:**
```bash
curl -X POST "http://localhost:8000/api/sales/sales/1/confirm" \
  -H "Authorization: Bearer <token>"
```

3. **Record Payment:**
```bash
curl -X POST "http://localhost:8000/api/sales/sales/1/payments/" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "payment_date": "2025-08-26",
    "payment_amount": 1000.00,
    "payment_method": "cash"
  }'
```

## Performance Considerations

The system includes optimized database indexes for:
- Customer-based queries
- Date-based filtering
- Status-based filtering
- Payment tracking

## Testing

Use the provided test endpoints to verify functionality:
- Create test customers and products first
- Test the complete sale workflow
- Verify stock deductions and accounting entries
