# Purchase Order API Documentation for Frontend Development

## Base URL
```
http://localhost:8000/api
```

## Authentication
All endpoints require JWT Token Authentication:
```javascript
headers: {
  'Authorization': 'Bearer <your_jwt_token>',
  'Content-Type': 'application/json'
}
```

## Available Endpoints

### 1. Create Purchase Order
**POST** `/purchase-orders`

Creates a new purchase order with items.

**Request Body:**
```json
{
  "po_number": "PO2025001",
  "supplier_id": 1,
  "po_date": "2025-08-25",
  "due_date": "2025-09-10",
  "transport_details": "Standard shipping",
  "tax_amount": 180.00,
  "discount_amount": 50.00,
  "remarks": "Urgent order for production",
  "items": [
    {
      "material_id": "RM001",
      "supplier_material_name": "Premium Cotton Fabric",
      "description": "High quality cotton for shirts",
      "quantity": 100.00,
      "unit_id": "UNT001",
      "rate": 180.00
    },
    {
      "material_id": "RM004",
      "supplier_material_name": "White Thread",
      "description": "Sewing thread",
      "quantity": 50.00,
      "unit_id": "UNT006",
      "rate": 25.00
    }
  ]
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "po_number": "PO2025001",
  "supplier_id": 1,
  "po_date": "2025-08-25",
  "due_date": "2025-09-10",
  "status": "Draft",
  "transport_details": "Standard shipping",
  "sub_total": "19250.00",
  "tax_amount": "180.00",
  "discount_amount": "50.00",
  "total_amount": "19380.00",
  "remarks": "Urgent order for production",
  "created_by": "rnrinfo",
  "is_active": true,
  "created_at": "2025-08-25T12:30:00Z",
  "updated_at": "2025-08-25T12:30:00Z",
  "calculated_sub_total": "19250.00",
  "calculated_total": "19380.00",
  "supplier": {
    "id": 1,
    "supplier_name": "ABC Textiles Ltd",
    "supplier_type": "Registered",
    "contact_person": "John Doe",
    "phone": "9876543210",
    "email": "contact@abctextiles.com"
  },
  "items": [
    {
      "id": 1,
      "po_id": 1,
      "material_id": "RM001",
      "supplier_material_name": "Premium Cotton Fabric",
      "description": "High quality cotton for shirts",
      "quantity": "100.00",
      "unit_id": "UNT001",
      "rate": "180.00",
      "total_amount": "18000.00",
      "received_qty": "0.00",
      "pending_qty": "100.00",
      "item_status": "Pending",
      "created_at": "2025-08-25T12:30:00Z",
      "updated_at": "2025-08-25T12:30:00Z",
      "material": {
        "id": "RM001",
        "material_name": "Smart Plus Slub",
        "material_code": "SPS001",
        "description": "Premium slub cotton fabric"
      },
      "unit": {
        "id": "UNT001",
        "unit_name": "Meter",
        "unit_code": "MTR"
      }
    }
  ]
}
```

### 2. Get Purchase Orders (List with Pagination)
**GET** `/purchase-orders`

Get paginated list of purchase orders with optional filters.

**Query Parameters:**
- `skip`: Number of records to skip (default: 0)
- `limit`: Number of records to return (default: 100, max: 1000)
- `supplier_id`: Filter by supplier ID
- `status`: Filter by status ("Draft", "Pending", "Approved", "Received", "Cancelled")
- `po_date_from`: Filter from date (YYYY-MM-DD)
- `po_date_to`: Filter to date (YYYY-MM-DD)

**Example Request:**
```
GET /purchase-orders?skip=0&limit=10&status=Draft&supplier_id=1
```

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "po_number": "PO2025001",
    "supplier_id": 1,
    "supplier_name": "ABC Textiles Ltd",
    "po_date": "2025-08-25",
    "due_date": "2025-09-10",
    "status": "Draft",
    "total_amount": "19380.00",
    "items_count": 2,
    "created_at": "2025-08-25T12:30:00Z"
  }
]
```

### 3. Get Purchase Order by ID
**GET** `/purchase-orders/{po_id}`

Get detailed information about a specific purchase order.

**Response (200 OK):**
Same structure as Create Purchase Order response.

### 4. Update Purchase Order
**PUT** `/purchase-orders/{po_id}`

Update purchase order details (only for Draft and Pending orders).

**Request Body (Partial Update):**
```json
{
  "due_date": "2025-09-15",
  "transport_details": "Express shipping",
  "remarks": "Updated delivery requirements"
}
```

**Response (200 OK):**
Updated purchase order with same structure as Create response.

### 5. Update Purchase Order Status
**PUT** `/purchase-orders/{po_id}/status`

Update the status of a purchase order with optional remarks.

**Request Body:**
```json
{
  "status": "Approved",
  "remarks": "Approved by manager on 2025-08-25"
}
```

**Valid Status Values:**
- `"Draft"` - Initial state, can be edited
- `"Pending"` - Submitted for approval
- `"Approved"` - Approved and ready to send
- `"Received"` - Materials received
- `"Cancelled"` - Cancelled order

**Response (200 OK):**
Updated purchase order with new status.

### 6. Delete Purchase Order
**DELETE** `/purchase-orders/{po_id}`

Delete a purchase order (only Draft orders can be deleted).

**Response (200 OK):**
```json
{
  "message": "Purchase order PO2025001 deleted successfully"
}
```

### 7. Get Purchase Order Statistics
**GET** `/purchase-orders-stats`

Get statistics about purchase orders.

**Response (200 OK):**
```json
{
  "total_purchase_orders": 25,
  "total_value": "500000.00",
  "by_status": [
    {
      "status": "Draft",
      "count": 5,
      "total_value": "75000.00"
    },
    {
      "status": "Approved",
      "count": 10,
      "total_value": "200000.00"
    },
    {
      "status": "Received",
      "count": 8,
      "total_value": "175000.00"
    },
    {
      "status": "Cancelled",
      "count": 2,
      "total_value": "50000.00"
    }
  ]
}
```

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Purchase order number PO2025001 already exists"
}
```

