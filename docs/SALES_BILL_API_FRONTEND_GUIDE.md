# Sales Bill API - Complete Frontend Development Guide

## Table of Contents
1. [Overview](#overview)
2. [Base Configuration](#base-configuration)
3. [Authentication](#authentication)
4. [Core Endpoints](#core-endpoints)
5. [Data Models](#data-models)
6. [Frontend Integration Examples](#frontend-integration-examples)
7. [Error Handling](#error-handling)
8. [Business Logic](#business-logic)
9. [Testing Guide](#testing-guide)

## Overview

The Sales Bill API provides complete CRUD operations for managing sales transactions in the ERP system. It includes features for:

- Sales transaction management (create, read, update, delete)
- Sales items management (add, edit, remove items)
- Status workflow (draft → confirmed → dispatched → delivered)
- Advanced filtering and pagination
- Bulk operations
- Sales analytics and reporting
- Integration with customers, agents, products, and bill books

**Base URL**: `http://localhost:8000/api/sales`
**API Documentation**: `http://localhost:8000/docs`

## Base Configuration

```javascript
// API Configuration
const API_CONFIG = {
  baseURL: 'http://localhost:8000',
  endpoints: {
    auth: '/auth',
    sales: '/sales',
    customers: '/customers',
    agents: '/agents',
    products: '/product-management',
    billBooks: '/bill-books'
  }
};

// Axios instance with auth
import axios from 'axios';

const api = axios.create({
  baseURL: API_CONFIG.baseURL,
  headers: {
    'Content-Type': 'application/json',
  }
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
```

## Authentication

All sales endpoints require JWT authentication. Include the bearer token in the `Authorization` header:

```javascript
// Login and get token
const login = async (username, password) => {
  const response = await api.post('/auth/login', {
    username,
    password
  });
  
  const { access_token } = response.data;
  localStorage.setItem('access_token', access_token);
  return access_token;
};
```

## Core Endpoints

### 1. Sales CRUD Operations

#### Create Sales
```javascript
// POST /sales/
const createSales = async (salesData) => {
  const response = await api.post('/sales/', {
    bill_book_id: 1,
    customer_id: 1,
    agent_id: 1,
    bill_date: "2025-08-30",
    due_date: "2025-09-30",
    additional_charges: 50.00,
    transport_details: "By road via ABC Transport",
    llr_no: "LLR001",
    llr_date: "2025-08-30",
    items: [
      {
        variant_id: 1,
        quantity: 5.000,
        sale_rate: 150.00,
        discount_percentage: 10.0,
        tax_percentage: 18.0
      }
    ]
  });
  return response.data;
};
```

#### Get Sales List
```javascript
// GET /sales/
const getSalesList = async (filters = {}) => {
  const params = new URLSearchParams();
  
  // Pagination
  if (filters.page) params.append('page', filters.page);
  if (filters.size) params.append('size', filters.size);
  
  // Filters
  if (filters.status) params.append('status', filters.status);
  if (filters.customer_id) params.append('customer_id', filters.customer_id);
  if (filters.agent_id) params.append('agent_id', filters.agent_id);
  if (filters.bill_book_id) params.append('bill_book_id', filters.bill_book_id);
  if (filters.from_date) params.append('from_date', filters.from_date);
  if (filters.to_date) params.append('to_date', filters.to_date);
  if (filters.min_amount) params.append('min_amount', filters.min_amount);
  if (filters.max_amount) params.append('max_amount', filters.max_amount);
  if (filters.search) params.append('search', filters.search);
  
  // Sorting
  if (filters.sort_by) params.append('sort_by', filters.sort_by);
  if (filters.sort_order) params.append('sort_order', filters.sort_order);
  
  const response = await api.get(`/sales/?${params}`);
  return response.data;
};
```

#### Get Sales Details
```javascript
// GET /sales/{sales_id}
const getSalesDetails = async (salesId) => {
  const response = await api.get(`/sales/${salesId}`);
  return response.data;
};
```

#### Update Sales
```javascript
// PUT /sales/{sales_id}
const updateSales = async (salesId, updateData) => {
  const response = await api.put(`/sales/${salesId}`, updateData);
  return response.data;
};
```

#### Delete Sales
```javascript
// DELETE /sales/{sales_id}
const deleteSales = async (salesId) => {
  const response = await api.delete(`/sales/${salesId}`);
  return response.data;
};
```

### 2. Sales Status Management

#### Update Sales Status
```javascript
// PATCH /sales/{sales_id}/status
const updateSalesStatus = async (salesId, status, comments = '') => {
  const response = await api.patch(`/sales/${salesId}/status`, {
    new_status: status, // "DRAFT", "CONFIRMED", "DISPATCHED", "DELIVERED", "CANCELLED"
    comments: comments
  });
  return response.data;
};

// Example: Confirm a sales order
await updateSalesStatus(1, "CONFIRMED", "Order confirmed by customer");
```

#### Bulk Status Update
```javascript
// PATCH /sales/bulk/status
const bulkUpdateStatus = async (salesIds, status, comments = '') => {
  const response = await api.patch('/sales/bulk/status', {
    sales_ids: salesIds,
    new_status: status,
    comments: comments
  });
  return response.data;
};
```

### 3. Sales Items Management

#### Add Sales Item
```javascript
// POST /sales/{sales_id}/items
const addSalesItem = async (salesId, itemData) => {
  const response = await api.post(`/sales/${salesId}/items`, {
    variant_id: 1,
    quantity: 3.000,
    sale_rate: 200.00,
    discount_percentage: 5.0,
    tax_percentage: 18.0
  });
  return response.data;
};
```

#### Update Sales Item
```javascript
// PUT /sales/{sales_id}/items/{item_id}
const updateSalesItem = async (salesId, itemId, updateData) => {
  const response = await api.put(`/sales/${salesId}/items/${itemId}`, {
    quantity: 5.000,
    sale_rate: 180.00,
    discount_percentage: 10.0
  });
  return response.data;
};
```

#### Delete Sales Item
```javascript
// DELETE /sales/{sales_id}/items/{item_id}
const deleteSalesItem = async (salesId, itemId) => {
  const response = await api.delete(`/sales/${salesId}/items/${itemId}`);
  return response.data;
};
```

### 4. Analytics and Reporting

#### Get Sales Summary
```javascript
// GET /sales/summary
const getSalesSummary = async (from_date, to_date) => {
  const params = new URLSearchParams();
  if (from_date) params.append('from_date', from_date);
  if (to_date) params.append('to_date', to_date);
  
  const response = await api.get(`/sales/summary?${params}`);
  return response.data;
};
```

#### Get Sales Analytics
```javascript
// GET /sales/analytics
const getSalesAnalytics = async (period = 'monthly') => {
  const response = await api.get(`/sales/analytics?period=${period}`);
  return response.data;
};
```

### 5. Utility Endpoints

#### Get Pending Sales
```javascript
// GET /sales/pending
const getPendingSales = async () => {
  const response = await api.get('/sales/pending');
  return response.data;
};
```

#### Get Sales History
```javascript
// GET /sales/{sales_id}/history
const getSalesHistory = async (salesId) => {
  const response = await api.get(`/sales/${salesId}/history`);
  return response.data;
};
```

#### Validate Sales Data
```javascript
// POST /sales/validate
const validateSalesData = async (salesData) => {
  const response = await api.post('/sales/validate', salesData);
  return response.data;
};
```

## Data Models

### Sales Response Model
```typescript
interface SalesResponse {
  id: number;
  bill_number: string;
  bill_book_id: number;
  customer_id: number;
  agent_id?: number;
  bill_date: string;
  due_date?: string;
  status: 'DRAFT' | 'CONFIRMED' | 'DISPATCHED' | 'DELIVERED' | 'CANCELLED';
  total_quantity: number;
  total_amount: number;
  total_discount: number;
  total_tax: number;
  additional_charges: number;
  final_amount: number;
  transport_details?: string;
  llr_no?: string;
  llr_date?: string;
  created_at: string;
  updated_at: string;
  
  // Related objects
  customer: Customer;
  agent?: Agent;
  bill_book: BillBook;
  items: SalesItem[];
}
```

### Sales Item Model
```typescript
interface SalesItem {
  id: number;
  sales_id: number;
  variant_id: number;
  product_name: string;
  quantity: number;
  sale_rate: number;
  discount_percentage: number;
  discount_amount: number;
  taxable_amount: number;
  tax_percentage: number;
  tax_amount: number;
  total_amount: number;
  created_at: string;
  updated_at: string;
  
  // Related objects
  variant: ProductVariant;
}
```

### Filter Parameters
```typescript
interface SalesFilter {
  // Pagination
  page?: number;
  size?: number;
  
  // Filters
  status?: string;
  customer_id?: number;
  agent_id?: number;
  bill_book_id?: number;
  from_date?: string;
  to_date?: string;
  min_amount?: number;
  max_amount?: number;
  search?: string;
  
  // Sorting
  sort_by?: 'bill_date' | 'total_amount' | 'created_at' | 'bill_number';
  sort_order?: 'asc' | 'desc';
}
```

## Frontend Integration Examples

### React Hook for Sales Management
```jsx
import { useState, useEffect } from 'react';

const useSales = () => {
  const [sales, setSales] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchSales = async (filters = {}) => {
    setLoading(true);
    try {
      const data = await getSalesList(filters);
      setSales(data.items);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const createNewSales = async (salesData) => {
    try {
      const newSales = await createSales(salesData);
      setSales(prev => [newSales, ...prev]);
      return newSales;
    } catch (err) {
      setError(err.message);
      throw err;
    }
  };

  const updateSalesStatus = async (salesId, status, comments) => {
    try {
      const updated = await updateSalesStatus(salesId, status, comments);
      setSales(prev => 
        prev.map(s => s.id === salesId ? updated : s)
      );
      return updated;
    } catch (err) {
      setError(err.message);
      throw err;
    }
  };

  return {
    sales,
    loading,
    error,
    fetchSales,
    createNewSales,
    updateSalesStatus
  };
};
```

### Vue.js Composable
```javascript
import { ref, reactive } from 'vue';

export function useSales() {
  const sales = ref([]);
  const loading = ref(false);
  const error = ref(null);

  const fetchSales = async (filters = {}) => {
    loading.value = true;
    try {
      const data = await getSalesList(filters);
      sales.value = data.items;
      error.value = null;
    } catch (err) {
      error.value = err.message;
    } finally {
      loading.value = false;
    }
  };

  const createSales = async (salesData) => {
    try {
      const newSales = await createSales(salesData);
      sales.value.unshift(newSales);
      return newSales;
    } catch (err) {
      error.value = err.message;
      throw err;
    }
  };

  return {
    sales,
    loading,
    error,
    fetchSales,
    createSales
  };
}
```

### Sales Form Component (React)
```jsx
import React, { useState } from 'react';

const SalesForm = ({ onSubmit, initialData = null }) => {
  const [formData, setFormData] = useState({
    bill_book_id: '',
    customer_id: '',
    agent_id: '',
    bill_date: new Date().toISOString().split('T')[0],
    due_date: '',
    additional_charges: 0,
    transport_details: '',
    llr_no: '',
    llr_date: '',
    items: [
      {
        variant_id: '',
        quantity: 1,
        sale_rate: 0,
        discount_percentage: 0,
        tax_percentage: 18
      }
    ]
  });

  const addItem = () => {
    setFormData(prev => ({
      ...prev,
      items: [
        ...prev.items,
        {
          variant_id: '',
          quantity: 1,
          sale_rate: 0,
          discount_percentage: 0,
          tax_percentage: 18
        }
      ]
    }));
  };

  const updateItem = (index, field, value) => {
    setFormData(prev => ({
      ...prev,
      items: prev.items.map((item, i) => 
        i === index ? { ...item, [field]: value } : item
      )
    }));
  };

  const removeItem = (index) => {
    setFormData(prev => ({
      ...prev,
      items: prev.items.filter((_, i) => i !== index)
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <form onSubmit={handleSubmit}>
      {/* Form fields */}
      <div>
        <label>Customer:</label>
        <select 
          value={formData.customer_id}
          onChange={(e) => setFormData(prev => ({...prev, customer_id: e.target.value}))}
          required
        >
          <option value="">Select Customer</option>
          {/* Customer options */}
        </select>
      </div>

      {/* Items section */}
      <div>
        <h3>Sales Items</h3>
        {formData.items.map((item, index) => (
          <div key={index} className="item-row">
            <select 
              value={item.variant_id}
              onChange={(e) => updateItem(index, 'variant_id', e.target.value)}
              required
            >
              <option value="">Select Product</option>
              {/* Product options */}
            </select>
            
            <input
              type="number"
              placeholder="Quantity"
              value={item.quantity}
              onChange={(e) => updateItem(index, 'quantity', parseFloat(e.target.value))}
              step="0.001"
              min="0"
              required
            />
            
            <input
              type="number"
              placeholder="Sale Rate"
              value={item.sale_rate}
              onChange={(e) => updateItem(index, 'sale_rate', parseFloat(e.target.value))}
              step="0.01"
              min="0"
              required
            />
            
            <button type="button" onClick={() => removeItem(index)}>
              Remove
            </button>
          </div>
        ))}
        
        <button type="button" onClick={addItem}>
          Add Item
        </button>
      </div>

      <button type="submit">Create Sales</button>
    </form>
  );
};
```

## Error Handling

### Common Error Responses
```javascript
// 400 Bad Request
{
  "detail": "Validation error",
  "errors": [
    {
      "field": "bill_date",
      "message": "Bill date is required"
    }
  ]
}

// 404 Not Found
{
  "detail": "Sales not found with id: 123"
}

// 409 Conflict
{
  "detail": "Cannot delete sales with status CONFIRMED"
}

// 422 Validation Error
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

### Error Handling Function
```javascript
const handleApiError = (error) => {
  if (error.response) {
    const { status, data } = error.response;
    
    switch (status) {
      case 400:
        return data.detail || 'Bad request';
      case 401:
        localStorage.removeItem('access_token');
        window.location.href = '/login';
        return 'Authentication required';
      case 403:
        return 'Permission denied';
      case 404:
        return 'Resource not found';
      case 409:
        return data.detail || 'Conflict';
      case 422:
        // Handle validation errors
        const errors = data.detail.map(err => 
          `${err.loc.join('.')}: ${err.msg}`
        ).join(', ');
        return `Validation error: ${errors}`;
      case 500:
        return 'Server error';
      default:
        return data.detail || 'Unknown error';
    }
  }
  
  return error.message || 'Network error';
};
```

## Business Logic

### Status Workflow
```javascript
const SALES_STATUS_FLOW = {
  DRAFT: ['CONFIRMED', 'CANCELLED'],
  CONFIRMED: ['DISPATCHED', 'CANCELLED'],
  DISPATCHED: ['DELIVERED'],
  DELIVERED: [], // Final state
  CANCELLED: [] // Final state
};

const canUpdateStatus = (currentStatus, newStatus) => {
  return SALES_STATUS_FLOW[currentStatus]?.includes(newStatus) || false;
};
```

### Tax Calculations
```javascript
const calculateTax = (amount, taxPercentage) => {
  return (amount * taxPercentage) / 100;
};

const calculateItemTotal = (item) => {
  const baseAmount = item.quantity * item.sale_rate;
  const discountAmount = (baseAmount * item.discount_percentage) / 100;
  const taxableAmount = baseAmount - discountAmount;
  const taxAmount = calculateTax(taxableAmount, item.tax_percentage);
  return taxableAmount + taxAmount;
};

const calculateSalesTotal = (items, additionalCharges = 0) => {
  const itemsTotal = items.reduce((sum, item) => sum + calculateItemTotal(item), 0);
  return itemsTotal + additionalCharges;
};
```

## Testing Guide

### API Testing with Jest
```javascript
import { getSalesList, createSales } from './salesApi';

describe('Sales API', () => {
  test('should fetch sales list', async () => {
    const sales = await getSalesList();
    expect(sales).toHaveProperty('items');
    expect(Array.isArray(sales.items)).toBe(true);
  });

  test('should create new sales', async () => {
    const salesData = {
      bill_book_id: 1,
      customer_id: 1,
      bill_date: '2025-08-30',
      items: [
        {
          variant_id: 1,
          quantity: 5,
          sale_rate: 100,
          discount_percentage: 0,
          tax_percentage: 18
        }
      ]
    };

    const newSales = await createSales(salesData);
    expect(newSales).toHaveProperty('id');
    expect(newSales.bill_number).toBeTruthy();
  });
});
```

### Manual Testing Checklist
1. **Create Sales**: Test with valid and invalid data
2. **Update Sales**: Test status transitions and field updates
3. **Delete Sales**: Test with different statuses
4. **Items Management**: Add, update, and remove items
5. **Filtering**: Test all filter combinations
6. **Pagination**: Test page navigation
7. **Bulk Operations**: Test bulk status updates
8. **Error Scenarios**: Test network errors, validation errors

This documentation provides everything a frontend developer needs to integrate with the Sales Bill API. The API is fully functional and ready for production use.
