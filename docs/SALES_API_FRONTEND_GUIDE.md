# Sales Bill API - Frontend Development Guide

## 🎯 Overview

This comprehensive guide provides frontend developers with everything needed to integrate with the Sales Billing API. The API follows RESTful principles and includes complete CRUD operations, status management, item management, and reporting features.

**Base URL**: `http://localhost:8000/api/sales`  
**API Documentation**: `http://localhost:8000/docs`

---

## 🔐 Authentication

All endpoints require JWT authentication. Include the token in the Authorization header:

```http
Authorization: Bearer YOUR_JWT_TOKEN
```

---

## 📊 Core Endpoints

### 1. Sales CRUD Operations

#### **Create Sales** 
`POST /api/sales/`

Creates a new sales transaction with automatic calculations.

**Request Body:**
```json
{
  "bill_book_id": 1,
  "customer_id": 2,
  "agent_id": 3,
  "bill_date": "2025-08-30",
  "due_date": "2025-09-15",
  "reference_number": "REF-001",
  "notes": "Customer notes",
  "items": [
    {
      "product_variant_id": 123,
      "quantity": 5,
      "rate": 100.00,
      "discount_percentage": 10.0,
      "tax_percentage": 18.0
    }
  ]
}
```

**Response:**
```json
{
  "id": 1,
  "bill_number": "B2B001",
  "bill_book_id": 1,
  "customer_id": 2,
  "agent_id": 3,
  "bill_date": "2025-08-30",
  "due_date": "2025-09-15",
  "reference_number": "REF-001",
  "notes": "Customer notes",
  "status": "DRAFT",
  "subtotal": 450.00,
  "total_discount": 50.00,
  "total_tax": 72.00,
  "total_amount": 472.00,
  "created_at": "2025-08-30T10:30:00Z",
  "updated_at": "2025-08-30T10:30:00Z",
  "items": [
    {
      "id": 1,
      "product_variant_id": 123,
      "product_name": "Smart Plus - Variant 123",
      "quantity": 5,
      "rate": 100.00,
      "amount": 500.00,
      "discount_percentage": 10.0,
      "discount_amount": 50.00,
      "taxable_amount": 450.00,
      "tax_percentage": 18.0,
      "tax_amount": 72.00,
      "total_amount": 472.00
    }
  ],
  "customer": {
    "id": 2,
    "customer_name": "John Doe",
    "mobile": "9876543210"
  },
  "agent": {
    "id": 3,
    "agent_name": "Sales Agent"
  },
  "bill_book": {
    "id": 1,
    "book_name": "B2B Sales",
    "book_code": "B2B"
  }
}
```

#### **List Sales**
`GET /api/sales/`

Retrieve sales with pagination, filtering, and sorting.

**Query Parameters:**
- `page`: Page number (default: 1)
- `size`: Items per page (default: 20, max: 100)
- `status`: Filter by status (DRAFT, CONFIRMED, DISPATCHED, DELIVERED, CANCELLED, RETURNED)
- `customer_id`: Filter by customer
- `agent_id`: Filter by agent
- `bill_book_id`: Filter by bill book
- `start_date`: Filter from date (YYYY-MM-DD)
- `end_date`: Filter to date (YYYY-MM-DD)
- `search`: Search in bill number, customer name, reference number
- `sort_by`: Sort field (bill_number, bill_date, total_amount, status)
- `sort_order`: asc or desc

**Example Request:**
```http
GET /api/sales/?page=1&size=10&status=CONFIRMED&sort_by=bill_date&sort_order=desc
```

**Response:**
```json
{
  "items": [
    {
      "id": 1,
      "bill_number": "B2B001",
      "bill_date": "2025-08-30",
      "customer_name": "John Doe",
      "agent_name": "Sales Agent",
      "status": "CONFIRMED",
      "total_amount": 472.00,
      "items_count": 1
    }
  ],
  "total": 1,
  "page": 1,
  "size": 10,
  "pages": 1
}
```

#### **Get Sales by ID**
`GET /api/sales/{sales_id}`

**Response:** Same as Create Sales response

#### **Update Sales**
`PUT /api/sales/{sales_id}`

Update sales transaction (only allowed for DRAFT status).

**Request Body:** Same as Create Sales

#### **Delete Sales**
`DELETE /api/sales/{sales_id}`

