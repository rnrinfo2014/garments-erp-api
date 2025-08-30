# Sales Bill System API - Frontend Development Guide

## 🎯 Overview

This comprehensive guide provides everything frontend developers need to integrate with the Sales Bill System API. The system manages complete sales workflows from draft creation to delivery with tax calculations, discounts, and business logic.

## 🔗 Base Configuration

### API Base URL
```javascript
const API_BASE_URL = 'http://localhost:8000/api'
```

### Authentication
All requests require JWT token in Authorization header:
```javascript
const headers = {
  'Authorization': `Bearer ${token}`,
  'Content-Type': 'application/json'
}
```

## 📊 Core Endpoints

### 1. Sales Management

#### List Sales (with filtering and pagination)
```javascript
GET /sales

// Query Parameters
const params = {
  page: 1,              // Page number (default: 1)
  size: 20,             // Items per page (default: 20)
  status: 'CONFIRMED',  // Filter by status: DRAFT, CONFIRMED, DISPATCHED, DELIVERED
  customer_id: 123,     // Filter by customer
  agent_id: 456,        // Filter by agent
  start_date: '2024-01-01',  // Filter from date (YYYY-MM-DD)
  end_date: '2024-12-31',    // Filter to date (YYYY-MM-DD)
  search: 'bill001'     // Search in bill number or customer name
}

// Response
{
  "items": [
    {
      "id": 1,
      "bill_number": "B2B001",
      "status": "CONFIRMED",
      "sales_date": "2024-01-15",
      "due_date": "2024-02-15",
      "total_amount": 1611.14,
      "tax_amount": 122.14,
      "discount_amount": 50.00,
      "customer": {
        "id": 1,
        "customer_name": "ABC Company",
        "customer_code": "CUST001"
      },
      "agent": {
        "id": 1,
        "agent_name": "John Sales",
        "agent_code": "AGT001"
      },
      "created_at": "2024-01-15T10:00:00Z",
      "updated_at": "2024-01-15T15:30:00Z"
    }
  ],
  "total": 150,
  "page": 1,
  "size": 20,
  "pages": 8
}
```

#### Create Sales Record
```javascript
POST /sales

// Request Body
{
  "bill_book_id": 1,           // Required: Bill book for numbering
  "customer_id": 1,            // Required: Customer ID
  "agent_id": 1,               // Optional: Sales agent
  "sales_date": "2024-01-15",  // Required: Sales date (YYYY-MM-DD)
  "due_date": "2024-02-15",    // Optional: Payment due date
  "tax_type": "INCLUDE_TAX",   // Required: INCLUDE_TAX, EXCLUDE_TAX, WITHOUT_TAX
  "discount_percentage": 5.0,   // Optional: Overall discount %
  "discount_amount": 0.0,      // Optional: Fixed discount amount
  "notes": "Sample order",     // Optional: Order notes
  "items": [                   // Required: At least one item
    {
      "product_variant_id": 1,
      "quantity": 2,
      "unit_price": 100.0,
      "discount_amount": 10.0  // Optional: Item-level discount
    }
  ]
}

// Response
{
  "id": 1,
  "bill_number": "B2B001",
  "status": "DRAFT",
  "sales_date": "2024-01-15",
  "due_date": "2024-02-15",
  "tax_type": "INCLUDE_TAX",
  "total_amount": 190.0,
  "tax_amount": 15.0,
  "discount_amount": 10.0,
  "customer": { ... },
  "agent": { ... },
  "items": [
    {
      "id": 1,
      "product_variant_id": 1,
      "product_name": "Cotton Shirt - Blue",
      "quantity": 2,
      "unit_price": 100.0,
      "discount_amount": 10.0,
      "tax_rate": 12.0,
      "tax_amount": 15.0,
      "total_amount": 190.0
    }
  ],
  "created_at": "2024-01-15T10:00:00Z"
}
```

