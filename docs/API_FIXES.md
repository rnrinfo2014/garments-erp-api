# Corrected Purchase API Request

## Issues Fixed:
1. **purchase_type**: Changed from "Credit" to "CREDIT" (database expects uppercase)
2. **JSON format**: Removed trailing comma that was causing parse errors

## Corrected CURL Request:

```bash
curl -X 'POST' \
  'http://localhost:8000/api/purchases/' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer YOUR_TOKEN_HERE' \
  -H 'Content-Type: application/json' \
  -d '{
  "purchase_date": "2025-08-26",
  "supplier_id": 2,
  "supplier_invoice_number": "INV-2025-TEST-01",
  "supplier_invoice_date": "2025-08-26",
  "po_id": 9,
  "po_number": "PO-TEST-001",
  "purchase_type": "CREDIT",
  "tax_amount": 100.50,
  "discount_amount": 50.00,
  "transport_charges": 120.00,
  "other_charges": 30.00,
  "amount_paid": 0.00,
  "payment_mode": "CASH",
  "payment_reference": null,
  "transport_details": "Standard delivery",
  "remarks": "Converted from PO-TEST-001",
  "items": [
    {
      "material_id": "RM001",
      "size_id": "SIZ002",
      "supplier_material_name": "Premium Cotton Fabric",
      "description": "High quality cotton fabric for garments",
      "quantity": 10.000,
      "unit_id": "UNT001",
      "rate": 150.00,
      "po_item_id": 7,
      "quality_status": "Accepted",
      "rejected_qty": 0,
      "batch_number": "BATCH-PO-001",
      "expiry_date": "2026-08-25"
    }
  ],
  "created_by": "rnrinfo"
}'
```

## Valid Enum Values:

### PurchaseType:
- "CASH"
- "CREDIT" 
- "ADVANCE"

### PurchaseStatus:
- "DRAFT"
- "POSTED"
- "CANCELLED"

### PaymentMode:
- "CASH"
- "BANK_TRANSFER"
- "CHEQUE"
- "DEMAND_DRAFT"
- "ONLINE_TRANSFER"
- "UPI"
- "RTGS"
- "NEFT"
- "CREDIT_CARD"

### QualityStatus:
- "Accepted"
- "Rejected" 
- "Pending"

## Customer Update Issue Fix:

For the customer update issue, the corrected JSON should be:

```json
{
  "customer_name": "rnrinfo",
  "customer_type": "Registered",
  "gst_number": "33WZXGZ7295Q7Z7",
  "contact_person": "nagaraj",
  "phone": "9698879060",
  "email": "rnrinfo@gmail.com",
  "address": "dindigul",
  "city": "dindigul",
  "pincode": "624001",
  "state_id": 23,
  "agent_id": 4,
  "status": "Active"
}
```

**Key fix:** Removed the trailing comma after `"status": "Active"`