Delete sales transaction (only allowed for DRAFT status).

---

### 2. Status Management

#### **Update Sales Status**
`PATCH /api/sales/{sales_id}/status`

**Request Body:**
```json
{
  "status": "CONFIRMED",
  "notes": "Order confirmed by customer"
}
```

**Status Flow:**
```
DRAFT → CONFIRMED → DISPATCHED → DELIVERED
  ↓         ↓           ↓
CANCELLED   CANCELLED   RETURNED
```

#### **Bulk Status Update**
`POST /api/sales/bulk-status-update`

**Request Body:**
```json
{
  "sales_ids": [1, 2, 3],
  "status": "CONFIRMED",
  "notes": "Bulk confirmation"
}
```

---

### 3. Sales Items Management

#### **Add Sales Item**
`POST /api/sales/{sales_id}/items`

**Request Body:**
```json
{
  "product_variant_id": 124,
  "quantity": 3,
  "rate": 150.00,
  "discount_percentage": 5.0,
  "tax_percentage": 18.0
}
```

#### **Update Sales Item**
`PUT /api/sales/{sales_id}/items/{item_id}`

#### **Delete Sales Item**
`DELETE /api/sales/{sales_id}/items/{item_id}`

#### **Get Sales Items**
`GET /api/sales/{sales_id}/items`

---

### 4. Analytics & Reports

#### **Sales Summary**
`GET /api/sales/summary`

**Query Parameters:**
- `start_date`, `end_date`: Date range
- `customer_id`, `agent_id`, `bill_book_id`: Filters

**Response:**
```json
{
  "total_sales": 15,
  "total_amount": 25000.00,
  "total_tax": 4500.00,
  "total_discount": 2500.00,
  "average_order_value": 1666.67,
  "status_breakdown": {
    "DRAFT": 3,
    "CONFIRMED": 5,
    "DISPATCHED": 4,
    "DELIVERED": 2,
    "CANCELLED": 1
  },
  "top_customers": [
    {
      "customer_id": 2,
      "customer_name": "John Doe",
      "total_amount": 5000.00,
      "order_count": 3
    }
  ],
  "top_products": [
    {
      "product_variant_id": 123,
      "product_name": "Smart Plus - Variant 123",
      "quantity_sold": 25,
      "total_amount": 3000.00
    }
  ]
}
```

#### **Daily Sales Report**
`GET /api/sales/reports/daily`

#### **Monthly Sales Report**
`GET /api/sales/reports/monthly`

#### **Customer Sales Report**
`GET /api/sales/reports/customer/{customer_id}`

#### **Agent Performance Report**
`GET /api/sales/reports/agent/{agent_id}`

---

### 5. Utility Endpoints

#### **Sales Statistics**
`GET /api/sales/stats`

Quick statistics for dashboard.

#### **Recent Sales**
`GET /api/sales/recent`

Last 10 sales transactions.

#### **Pending Deliveries**
`GET /api/sales/pending-deliveries`

Sales with DISPATCHED status.

#### **Overdue Sales**
`GET /api/sales/overdue`

Sales past due date.

---

## 📝 Data Models

### Sales Status Enum
```typescript
enum SalesStatus {
  DRAFT = "DRAFT",
  CONFIRMED = "CONFIRMED", 
  DISPATCHED = "DISPATCHED",
  DELIVERED = "DELIVERED",
  CANCELLED = "CANCELLED",
  RETURNED = "RETURNED"
}
```

### Sales Model
```typescript
interface Sales {
  id: number;
  bill_number: string;
  bill_book_id: number;
  customer_id: number;
  agent_id?: number;
  bill_date: string; // YYYY-MM-DD
  due_date?: string; // YYYY-MM-DD
  reference_number?: string;
  notes?: string;
  status: SalesStatus;
  subtotal: number;
  total_discount: number;
  total_tax: number;
  total_amount: number;
  created_at: string; // ISO datetime
  updated_at: string; // ISO datetime
  items: SalesItem[];
  customer: Customer;
  agent?: Agent;
  bill_book: BillBook;
  
  // Computed properties
  is_editable: boolean;
  is_deletable: boolean;
  can_confirm: boolean;
  can_dispatch: boolean;
  can_deliver: boolean;
  can_cancel: boolean;
  days_since_created: number;
  is_overdue: boolean;
}
```