#### Get Sales Details
```javascript
GET /sales/{id}

// Response includes complete sales info with items
{
  "id": 1,
  "bill_number": "B2B001",
  "status": "CONFIRMED",
  // ... all sales fields
  "items": [
    {
      "id": 1,
      "product_variant_id": 1,
      "product_name": "Cotton Shirt - Blue",
      "variant_code": "CSH001-BLU-L",
      "hsn_code": "6205",
      "unit_type": "PCS",
      "quantity": 2,
      "unit_price": 100.0,
      "discount_amount": 10.0,
      "tax_rate": 12.0,
      "tax_amount": 15.0,
      "total_amount": 190.0
    }
  ],
  "calculations": {
    "subtotal": 200.0,
    "total_discount": 10.0,
    "total_tax": 15.0,
    "grand_total": 190.0
  }
}
```

#### Update Sales Record
```javascript
PUT /sales/{id}

// Request Body (same as create, all fields optional)
{
  "due_date": "2024-03-15",
  "discount_percentage": 10.0,
  "notes": "Updated notes"
}
```

#### Delete Sales Record
```javascript
DELETE /sales/{id}

// Response
{
  "message": "Sales record deleted successfully"
}
```

### 2. Status Management

#### Update Sales Status
```javascript
PUT /sales/{id}/status

// Request Body
{
  "status": "CONFIRMED",  // DRAFT → CONFIRMED → DISPATCHED → DELIVERED
  "notes": "Order confirmed by customer"  // Optional
}

// Response
{
  "id": 1,
  "bill_number": "B2B001",
  "status": "CONFIRMED",
  "status_updated_at": "2024-01-15T15:30:00Z",
  "notes": "Order confirmed by customer"
}
```

### 3. Sales Items Management

#### Get Sales Items
```javascript
GET /sales/{id}/items

// Response
{
  "items": [
    {
      "id": 1,
      "product_variant_id": 1,
      "product_name": "Cotton Shirt - Blue",
      "quantity": 2,
      "unit_price": 100.0,
      "total_amount": 190.0
    }
  ],
  "total_items": 1,
  "total_quantity": 2,
  "total_amount": 190.0
}
```

#### Add Sales Item
```javascript
POST /sales/{id}/items

// Request Body
{
  "product_variant_id": 1,
  "quantity": 3,
  "unit_price": 150.0,
  "discount_amount": 15.0
}

// Response
{
  "id": 2,
  "product_variant_id": 1,
  "product_name": "Cotton Shirt - Blue",
  "quantity": 3,
  "unit_price": 150.0,
  "discount_amount": 15.0,
  "tax_amount": 22.5,
  "total_amount": 285.0
}
```

#### Update Sales Item
```javascript
PUT /sales/{id}/items/{item_id}

// Request Body
{
  "quantity": 5,
  "unit_price": 120.0,
  "discount_amount": 20.0
}
```

#### Remove Sales Item
```javascript
DELETE /sales/{id}/items/{item_id}

// Response
{
  "message": "Sales item removed successfully"
}
```

### 4. Analytics & Reports

#### Sales Summary
```javascript
GET /sales/summary

// Query Parameters
{
  start_date: '2024-01-01',
  end_date: '2024-12-31',
  status: 'CONFIRMED'  // Optional filter
}

// Response
{
  "total_sales": 150,
  "total_amount": 125000.50,
  "total_tax": 15000.25,
  "average_order_value": 833.34,
  "status_breakdown": {
    "DRAFT": 25,
    "CONFIRMED": 100,
    "DISPATCHED": 20,
    "DELIVERED": 5
  },
  "monthly_breakdown": [
    {
      "month": "2024-01",
      "sales_count": 45,
      "total_amount": 35000.0
    }
  ]
}
```

