# Stock Ledger API Documentation

## Overview
The Stock Ledger API provides comprehensive inventory management functionality for tracking raw material movements in your Garments ERP system.

## Database Table Structure
```sql
CREATE TABLE StockLedger (
    LedgerID INT PRIMARY KEY IDENTITY(1,1),
    RawMaterialID VARCHAR(50) NOT NULL,           -- link to RawMaterialMaster
    SizeID VARCHAR(50) NOT NULL,                  -- link to SizeMaster  
    SupplierID INT NULL,                          -- link to Suppliers (NULL for Opening Stock)
    TransactionDate DATE NOT NULL,               -- stock entry date
    TransactionType VARCHAR(50) NOT NULL,        -- OpeningStock/Purchase/PurchaseReturn/Issue/Adjustment
    ReferenceTable VARCHAR(100) NULL,            -- which table this entry comes from
    ReferenceID INT NULL,                        -- PK from that table
    QtyIn DECIMAL(18,2) DEFAULT 0,               -- inward quantity
    QtyOut DECIMAL(18,2) DEFAULT 0,              -- outward quantity
    Rate DECIMAL(18,2) DEFAULT 0,                -- rate for this transaction
    Amount AS ((QtyIn - QtyOut) * Rate),         -- computed column
    CreatedBy VARCHAR(50) NULL,
    CreatedDate DATETIME DEFAULT GETDATE()
);
```

## Authentication
All endpoints use **HTTP Basic Authentication**. Send username/password directly in the Authorization header:
```
Authorization: Basic <base64(username:password)>
```

## API Endpoints

### 1. Create Stock Ledger Entry
**POST** `/api/stock-ledger`

Creates a new stock ledger entry for tracking inventory movements.

**Request Body:**
```json
{
    "raw_material_id": "RM001",
    "size_id": "SIZE001", 
    "supplier_id": null,                    // null for opening stock
    "transaction_date": "2025-08-24",
    "transaction_type": "OpeningStock",     // OpeningStock, Purchase, PurchaseReturn, Issue, Adjustment
    "reference_table": null,                // optional: source table name
    "reference_id": null,                   // optional: source record ID
    "qty_in": "100.00",
    "qty_out": "0.00",
    "rate": "50.00"
}
```

**Response:**
```json
{
    "ledger_id": 1,
    "raw_material_id": "RM001",
    "size_id": "SIZE001",
    "supplier_id": null,
    "transaction_date": "2025-08-24",
    "transaction_type": "OpeningStock",
    "reference_table": null,
    "reference_id": null,
    "qty_in": "100.00",
    "qty_out": "0.00",
    "rate": "50.00",
    "amount": "5000.00",
    "net_quantity": "100.00",
    "created_by": "admin",
    "created_date": "2025-08-24T10:30:00"
}
```

### 2. Get Stock Ledger Entries
**GET** `/api/stock-ledger`

Retrieves stock ledger entries with optional filtering.

**Query Parameters:**
- `skip` (int): Records to skip (pagination)
- `limit` (int): Max records to return (1-1000)
- `raw_material_id` (string): Filter by material ID
- `size_id` (string): Filter by size ID
- `supplier_id` (int): Filter by supplier ID
- `transaction_type` (string): Filter by transaction type
- `from_date` (date): Filter from date
- `to_date` (date): Filter to date

**Example:**
```
GET /api/stock-ledger?raw_material_id=RM001&limit=50
```

### 3. Get Stock Ledger Entry by ID
**GET** `/api/stock-ledger/{ledger_id}`

Retrieves a specific stock ledger entry with related data.

### 4. Update Stock Ledger Entry
**PUT** `/api/stock-ledger/{ledger_id}`

Updates an existing stock ledger entry (Admin only).

### 5. Delete Stock Ledger Entry  
**DELETE** `/api/stock-ledger/{ledger_id}`

Deletes a stock ledger entry (Admin only).

### 6. Get Stock Summary
**GET** `/api/stock-summary`

Returns current stock summary grouped by raw material and size.

**Query Parameters:**
- `raw_material_id` (optional): Filter by specific material
- `size_id` (optional): Filter by specific size