### Sales Item Model
```typescript
interface SalesItem {
  id: number;
  sales_id: number;
  product_variant_id: number;
  product_name: string;
  quantity: number;
  rate: number;
  amount: number;
  discount_percentage: number;
  discount_amount: number;
  taxable_amount: number;
  tax_percentage: number;
  tax_amount: number;
  total_amount: number;
  
  // Related data
  product_variant: ProductVariant;
}
```

---

## 🚀 Frontend Integration Examples

### React/TypeScript Example

```typescript
// services/salesApi.ts
import axios from 'axios';

const API_BASE = 'http://localhost:8000/api';

export class SalesAPI {
  private getHeaders() {
    return {
      'Authorization': `Bearer ${localStorage.getItem('token')}`,
      'Content-Type': 'application/json'
    };
  }

  // Create sales
  async createSales(salesData: SalesCreate): Promise<SalesResponse> {
    const response = await axios.post(
      `${API_BASE}/sales/`, 
      salesData, 
      { headers: this.getHeaders() }
    );
    return response.data;
  }

  // List sales with filters
  async listSales(params: SalesListParams): Promise<PaginatedSalesResponse> {
    const response = await axios.get(`${API_BASE}/sales/`, {
      headers: this.getHeaders(),
      params
    });
    return response.data;
  }

  // Update status
  async updateStatus(salesId: number, status: SalesStatus, notes?: string) {
    const response = await axios.patch(
      `${API_BASE}/sales/${salesId}/status`,
      { status, notes },
      { headers: this.getHeaders() }
    );
    return response.data;
  }

  // Get summary
  async getSummary(filters?: SummaryFilters): Promise<SalesSummary> {
    const response = await axios.get(`${API_BASE}/sales/summary`, {
      headers: this.getHeaders(),
      params: filters
    });
    return response.data;
  }
}
```

### Vue.js Example

```javascript
// composables/useSales.js
import { ref, computed } from 'vue';
import { SalesAPI } from '@/services/salesApi';

export function useSales() {
  const sales = ref([]);
  const loading = ref(false);
  const pagination = ref({ page: 1, size: 20, total: 0 });
  
  const salesApi = new SalesAPI();

  const loadSales = async (filters = {}) => {
    loading.value = true;
    try {
      const response = await salesApi.listSales({
        ...filters,
        page: pagination.value.page,
        size: pagination.value.size
      });
      
      sales.value = response.items;
      pagination.value.total = response.total;
    } catch (error) {
      console.error('Failed to load sales:', error);
    } finally {
      loading.value = false;
    }
  };

  const createSales = async (salesData) => {
    try {
      const newSales = await salesApi.createSales(salesData);
      sales.value.unshift(newSales);
      return newSales;
    } catch (error) {
      throw error;
    }
  };

  const updateStatus = async (salesId, status, notes) => {
    try {
      const updated = await salesApi.updateStatus(salesId, status, notes);
      const index = sales.value.findIndex(s => s.id === salesId);
      if (index !== -1) {
        sales.value[index] = updated;
      }
      return updated;
    } catch (error) {
      throw error;
    }
  };

  return {
    sales: readonly(sales),
    loading: readonly(loading),
    pagination,
    loadSales,
    createSales,
    updateStatus
  };
}
```

---

## 🎨 UI Components Suggestions

### 1. Sales List Component
- Data table with pagination
- Status badges with colors
- Search and filter controls
- Bulk actions (status update, export)
- Sorting capabilities

### 2. Sales Form Component
- Customer selection with search
- Product variant selection with autocomplete
- Dynamic items management (add/remove rows)
- Real-time calculations
- Validation with error messages

### 3. Sales Details Component
- Read-only view of sales information
- Status timeline/workflow
- Print/export options
- Edit button (if editable)

### 4. Status Management Component
- Status workflow visualization
- Status update form with notes
- History of status changes
- Bulk status update

### 5. Dashboard Widgets
- Sales summary cards
- Charts (daily/monthly trends)
- Top customers/products
- Pending deliveries alert

---

## 🚨 Error Handling

### Common HTTP Status Codes