#### Status Report
```javascript
GET /sales/status-report

// Response
{
  "total_sales": 150,
  "status_counts": {
    "DRAFT": 25,
    "CONFIRMED": 100,
    "DISPATCHED": 20,
    "DELIVERED": 5
  },
  "status_amounts": {
    "DRAFT": 15000.0,
    "CONFIRMED": 85000.0,
    "DISPATCHED": 20000.0,
    "DELIVERED": 5000.0
  }
}
```

#### Customer Summary
```javascript
GET /sales/customer-summary

// Response
{
  "customers": [
    {
      "customer_id": 1,
      "customer_name": "ABC Company",
      "total_sales": 25,
      "total_amount": 45000.0,
      "last_sale_date": "2024-01-15"
    }
  ],
  "total_customers": 50,
  "total_amount": 125000.0
}
```

### 5. Utility Functions

#### Generate Bill Number
```javascript
POST /sales/generate-bill-number

// Request Body
{
  "bill_book_id": 1
}

// Response
{
  "bill_number": "B2B001",
  "bill_book_id": 1,
  "series": "B2B",
  "next_number": 1
}
```

#### Calculate Taxes
```javascript
POST /sales/calculate-taxes

// Request Body
{
  "items": [
    {
      "quantity": 2,
      "unit_price": 100.0,
      "tax_rate": 12.0,
      "discount_amount": 10.0
    }
  ],
  "tax_type": "INCLUDE_TAX",
  "discount_percentage": 5.0
}

// Response
{
  "subtotal": 200.0,
  "total_discount": 20.0,
  "taxable_amount": 180.0,
  "total_tax": 21.6,
  "grand_total": 201.6,
  "items": [
    {
      "item_total": 190.0,
      "tax_amount": 20.34,
      "final_amount": 201.6
    }
  ]
}
```

## 🎨 Frontend Implementation Examples

### React Component Example

```jsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';

const SalesList = () => {
  const [sales, setSales] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    page: 1,
    size: 20,
    status: '',
    search: ''
  });

  const fetchSales = async () => {
    try {
      setLoading(true);
      const response = await axios.get('/api/sales', {
        params: filters,
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      setSales(response.data);
    } catch (error) {
      console.error('Error fetching sales:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSales();
  }, [filters]);

  const updateStatus = async (salesId, newStatus) => {
    try {
      await axios.put(`/api/sales/${salesId}/status`, {
        status: newStatus
      }, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      fetchSales(); // Refresh list
    } catch (error) {
      console.error('Error updating status:', error);
    }
  };

  return (
    <div>
      {/* Filter UI */}
      <div className="filters">
        <select
          value={filters.status}
          onChange={(e) => setFilters({...filters, status: e.target.value})}
        >
          <option value="">All Status</option>
          <option value="DRAFT">Draft</option>
          <option value="CONFIRMED">Confirmed</option>
          <option value="DISPATCHED">Dispatched</option>
          <option value="DELIVERED">Delivered</option>
        </select>
        
        <input
          type="text"
          placeholder="Search..."
          value={filters.search}
          onChange={(e) => setFilters({...filters, search: e.target.value})}
        />
      </div>

      {/* Sales List */}
      {loading ? (
        <div>Loading...</div>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Bill Number</th>
              <th>Customer</th>
              <th>Date</th>
              <th>Amount</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {sales.items?.map(sale => (
              <tr key={sale.id}>
                <td>{sale.bill_number}</td>
                <td>{sale.customer.customer_name}</td>
                <td>{sale.sales_date}</td>
                <td>₹{sale.total_amount}</td>
                <td>
                  <span className={`status-${sale.status.toLowerCase()}`}>
                    {sale.status}
                  </span>
                </td>
                <td>
                  {sale.status === 'DRAFT' && (
                    <button onClick={() => updateStatus(sale.id, 'CONFIRMED')}>
                      Confirm
                    </button>
                  )}
                  {sale.status === 'CONFIRMED' && (
                    <button onClick={() => updateStatus(sale.id, 'DISPATCHED')}>
                      Dispatch
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
};

export default SalesList;
```