### 401 Unauthorized
```json
{
  "detail": "Not authenticated"
}
```

### 404 Not Found
```json
{
  "detail": "Purchase order with ID 999 not found"
}
```

### 422 Validation Error
```json
{
  "detail": [
    {
      "loc": ["body", "items", 0, "quantity"],
      "msg": "ensure this value is greater than 0",
      "type": "value_error.number.not_gt"
    }
  ]
}
```

## Frontend Integration Examples

### React/JavaScript Example

```javascript
// Create Purchase Order
const createPurchaseOrder = async (poData) => {
  try {
    const response = await fetch('http://localhost:8000/api/purchase-orders', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(poData)
    });
    
    if (!response.ok) {
      throw new Error('Failed to create purchase order');
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error creating purchase order:', error);
    throw error;
  }
};

// Get Purchase Orders with Filters
const getPurchaseOrders = async (filters = {}) => {
  const params = new URLSearchParams();
  
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== null && value !== undefined && value !== '') {
      params.append(key, value);
    }
  });
  
  try {
    const response = await fetch(`http://localhost:8000/api/purchase-orders?${params}`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    });
    
    if (!response.ok) {
      throw new Error('Failed to fetch purchase orders');
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error fetching purchase orders:', error);
    throw error;
  }
};

// Update Purchase Order Status
const updatePurchaseOrderStatus = async (poId, status, remarks) => {
  try {
    const response = await fetch(`http://localhost:8000/api/purchase-orders/${poId}/status`, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ status, remarks })
    });
    
    if (!response.ok) {
      throw new Error('Failed to update purchase order status');
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error updating purchase order status:', error);
    throw error;
  }
};
```

### Vue.js Example

```javascript
// Vue component methods
export default {
  data() {
    return {
      purchaseOrders: [],
      loading: false,
      filters: {
        status: '',
        supplier_id: null,
        po_date_from: '',
        po_date_to: ''
      }
    }
  },
  
  methods: {
    async fetchPurchaseOrders() {
      this.loading = true;
      try {
        const params = new URLSearchParams();
        
        Object.entries(this.filters).forEach(([key, value]) => {
          if (value) params.append(key, value);
        });
        
        const response = await this.$http.get(`/purchase-orders?${params}`);
        this.purchaseOrders = response.data;
      } catch (error) {
        this.$toast.error('Failed to load purchase orders');
        console.error(error);
      } finally {
        this.loading = false;
      }
    },
    
    async approvePurchaseOrder(poId) {
      try {
        await this.$http.put(`/purchase-orders/${poId}/status`, {
          status: 'Approved',
          remarks: 'Approved via web interface'
        });
        
        this.$toast.success('Purchase order approved successfully');
        this.fetchPurchaseOrders(); // Refresh list
      } catch (error) {
        this.$toast.error('Failed to approve purchase order');
        console.error(error);
      }
    }
  },
  
  mounted() {
    this.fetchPurchaseOrders();
  }
}
```

## Data Validation Rules

### Purchase Order
- `po_number`: Required, max 50 characters, must be unique
- `supplier_id`: Required, must exist in suppliers table
- `po_date`: Required, date format
- `due_date`: Optional, date format
- `tax_amount`: Optional, decimal ≥ 0, default 0.00
- `discount_amount`: Optional, decimal ≥ 0, default 0.00
- `items`: Required, minimum 1 item

### Purchase Order Items
- `material_id`: Required, must exist in raw_material_master table
- `unit_id`: Required, must exist in unit_master table
- `quantity`: Required, decimal > 0
- `rate`: Required, decimal ≥ 0
- `supplier_material_name`: Optional, max 200 characters

## Business Logic Notes

1. **Status Workflow**: Draft → Pending → Approved → Received
2. **Calculations**: 
   - Item Total = Quantity × Rate
   - Sub Total = Sum of all item totals
   - Total Amount = Sub Total + Tax - Discount
3. **Edit Restrictions**: Only Draft and Pending orders can be updated
4. **Delete Restrictions**: Only Draft orders can be deleted
5. **Item Status**: Automatically managed based on received quantities
6. **Pending Quantity**: Automatically calculated as Quantity - Received Quantity

This documentation provides all the necessary information for frontend developers to integrate with the Purchase Order API effectively.
