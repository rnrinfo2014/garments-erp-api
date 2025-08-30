# Raw Material Purchase API Endpoints

## 🎯 Available API Endpoints for Raw Material Purchases

Based on your ERP system, here are all the available API endpoints related to raw material purchases:

### 📋 **Raw Material Master Management**
**Base URL:** `/api/raw-material-master`

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/raw-material-master/` | Get all raw materials with filtering |
| `POST` | `/api/raw-material-master/` | Create new raw material |
| `GET` | `/api/raw-material-master/{id}` | Get specific raw material details |
| `PUT` | `/api/raw-material-master/{id}` | Update raw material |
| `DELETE` | `/api/raw-material-master/{id}` | Delete raw material |

**Query Parameters for GET:**
- `skip` - Pagination offset
- `limit` - Number of records to return
- `category_id` - Filter by category
- `is_active` - Filter by active status

---

### 🛒 **Purchase Orders (for Raw Materials)**
**Base URL:** `/api/purchase-orders`

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/purchase-orders/` | Create new purchase order |
| `GET` | `/api/purchase-orders/` | Get all purchase orders |
| `GET` | `/api/purchase-orders/{po_id}` | Get specific PO details |
| `PUT` | `/api/purchase-orders/{po_id}` | Update purchase order |
| `PUT` | `/api/purchase-orders/{po_id}/status` | Update PO status |
| `DELETE` | `/api/purchase-orders/{po_id}` | Delete purchase order |
| `GET` | `/api/purchase-orders/stats` | Get purchase order statistics |

**Query Parameters for GET:**
- `skip` - Pagination offset
- `limit` - Number of records
- `supplier_id` - Filter by supplier
- `status` - Filter by status
- `from_date` - Date range start
- `to_date` - Date range end

---

### 📦 **Purchase Entries (Raw Material Receipts)**
**Base URL:** `/api/purchases`

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/purchases/` | Create new purchase entry |
| `GET` | `/api/purchases/` | Get all purchases |
| `GET` | `/api/purchases/{purchase_id}` | Get specific purchase details |
| `PUT` | `/api/purchases/{purchase_id}` | Update purchase |
| `DELETE` | `/api/purchases/{purchase_id}` | Delete purchase |
| `POST` | `/api/purchases/{purchase_id}/post` | Post purchase to accounts |
| `POST` | `/api/purchases/from-po` | Create purchase from PO |
| `GET` | `/api/purchases/reports/summary` | Get purchase summary report |

**Query Parameters for GET:**
- `skip` - Pagination offset
- `limit` - Number of records
- `supplier_id` - Filter by supplier
- `status` - Filter by status
- `from_date` - Date range start
- `to_date` - Date range end

---

### 🔄 **Purchase Returns**
**Base URL:** `/api/purchase-returns`

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/purchase-returns/` | Create purchase return |
| `GET` | `/api/purchase-returns/` | Get all returns |
| `GET` | `/api/purchase-returns/{return_id}` | Get specific return details |
| `PUT` | `/api/purchase-returns/{return_id}` | Update return |
| `DELETE` | `/api/purchase-returns/{return_id}` | Delete return |

---

### 💳 **Supplier Payments**
**Base URL:** `/api/supplier-payments`

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/supplier-payments/` | Create supplier payment |
| `GET` | `/api/supplier-payments/` | Get all payments |
| `GET` | `/api/supplier-payments/{payment_id}` | Get payment details |
| `PUT` | `/api/supplier-payments/{payment_id}` | Update payment |
| `DELETE` | `/api/supplier-payments/{payment_id}` | Delete payment |

---

### 📊 **Stock Ledger (Raw Material Stock)**
**Base URL:** `/api/stock-ledger`

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/stock-ledger/` | Get stock movements |
| `POST` | `/api/stock-ledger/` | Create stock entry |

**Query Parameters:**
- `raw_material_id` - Filter by raw material
- `movement_type` - Filter by movement type
- `from_date` - Date range start
- `to_date` - Date range end

---

## 🔗 **Related Master Data Endpoints**

### Suppliers
- `GET /api/suppliers/` - Get all suppliers
- `POST /api/suppliers/` - Create supplier

### Categories
- `GET /api/category-master/` - Get material categories
- `POST /api/category-master/` - Create category

### Units
- `GET /api/unit-master/` - Get units of measurement
- `POST /api/unit-master/` - Create unit

### Sizes
- `GET /api/size-master/` - Get sizes
- `POST /api/size-master/` - Create size

---

## 🚀 **Complete Raw Material Purchase Workflow**

1. **Setup Masters:**
   - Create/manage suppliers via `/api/suppliers/`
   - Create/manage raw materials via `/api/raw-material-master/`

2. **Purchase Process:**
   - Create purchase order via `POST /api/purchase-orders/`
   - Create purchase entry via `POST /api/purchases/` or `POST /api/purchases/from-po`
   - Post to accounts via `POST /api/purchases/{id}/post`

3. **Returns (if needed):**
   - Create return via `POST /api/purchase-returns/`

4. **Payments:**
   - Make payments via `POST /api/supplier-payments/`

5. **Tracking:**
   - Monitor stock via `/api/stock-ledger/`
   - View reports via `/api/purchases/reports/summary`

---

## 📝 **Authentication**

All endpoints require authentication. Include the Bearer token in the Authorization header:
```
Authorization: Bearer <your_token>
```

## 🔍 **Testing**

You can test all endpoints via:
- **Swagger UI:** `http://127.0.0.1:8000/docs`
- **ReDoc:** `http://127.0.0.1:8000/redoc`