### Vue.js Component Example

```vue
<template>
  <div class="sales-form">
    <form @submit.prevent="createSales">
      <div class="form-group">
        <label>Customer</label>
        <select v-model="salesData.customer_id" required>
          <option value="">Select Customer</option>
          <option v-for="customer in customers" :key="customer.id" :value="customer.id">
            {{ customer.customer_name }}
          </option>
        </select>
      </div>

      <div class="form-group">
        <label>Bill Book</label>
        <select v-model="salesData.bill_book_id" required>
          <option value="">Select Bill Book</option>
          <option v-for="book in billBooks" :key="book.id" :value="book.id">
            {{ book.book_name }} ({{ book.tax_type }})
          </option>
        </select>
      </div>

      <div class="form-group">
        <label>Tax Type</label>
        <select v-model="salesData.tax_type" required>
          <option value="INCLUDE_TAX">Include Tax</option>
          <option value="EXCLUDE_TAX">Exclude Tax</option>
          <option value="WITHOUT_TAX">Without Tax</option>
        </select>
      </div>

      <div class="items-section">
        <h3>Sales Items</h3>
        <div v-for="(item, index) in salesData.items" :key="index" class="item-row">
          <select v-model="item.product_variant_id" required>
            <option value="">Select Product</option>
            <option v-for="variant in productVariants" :key="variant.id" :value="variant.id">
              {{ variant.variant_name }} - ₹{{ variant.mrp }}
            </option>
          </select>
          
          <input
            type="number"
            v-model="item.quantity"
            placeholder="Quantity"
            min="1"
            required
          />
          
          <input
            type="number"
            v-model="item.unit_price"
            placeholder="Unit Price"
            min="0"
            step="0.01"
            required
          />
          
          <input
            type="number"
            v-model="item.discount_amount"
            placeholder="Discount"
            min="0"
            step="0.01"
          />
          
          <button type="button" @click="removeItem(index)">Remove</button>
        </div>
        
        <button type="button" @click="addItem">Add Item</button>
      </div>

      <div class="form-actions">
        <button type="submit">Create Sales</button>
        <button type="button" @click="calculateTaxes">Calculate Taxes</button>
      </div>
    </form>

    <div v-if="taxCalculation" class="tax-summary">
      <h3>Tax Calculation</h3>
      <p>Subtotal: ₹{{ taxCalculation.subtotal }}</p>
      <p>Discount: ₹{{ taxCalculation.total_discount }}</p>
      <p>Tax: ₹{{ taxCalculation.total_tax }}</p>
      <p><strong>Total: ₹{{ taxCalculation.grand_total }}</strong></p>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'SalesForm',
  data() {
    return {
      salesData: {
        customer_id: '',
        bill_book_id: '',
        tax_type: 'INCLUDE_TAX',
        sales_date: new Date().toISOString().split('T')[0],
        items: [
          {
            product_variant_id: '',
            quantity: 1,
            unit_price: 0,
            discount_amount: 0
          }
        ]
      },
      customers: [],
      billBooks: [],
      productVariants: [],
      taxCalculation: null
    };
  },
  async mounted() {
    await this.loadData();
  },
  methods: {
    async loadData() {
      try {
        const [customersRes, billBooksRes, variantsRes] = await Promise.all([
          axios.get('/api/customers'),
          axios.get('/api/bill-books'),
          axios.get('/api/product-variants')
        ]);
        
        this.customers = customersRes.data;
        this.billBooks = billBooksRes.data;
        this.productVariants = variantsRes.data;
      } catch (error) {
        console.error('Error loading data:', error);
      }
    },
    
    addItem() {
      this.salesData.items.push({
        product_variant_id: '',
        quantity: 1,
        unit_price: 0,
        discount_amount: 0
      });
    },
    
    removeItem(index) {
      if (this.salesData.items.length > 1) {
        this.salesData.items.splice(index, 1);
      }
    },
    
    async calculateTaxes() {
      try {
        const response = await axios.post('/api/sales/calculate-taxes', {
          items: this.salesData.items.map(item => ({
            quantity: Number(item.quantity),
            unit_price: Number(item.unit_price),
            discount_amount: Number(item.discount_amount),
            tax_rate: 12.0 // Get from product variant
          })),
          tax_type: this.salesData.tax_type
        });
        
        this.taxCalculation = response.data;
      } catch (error) {
        console.error('Error calculating taxes:', error);
      }
    },
    
    async createSales() {
      try {
        const response = await axios.post('/api/sales', this.salesData);
        
        this.$emit('sales-created', response.data);
        this.$router.push(`/sales/${response.data.id}`);
      } catch (error) {
        console.error('Error creating sales:', error);
        alert('Error creating sales record');
      }
    }
  }
};
</script>
```

