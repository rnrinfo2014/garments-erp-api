# Supplier Payment System API Documentation

## Overview
The Supplier Payment System provides comprehensive payment processing for suppliers with automatic accounting integration, TDS management, and multi-bill payment support.

## Features
- ✅ Payment against multiple purchase bills  
- ✅ Multiple payment modes (Cash, Bank Transfer, UPI, Cheque, etc.)
- ✅ TDS calculation and tracking
- ✅ Automatic ledger integration with double-entry bookkeeping
- ✅ Payment reconciliation
- ✅ Supplier ledger with running balance
- ✅ Comprehensive reporting and analytics

## API Endpoints

### Authentication
All endpoints require JWT authentication. Include the token in the Authorization header:
```
Authorization: Bearer <your_jwt_token>
```

### 1. Get Outstanding Bills

**GET** `/api/supplier-payments/outstanding-bills/{supplier_id}`

Get list of unpaid/partially paid purchase bills for a supplier.

**Parameters:**
- `supplier_id` (path): Supplier ID
- `as_of_date` (query, optional): Date for outstanding calculation (default: today)

**Response:**
```json
[
  {
    "purchase_id": 1,
    "purchase_number": "PO-000001",
    "purchase_date": "2025-01-15",
    "bill_amount": 10000.00,
    "payments_made": 2000.00,
    "outstanding_amount": 8000.00,
    "days_outstanding": 10,
    "supplier_invoice_number": "INV-001",
    "is_overdue": false
  }
]
```

### 2. Create Payment

**POST** `/api/supplier-payments/`

Create a new supplier payment with multiple bills.

**Request Body:**
```json
{
  "payment_date": "2025-01-25",
  "supplier_id": 1,
  "payment_type": "Against Bill",
  "payment_mode": "Bank Transfer",
  "gross_amount": 10000.00,
  "discount_amount": 500.00,
  "tds_amount": 200.00,
  "other_deductions": 0.00,
  "bank_account_id": "BANK001",
  "transaction_reference": "UTR123456789",
  "tds_rate": 2.00,
  "tds_section": "194C",
  "narration": "Payment against purchase bills",
  "bills": [
    {
      "purchase_id": 1,
      "bill_amount": 10000.00,
      "outstanding_amount": 8000.00,
      "paid_amount": 7500.00,
      "discount_allowed": 500.00,
      "adjustment_amount": 0.00,
      "remarks": "Payment with discount"
    }
  ],
  "created_by": "user123"
}
```

**Response:** Full payment details with calculated fields.

### 3. Pay Against Selected Bills (Simplified)

**POST** `/api/supplier-payments/pay-against-bills`

Create payment against specific bills with automatic calculation.

**Request Body:**
```json
{
  "supplier_id": 1,
  "payment_date": "2025-01-25",
  "payment_mode": "Bank Transfer",
  "selected_bills": [
    {
      "purchase_id": 1,
      "outstanding_amount": 10000.00,
      "paying_amount": 9500.00,
      "discount_allowed": 500.00
    },
    {
      "purchase_id": 2,
      "outstanding_amount": 5000.00,
      "paying_amount": 5000.00,
      "discount_allowed": 0.00
    }
  ],
  "bank_account_id": "BANK001",
  "transaction_reference": "TXN123456789",
  "tds_rate": 2.00,
  "tds_section": "194C",
  "created_by": "user123"
}
```

### 4. Get Payment List

**GET** `/api/supplier-payments/`

Get list of supplier payments with filters.

**Query Parameters:**
- `supplier_id` (optional): Filter by supplier
- `status` (optional): Filter by status (Draft, Posted, Cancelled)
- `payment_date_from` (optional): From date
- `payment_date_to` (optional): To date
- `payment_mode` (optional): Filter by payment mode
- `limit` (optional): Records per page (default: 100)
- `offset` (optional): Skip records (default: 0)

### 5. Get Payment Details

**GET** `/api/supplier-payments/{payment_id}`

Get detailed information about a specific payment.

### 6. Update Payment

**PUT** `/api/supplier-payments/{payment_id}`

Update payment details (only draft payments can be updated).

### 7. Post Payment

**POST** `/api/supplier-payments/{payment_id}/post`

Post draft payment to ledger and change status to Posted.

**Request Body:**
```json
{
  "payment_id": 1,
  "post_to_ledger": true,
  "posted_by": "user123"
}
```

### 8. Reconcile Payment

**POST** `/api/supplier-payments/{payment_id}/reconcile`

Mark payment as reconciled with bank statement.

**Request Body:**
```json
{
  "payment_id": 1,
  "reconciled": true,
  "reconciled_by": "user123",
  "reconciliation_date": "2025-01-25"
}
```

### 9. Cancel Payment

**DELETE** `/api/supplier-payments/{payment_id}`

Cancel a draft payment.