**Response:**
```json
[
    {
        "raw_material_id": "RM001",
        "size_id": "SIZE001",
        "raw_material_name": null,
        "size_name": null,
        "total_qty_in": "150.00",
        "total_qty_out": "25.00", 
        "current_stock": "125.00",
        "last_transaction_date": "2025-08-24",
        "avg_rate": "52.50"
    }
]
```

### 7. Get Stock Movements
**GET** `/api/stock-movement`

Returns detailed stock movements for a specific material and size.

**Query Parameters:**
- `raw_material_id` (required): Material ID
- `size_id` (required): Size ID
- `from_date` (optional): Filter from date
- `to_date` (optional): Filter to date

### 8. Get Current Stock Balance
**GET** `/api/current-stock/{raw_material_id}/{size_id}`

Returns current stock balance for specific material and size.

**Response:**
```json
{
    "raw_material_id": "RM001",
    "size_id": "SIZE001", 
    "total_qty_in": "150.00",
    "total_qty_out": "25.00",
    "current_stock": "125.00"
}
```

## Transaction Types

1. **OpeningStock** - Initial stock entry
2. **Purchase** - Stock received from suppliers
3. **PurchaseReturn** - Stock returned to suppliers
4. **Issue** - Stock issued for production/consumption
5. **Adjustment** - Manual stock adjustments

## Usage Examples

### Example 1: Record Opening Stock
```bash
curl -X POST "http://localhost:8001/api/stock-ledger" \
  -H "Authorization: Basic YWRtaW46YWRtaW4=" \
  -H "Content-Type: application/json" \
  -d '{
    "raw_material_id": "RM001",
    "size_id": "SIZE001",
    "supplier_id": null,
    "transaction_date": "2025-08-24",
    "transaction_type": "OpeningStock",
    "qty_in": "100.00",
    "qty_out": "0.00",
    "rate": "50.00"
  }'
```

### Example 2: Record Purchase
```bash
curl -X POST "http://localhost:8001/api/stock-ledger" \
  -H "Authorization: Basic YWRtaW46YWRtaW4=" \
  -H "Content-Type: application/json" \
  -d '{
    "raw_material_id": "RM001",
    "size_id": "SIZE001", 
    "supplier_id": 1,
    "transaction_date": "2025-08-24",
    "transaction_type": "Purchase",
    "reference_table": "purchase_orders",
    "reference_id": 1001,
    "qty_in": "50.00",
    "qty_out": "0.00",
    "rate": "55.00"
  }'
```

### Example 3: Issue Material
```bash
curl -X POST "http://localhost:8001/api/stock-ledger" \
  -H "Authorization: Basic YWRtaW46YWRtaW4=" \
  -H "Content-Type: application/json" \
  -d '{
    "raw_material_id": "RM001",
    "size_id": "SIZE001",
    "supplier_id": null,
    "transaction_date": "2025-08-24",
    "transaction_type": "Issue",
    "reference_table": "production_orders",
    "reference_id": 2001,
    "qty_in": "0.00",
    "qty_out": "25.00",
    "rate": "52.50"
  }'
```

### Example 4: Get Stock Summary
```bash
curl -X GET "http://localhost:8001/api/stock-summary?raw_material_id=RM001" \
  -H "Authorization: Basic YWRtaW46YWRtaW4="
```

### Example 5: Check Current Stock
```bash
curl -X GET "http://localhost:8001/api/current-stock/RM001/SIZE001" \
  -H "Authorization: Basic YWRtaW46YWRtaW4="
```

## Testing

Use the provided test script:
```bash
python test_stock_ledger.py
```

## API Documentation

Visit `http://localhost:8001/docs` to access the interactive Swagger documentation.

## Business Rules

1. Either `qty_in` or `qty_out` must be greater than zero (not both zero)
2. Opening stock entries typically have `supplier_id = null`
3. Purchase entries should have a valid `supplier_id`
4. Issue entries typically have `supplier_id = null`
5. The `amount` is automatically calculated as `(qty_in - qty_out) * rate`
6. Admin permissions required for update/delete operations
7. All users can view stock information with proper authentication

## Integration Notes

- Ensure raw materials exist in `raw_material_master` table
- Ensure sizes exist in `size_master` table  
- Ensure suppliers exist in `suppliers` table for purchase transactions
- Use `reference_table` and `reference_id` to link stock movements to source documents
- Stock balances are calculated in real-time from ledger entries