## 🔍 Status Workflow

### Status Transitions
```
DRAFT ────────────► CONFIRMED ────────────► DISPATCHED ────────────► DELIVERED
  │                      │                      │                      │
  │                      │                      │                      │
  ▼                      ▼                      ▼                      ▼
Edit/Delete         Lock for editing      Update tracking     Final status
allowed             Bill generated       Generate invoice    Payment complete
```

### Status Validation Rules
- **DRAFT**: Can be edited, deleted, or confirmed
- **CONFIRMED**: Cannot be edited, can be dispatched
- **DISPATCHED**: Cannot be edited, can be marked delivered
- **DELIVERED**: Final status, no changes allowed

## 💰 Tax Calculation Logic

### Tax Types Explained

#### INCLUDE_TAX
Price includes tax amount:
```javascript
// Example: Product price ₹112 with 12% tax
const priceWithTax = 112;
const taxRate = 12;
const taxAmount = (priceWithTax * taxRate) / (100 + taxRate);
// taxAmount = (112 * 12) / (100 + 12) = 12
const priceWithoutTax = priceWithTax - taxAmount; // 100
```

#### EXCLUDE_TAX
Tax added to price:
```javascript
// Example: Product price ₹100 with 12% tax
const price = 100;
const taxRate = 12;
const taxAmount = (price * taxRate) / 100; // 12
const totalPrice = price + taxAmount; // 112
```

#### WITHOUT_TAX
No tax calculations:
```javascript
const price = 100;
const taxAmount = 0;
const totalPrice = price; // 100
```

## 🎯 Frontend State Management

### Redux Store Structure
```javascript
const initialState = {
  sales: {
    list: [],
    current: null,
    loading: false,
    error: null,
    pagination: {
      page: 1,
      size: 20,
      total: 0
    },
    filters: {
      status: '',
      customer_id: '',
      search: ''
    }
  },
  customers: [],
  billBooks: [],
  productVariants: []
};
```

### Actions Example
```javascript
// Redux actions
export const fetchSales = (filters) => async (dispatch) => {
  dispatch({ type: 'SALES_LOADING' });
  try {
    const response = await api.get('/sales', { params: filters });
    dispatch({ type: 'SALES_SUCCESS', payload: response.data });
  } catch (error) {
    dispatch({ type: 'SALES_ERROR', payload: error.message });
  }
};

export const createSales = (salesData) => async (dispatch) => {
  try {
    const response = await api.post('/sales', salesData);
    dispatch({ type: 'SALES_CREATED', payload: response.data });
    return response.data;
  } catch (error) {
    dispatch({ type: 'SALES_ERROR', payload: error.message });
    throw error;
  }
};

export const updateStatus = (salesId, status) => async (dispatch) => {
  try {
    const response = await api.put(`/sales/${salesId}/status`, { status });
    dispatch({ type: 'SALES_STATUS_UPDATED', payload: response.data });
    return response.data;
  } catch (error) {
    dispatch({ type: 'SALES_ERROR', payload: error.message });
    throw error;
  }
};
```