## Reports & Analytics

### Payment Summary

**GET** `/api/supplier-payments/reports/summary`

Get payment summary with totals and statistics.

**Query Parameters:**
- `date_from` (optional): From date
- `date_to` (optional): To date

**Response:**
```json
{
  "total_payments": 50,
  "total_amount": 100000.00,
  "total_tds": 2000.00,
  "cash_payments": 10000.00,
  "bank_payments": 90000.00,
  "pending_reconciliation": 5,
  "draft_payments": 3,
  "posted_payments": 47
}
```

### Supplier Outstanding Report

**GET** `/api/supplier-payments/reports/supplier-outstanding`

Get supplier-wise outstanding amounts.

**Query Parameters:**
- `as_of_date` (optional): As of date

### Supplier Ledger

**GET** `/api/supplier-payments/supplier-ledger/{supplier_id}`

Get supplier ledger with running balance.

**Query Parameters:**
- `date_from` (optional): From date
- `date_to` (optional): To date

### TDS Summary

**GET** `/api/supplier-payments/tds/summary`

Get TDS summary by financial year and quarter.

**Query Parameters:**
- `financial_year` (optional): e.g., "2023-24"
- `quarter` (optional): e.g., "Q1"

## Payment Modes

The system supports the following payment modes:
- `Cash`
- `Bank Transfer`
- `Cheque`
- `Demand Draft`
- `Online Transfer`
- `UPI`
- `RTGS`
- `NEFT`
- `Credit Card`

## Payment Types

- `Advance` - Advance payment to supplier
- `Against Bill` - Payment against specific bills
- `On Account` - General payment on account

## TDS Sections

Supported TDS sections:
- `194C` - Payments to contractors
- `194J` - Professional fees
- `194I` - Rent payments
- `194H` - Commission/Brokerage
- `194A` - Interest payments
- `195` - Non-resident payments

## Status Flow

1. **Draft** - Payment created but not posted
2. **Posted** - Payment posted to ledger
3. **Cancelled** - Payment cancelled (only from Draft)

## Automatic Accounting Integration

When a payment is posted, the system automatically creates:

1. **Supplier Account** - Credit (reduces liability)
2. **Payment Account** - Debit (cash/bank account)
3. **TDS Account** - Credit (if TDS deducted)
4. **Deduction Accounts** - Credit (if other deductions)

## Error Handling

The API returns standard HTTP status codes:
- `200` - Success
- `201` - Created
- `400` - Bad Request (validation errors)
- `401` - Unauthorized
- `404` - Not Found
- `500` - Internal Server Error

## Example Usage Scenarios

### Scenario 1: Simple Bill Payment

1. Get outstanding bills: `GET /outstanding-bills/1`
2. Create payment: `POST /pay-against-bills`
3. Post payment: `POST /{payment_id}/post`
4. Reconcile: `POST /{payment_id}/reconcile`

### Scenario 2: Partial Bill Payment

1. Get outstanding bills
2. Select specific bills with partial amounts
3. Create payment with TDS deduction
4. Post and reconcile

### Scenario 3: Advance Payment

1. Create advance payment (no bills)
2. Later adjust against new bills
3. Track advance balance

## Database Tables Created

1. **supplier_payments** - Main payment entries
2. **supplier_payment_bills** - Links payments to bills
3. **supplier_ledger** - Running balance ledger
4. **tds_entries** - TDS tracking and certificates

## Required Account Codes

The migration creates these account codes:
- `CASH_IN_HAND` - Cash payments
- `BANK_ACCOUNT` - Bank transfers
- `UPI_ACCOUNT` - UPI payments  
- `CREDIT_CARD_ACCOUNT` - Credit card payments
- `TDS_PAYABLE` - TDS liability
- `OTHER_DEDUCTIONS` - Other deductions

## Security Considerations

- All endpoints require JWT authentication
- Payments can only be updated in Draft status
- Posted payments cannot be deleted
- Audit trail maintained for all changes
- Bank account validation for sensitive operations

## Performance Optimizations

- Database indexes on frequently queried fields
- Batch processing for bulk operations
- Optimized queries for reports
- Caching for reference data

## Testing

Use the API endpoints with Postman or curl:

```bash
# Get outstanding bills
curl -X GET "http://localhost:8000/api/supplier-payments/outstanding-bills/1" \
  -H "Authorization: Bearer your_token"

# Create payment  
curl -X POST "http://localhost:8000/api/supplier-payments/pay-against-bills" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_token" \
  -d '{...payment_data...}'
```

## Next Steps

1. Test all API endpoints
2. Configure TDS rates per tax regulations
3. Set up bank account mappings
4. Create custom reports as needed
5. Configure automated reconciliation processes

---

**Note:** This system integrates seamlessly with the existing Purchase and Accounting modules for complete financial workflow automation.