| Code | Meaning | Action |
|------|---------|---------|
| 200 | Success | Continue |
| 201 | Created | Resource created successfully |
| 400 | Bad Request | Check request data |
| 401 | Unauthorized | Refresh token or login |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource doesn't exist |
| 422 | Validation Error | Fix validation errors |
| 500 | Server Error | Contact support |

### Error Response Format
```json
{
  "detail": "Error message",
  "type": "validation_error",
  "errors": [
    {
      "field": "items.0.quantity",
      "message": "Quantity must be greater than 0"
    }
  ]
}
```

### Frontend Error Handling Example
```typescript
try {
  const sales = await salesApi.createSales(salesData);
} catch (error) {
  if (error.response?.status === 422) {
    // Handle validation errors
    const errors = error.response.data.errors;
    errors.forEach(err => {
      setFieldError(err.field, err.message);
    });
  } else if (error.response?.status === 401) {
    // Handle authentication error
    redirectToLogin();
  } else {
    // Handle other errors
    showErrorMessage('Failed to create sales');
  }
}
```

---

## 📱 Mobile Considerations

### Responsive Design
- Use responsive tables or cards for sales list
- Implement mobile-friendly forms
- Consider touch-friendly buttons and inputs
- Optimize for smaller screens

### Offline Support
- Cache frequently accessed data
- Queue actions when offline
- Sync when connection restored
- Show offline status indicator

---

## 🔧 Testing

### Test Data
Use the sample data creation script:
```bash
python scripts/database/create_sample_sales_data.py
```

### API Testing Tools
- **Swagger UI**: `http://localhost:8000/docs`
- **Postman**: Import OpenAPI spec from `/openapi.json`
- **curl**: Command line testing

### Example Test Cases
```bash
# Create sales
curl -X POST "http://localhost:8000/api/sales/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"bill_book_id":1,"customer_id":2,"items":[{"product_variant_id":123,"quantity":5,"rate":100}]}'

# List sales
curl -X GET "http://localhost:8000/api/sales/?page=1&size=10" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Update status
curl -X PATCH "http://localhost:8000/api/sales/1/status" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status":"CONFIRMED"}'
```

---

## 📈 Performance Tips

### Frontend Optimization
- Implement virtual scrolling for large lists
- Use pagination instead of loading all data
- Cache API responses where appropriate
- Debounce search inputs
- Use lazy loading for details

### API Usage Best Practices
- Use appropriate page sizes (10-50 items)
- Implement proper error handling and retry logic
- Use filters to reduce data transfer
- Cache reference data (customers, products)
- Implement optimistic updates for better UX

---

## 🔄 Real-time Updates

### WebSocket Integration (Future Enhancement)
Consider implementing WebSocket connections for:
- Real-time status updates
- Live sales notifications
- Collaborative editing alerts
- System-wide announcements

---

## 📋 Checklist for Frontend Developers

### Initial Setup
- [ ] Set up API client with authentication
- [ ] Configure base URL and endpoints
- [ ] Implement error handling middleware
- [ ] Set up TypeScript interfaces/types

### Core Features
- [ ] Sales list with pagination and filters
- [ ] Sales creation form with validation
- [ ] Sales details view
- [ ] Status management workflow
- [ ] Items management (add/edit/delete)

### Advanced Features
- [ ] Search and autocomplete
- [ ] Bulk operations
- [ ] Export functionality
- [ ] Print views
- [ ] Dashboard analytics

### Testing
- [ ] Unit tests for API services
- [ ] Integration tests for components
- [ ] E2E tests for critical workflows
- [ ] Performance testing with large datasets

### Production Ready
- [ ] Error boundaries
- [ ] Loading states
- [ ] Empty states
- [ ] Mobile responsive design
- [ ] Accessibility compliance

---

## 🆘 Support

### Resources
- **API Documentation**: `http://localhost:8000/docs`
- **Source Code**: Check the `routes/sales.py` file
- **Sample Data**: Use `create_sample_sales_data.py`

### Common Issues
1. **Double "sales" in URL**: Fixed - router prefix removed
2. **Authentication errors**: Ensure JWT token is valid
3. **Validation errors**: Check required fields and data types
4. **Performance issues**: Use pagination and filters

### Contact
For technical questions or issues, refer to the API documentation or check the backend logs for detailed error information.

---

*This documentation is generated for the Sales Billing API v1.0. Last updated: August 30, 2025*