## 🔄 Real-time Updates

### WebSocket Integration (if implemented)
```javascript
// WebSocket connection for real-time updates
const ws = new WebSocket('ws://localhost:8000/ws/sales');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  switch (data.type) {
    case 'SALES_UPDATED':
      dispatch(updateSalesInStore(data.sales));
      break;
    case 'STATUS_CHANGED':
      dispatch(updateSalesStatus(data.sales_id, data.status));
      break;
  }
};
```

## 🚨 Error Handling

### Common Error Codes
```javascript
const ErrorCodes = {
  400: 'Bad Request - Invalid data',
  401: 'Unauthorized - Invalid token',
  403: 'Forbidden - Insufficient permissions',
  404: 'Not Found - Sales record not found',
  422: 'Validation Error - Invalid input data',
  500: 'Server Error - Internal server error'
};

// Error handling utility
const handleApiError = (error) => {
  if (error.response) {
    const { status, data } = error.response;
    return {
      code: status,
      message: data.detail || ErrorCodes[status] || 'Unknown error'
    };
  }
  return {
    code: 'NETWORK_ERROR',
    message: 'Network connection error'
  };
};
```

### Validation Errors
```javascript
// Handle validation errors
const handleValidationError = (error) => {
  if (error.response?.status === 422) {
    const errors = error.response.data.detail;
    return errors.map(err => ({
      field: err.loc.join('.'),
      message: err.msg
    }));
  }
  return [];
};
```

## 📱 Mobile Responsiveness

### Responsive Design Considerations
```css
/* Mobile-first approach */
.sales-table {
  width: 100%;
  overflow-x: auto;
}

@media (max-width: 768px) {
  .sales-table {
    font-size: 12px;
  }
  
  .sales-form {
    padding: 10px;
  }
  
  .form-group {
    margin-bottom: 15px;
  }
  
  .item-row {
    flex-direction: column;
    gap: 10px;
  }
}

/* Touch-friendly buttons */
.mobile-action-btn {
  min-height: 44px;
  min-width: 44px;
  padding: 10px 15px;
}
```

## 🔒 Security Best Practices

### Frontend Security
```javascript
// Input sanitization
const sanitizeInput = (input) => {
  return input
    .replace(/[<>]/g, '') // Remove potential XSS characters
    .trim()
    .substring(0, 255); // Limit length
};

// Amount validation
const validateAmount = (amount) => {
  const num = parseFloat(amount);
  return !isNaN(num) && num >= 0 && num <= 999999.99;
};

// Token management
const TokenManager = {
  get: () => localStorage.getItem('auth_token'),
  set: (token) => localStorage.setItem('auth_token', token),
  remove: () => localStorage.removeItem('auth_token'),
  isValid: (token) => {
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      return payload.exp > Date.now() / 1000;
    } catch {
      return false;
    }
  }
};
```

## 📊 Performance Optimization

### API Call Optimization
```javascript
// Debounced search
import { debounce } from 'lodash';

const debouncedSearch = debounce((searchTerm) => {
  fetchSales({ search: searchTerm });
}, 300);

// Pagination optimization
const usePagination = (initialPage = 1, initialSize = 20) => {
  const [pagination, setPagination] = useState({
    page: initialPage,
    size: initialSize
  });
  
  const loadMore = () => {
    setPagination(prev => ({
      ...prev,
      page: prev.page + 1
    }));
  };
  
  return { pagination, setPagination, loadMore };
};

// Caching with React Query
import { useQuery } from 'react-query';

const useSales = (filters) => {
  return useQuery(
    ['sales', filters],
    () => fetchSales(filters),
    {
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
      refetchOnWindowFocus: false
    }
  );
};
```

This comprehensive guide provides everything needed for frontend development with the Sales Bill API. The examples cover React, Vue.js, state management, error handling, and performance optimization.
