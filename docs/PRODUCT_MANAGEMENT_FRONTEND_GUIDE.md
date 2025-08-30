# Product Management API - Frontend Developer Guide

## Overview
This guide provides comprehensive documentation for frontend developers to integrate with the Garments ERP Product Management API. The API follows RESTful conventions and uses JWT authentication.

## Base Configuration

### API Base URL
```
http://localhost:8000/api/products
```

### Authentication
All endpoints require JWT authentication:
```javascript
headers: {
  'Authorization': 'Bearer <your_jwt_token>',
  'Content-Type': 'application/json'
}
```

---

## 1. PRODUCT SIZES API

### Create Size
```javascript
POST /api/products/sizes/
Content-Type: application/json

{
  "size_value": "38",
  "size_display": "Size 38",
  "size_code": "SZ38",
  "sort_order": 1,
  "is_active": true
}
```

**Response:**
```javascript
{
  "id": 1,
  "size_value": "38",
  "size_display": "Size 38", 
  "size_code": "SZ38",
  "sort_order": 1,
  "is_active": true,
  "created_at": "2025-08-27T00:00:00Z",
  "updated_at": "2025-08-27T00:00:00Z"
}
```

### List Sizes
```javascript
GET /api/products/sizes/?active_only=true
```

**Response:**
```javascript
[
  {
    "id": 1,
    "size_value": "36",
    "size_display": "Size 36",
    "size_code": "SZ36",
    "sort_order": 1,
    "is_active": true,
    "created_at": "2025-08-27T00:00:00Z",
    "updated_at": "2025-08-27T00:00:00Z"
  }
]
```

### Get Single Size
```javascript
GET /api/products/sizes/{size_id}
```

### Update Size
```javascript
PUT /api/products/sizes/{size_id}
{
  "size_value": "38 Updated",
  "is_active": false
}
```

---

## 2. SLEEVE TYPES API

### Create Sleeve Type
```javascript
POST /api/products/sleeve-types/
{
  "sleeve_type": "Full Sleeve",
  "sleeve_code": "SLFS",
  "description": "Full sleeve garment",
  "is_active": true
}
```

### List Sleeve Types
```javascript
GET /api/products/sleeve-types/?active_only=true
```

**Response:**
```javascript
[
  {
    "id": 1,
    "sleeve_type": "Full Sleeve",
    "sleeve_code": "SLFS",
    "description": "Full sleeve garment",
    "is_active": true,
    "created_at": "2025-08-27T00:00:00Z",
    "updated_at": "2025-08-27T00:00:00Z"
  }
]
```

### Update Sleeve Type
```javascript
PUT /api/products/sleeve-types/{sleeve_id}
{
  "sleeve_type": "Half Sleeve",
  "description": "Updated description"
}
```

---

## 3. PRODUCT DESIGNS API

### Create Design
```javascript
POST /api/products/designs/
{
  "design_name": "Plain",
  "design_code": "PLN",
  "design_category": "plain",
  "description": "Plain design",
  "is_active": true
}
```

**Design Categories:** `plain`, `pattern`, `print`, `texture`

### List Designs
```javascript
GET /api/products/designs/?active_only=true
```

**Response:**
```javascript
[
  {
    "id": 1,
    "design_name": "Plain",
    "design_code": "PLN",
    "design_category": "plain",
    "description": "Plain design",
    "is_active": true,
    "created_at": "2025-08-27T00:00:00Z",
    "updated_at": "2025-08-27T00:00:00Z"
  }
]
```

---

## 4. PRODUCTS API

### Create Product
```javascript
POST /api/products/products/
{
  "product_name": "Smart Plus Shirt",
  "product_code": "SPS001",
  "category_id": "CAT001",
  "description": "Premium quality shirt",
  "price_a": 500.00,
  "price_b": 450.00,
  "price_c": 400.00,
  "base_price": 425.00,
  "is_active": true,
  "create_all_variants": true,
  "size_ids": [1, 2, 3],
  "sleeve_type_ids": [1, 2],
  "design_ids": [1, 2]
}
```

### List Products with Filtering
```javascript
GET /api/products/products/?search=smart&category_id=CAT001&is_active=true&page=1&per_page=20
```

**Query Parameters:**
- `search`: Search in product name or code
- `category_id`: Filter by category
- `is_active`: Filter by active status
- `has_stock`: Filter products with stock
- `page`: Page number (default: 1)
- `per_page`: Items per page (1-100, default: 50)

**Response:**
```javascript
{
  "products": [
    {
      "id": 1,
      "product_name": "Smart Plus Shirt",
      "product_code": "SPS001",
      "category_id": "CAT001",
      "description": "Premium quality shirt",
      "price_a": 500.00,
      "price_b": 450.00,
      "price_c": 400.00,
      "base_price": 425.00,
      "is_active": true,
      "created_at": "2025-08-27T00:00:00Z",
      "updated_at": "2025-08-27T00:00:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 20
}
```

### Get Single Product
```javascript
GET /api/products/products/{product_id}?include_variants=true
```

### Update Product
```javascript
PUT /api/products/products/{product_id}
{
  "product_name": "Updated Product Name",
  "price_a": 550.00,
  "is_active": false
}
```

---

## 5. PRODUCT VARIANTS API

### Create Single Variant
```javascript
POST /api/products/variants/
{
  "product_id": 1,
  "size_id": 1,
  "sleeve_type_id": 1,
  "design_id": 1,
  "variant_code": "SPS001-SZ36-SLFS-PLN",
  "sku": "SMP36FCHK",
  "price": 425.00,
  "cost_price": 300.00,
  "is_active": true
}
```

### Create Bulk Variants
```javascript
POST /api/products/variants/bulk
{
  "product_id": 1,
  "variants": [
    {
      "size_id": 1,
      "sleeve_type_id": 1,
      "design_id": 1,
      "price": 425.00
    },
    {
      "size_id": 2,
      "sleeve_type_id": 1,
      "design_id": 1,
      "price": 430.00
    }
  ]
}
```

### List Variants with Advanced Filtering
```javascript
GET /api/products/variants/?product_id=1&size_id=1&min_stock=10&page=1&per_page=20
```

**Query Parameters:**
- `search`: Search in variant name, code, SKU
- `product_id`: Filter by product
- `size_id`: Filter by size
- `sleeve_type_id`: Filter by sleeve type
- `design_id`: Filter by design
- `is_active`: Filter by active status
- `min_stock`: Minimum stock balance
- `max_stock`: Maximum stock balance
- `page`: Page number
- `per_page`: Items per page

**Response:**
```javascript
{
  "variants": [
    {
      "id": 1,
      "product_id": 1,
      "size_id": 1,
      "sleeve_type_id": 1,
      "design_id": 1,
      "variant_code": "SPS001-SZ36-SLFS-PLN",
      "sku": "SMP36FPLN",
      "variant_name": "Smart Plus Shirt - Size 36 - Full Sleeve - Plain",
      "price": 425.00,
      "cost_price": 300.00,
      "stock_balance": 100.00,
      "is_active": true,
      "created_at": "2025-08-27T00:00:00Z",
      "updated_at": "2025-08-27T00:00:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 20
}
```

### Update Variant
```javascript
PUT /api/products/variants/{variant_id}
{
  "price": 450.00,
  "cost_price": 320.00,
  "is_active": false
}
```

---

## 6. STOCK MANAGEMENT API

### Create Stock Movement
```javascript
POST /api/products/stock/movements/
{
  "variant_id": 1,
  "movement_type": "IN",
  "quantity": 50.00,
  "unit_price": 300.00,
  "reference_type": "PURCHASE",
  "reference_id": 123,
  "reference_number": "PO2025001",
  "notes": "Initial stock from purchase order"
}
```

**Movement Types:** `IN`, `OUT`, `TRANSFER`, `ADJUSTMENT`

### Bulk Stock Movements
```javascript
POST /api/products/stock/movements/bulk
{
  "movements": [
    {
      "variant_id": 1,
      "movement_type": "IN",
      "quantity": 50.00,
      "unit_price": 300.00,
      "reference_type": "PURCHASE",
      "reference_number": "PO2025001",
      "notes": "Stock in from purchase"
    },
    {
      "variant_id": 2,
      "movement_type": "OUT",
      "quantity": 10.00,
      "reference_type": "SALE",
      "reference_number": "SO2025001",
      "notes": "Stock out from sale"
    }
  ]
}
```

### Get Stock Balance
```javascript
GET /api/products/stock/balance/{variant_id}
```

**Response:**
```javascript
{
  "variant_id": 1,
  "current_balance": 40.00,
  "variant_name": "Smart Plus Shirt - Size 36 - Full Sleeve - Plain",
  "product_name": "Smart Plus Shirt",
  "size_value": "36",
  "sleeve_type": "Full Sleeve",
  "design_name": "Plain"
}
```

### Get Stock Summary
```javascript
GET /api/products/stock/summary?product_id=1&low_stock_threshold=10
```

**Response:**
```javascript
{
  "total_variants": 12,
  "total_stock_value": 15000.00,
  "low_stock_variants": 2,
  "out_of_stock_variants": 1,
  "variants_summary": [
    {
      "variant_id": 1,
      "current_balance": 5.00,
      "variant_name": "Smart Plus Shirt - Size 36 - Full Sleeve - Plain",
      "product_name": "Smart Plus Shirt",
      "size_value": "36",
      "sleeve_type": "Full Sleeve",
      "design_name": "Plain"
    }
  ]
}
```

### List Stock Movements
```javascript
GET /api/products/stock/movements/?variant_id=1&movement_type=IN&page=1&per_page=20
```

---

## 7. FRONTEND IMPLEMENTATION EXAMPLES

### React.js Example - Product List Component

```jsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';

const ProductList = () => {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(0);

  const fetchProducts = async () => {
    try {
      const token = localStorage.getItem('jwt_token');
      const response = await axios.get('/api/products/products/', {
        headers: {
          'Authorization': `Bearer ${token}`
        },
        params: {
          search,
          page,
          per_page: 20
        }
      });
      
      setProducts(response.data.products);
      setTotalPages(Math.ceil(response.data.total / 20));
      setLoading(false);
    } catch (error) {
      console.error('Error fetching products:', error);
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProducts();
  }, [search, page]);

  return (
    <div>
      <h2>Products</h2>
      
      {/* Search Input */}
      <input
        type="text"
        placeholder="Search products..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
      />
      
      {/* Product List */}
      {loading ? (
        <div>Loading...</div>
      ) : (
        <div>
          {products.map(product => (
            <div key={product.id} className="product-card">
              <h3>{product.product_name}</h3>
              <p>Code: {product.product_code}</p>
              <p>Price A: ₹{product.price_a}</p>
              <p>Price B: ₹{product.price_b}</p>
              <p>Price C: ₹{product.price_c}</p>
              <p>Status: {product.is_active ? 'Active' : 'Inactive'}</p>
            </div>
          ))}
        </div>
      )}
      
      {/* Pagination */}
      <div>
        <button 
          disabled={page === 1} 
          onClick={() => setPage(page - 1)}
        >
          Previous
        </button>
        <span>Page {page} of {totalPages}</span>
        <button 
          disabled={page === totalPages} 
          onClick={() => setPage(page + 1)}
        >
          Next
        </button>
      </div>
    </div>
  );
};

export default ProductList;
```

### Create Product Form Component

```jsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';

const CreateProduct = () => {
  const [formData, setFormData] = useState({
    product_name: '',
    product_code: '',
    category_id: '',
    description: '',
    price_a: '',
    price_b: '',
    price_c: '',
    base_price: '',
    create_all_variants: false,
    size_ids: [],
    sleeve_type_ids: [],
    design_ids: []
  });
  
  const [sizes, setSizes] = useState([]);
  const [sleeveTypes, setSleeveTypes] = useState([]);
  const [designs, setDesigns] = useState([]);

  useEffect(() => {
    // Fetch dropdown data
    fetchSizes();
    fetchSleeveTypes();
    fetchDesigns();
  }, []);

  const fetchSizes = async () => {
    try {
      const token = localStorage.getItem('jwt_token');
      const response = await axios.get('/api/products/sizes/', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      setSizes(response.data);
    } catch (error) {
      console.error('Error fetching sizes:', error);
    }
  };

  const fetchSleeveTypes = async () => {
    try {
      const token = localStorage.getItem('jwt_token');
      const response = await axios.get('/api/products/sleeve-types/', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      setSleeveTypes(response.data);
    } catch (error) {
      console.error('Error fetching sleeve types:', error);
    }
  };

  const fetchDesigns = async () => {
    try {
      const token = localStorage.getItem('jwt_token');
      const response = await axios.get('/api/products/designs/', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      setDesigns(response.data);
    } catch (error) {
      console.error('Error fetching designs:', error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem('jwt_token');
      const response = await axios.post('/api/products/products/', formData, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      alert('Product created successfully!');
      console.log('Created product:', response.data);
      
    } catch (error) {
      console.error('Error creating product:', error);
      alert('Error creating product');
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <h2>Create New Product</h2>
      
      <div>
        <label>Product Name:</label>
        <input
          type="text"
          value={formData.product_name}
          onChange={(e) => setFormData({...formData, product_name: e.target.value})}
          required
        />
      </div>
      
      <div>
        <label>Product Code:</label>
        <input
          type="text"
          value={formData.product_code}
          onChange={(e) => setFormData({...formData, product_code: e.target.value})}
        />
      </div>
      
      <div>
        <label>Price A:</label>
        <input
          type="number"
          step="0.01"
          value={formData.price_a}
          onChange={(e) => setFormData({...formData, price_a: e.target.value})}
        />
      </div>
      
      <div>
        <label>Price B:</label>
        <input
          type="number"
          step="0.01"
          value={formData.price_b}
          onChange={(e) => setFormData({...formData, price_b: e.target.value})}
        />
      </div>
      
      <div>
        <label>Price C:</label>
        <input
          type="number"
          step="0.01"
          value={formData.price_c}
          onChange={(e) => setFormData({...formData, price_c: e.target.value})}
        />
      </div>
      
      <div>
        <label>
          <input
            type="checkbox"
            checked={formData.create_all_variants}
            onChange={(e) => setFormData({...formData, create_all_variants: e.target.checked})}
          />
          Create All Variants
        </label>
      </div>
      
      {formData.create_all_variants && (
        <>
          <div>
            <label>Sizes:</label>
            <select
              multiple
              value={formData.size_ids}
              onChange={(e) => {
                const values = Array.from(e.target.selectedOptions, option => parseInt(option.value));
                setFormData({...formData, size_ids: values});
              }}
            >
              {sizes.map(size => (
                <option key={size.id} value={size.id}>
                  {size.size_value}
                </option>
              ))}
            </select>
          </div>
          
          <div>
            <label>Sleeve Types:</label>
            <select
              multiple
              value={formData.sleeve_type_ids}
              onChange={(e) => {
                const values = Array.from(e.target.selectedOptions, option => parseInt(option.value));
                setFormData({...formData, sleeve_type_ids: values});
              }}
            >
              {sleeveTypes.map(sleeve => (
                <option key={sleeve.id} value={sleeve.id}>
                  {sleeve.sleeve_type}
                </option>
              ))}
            </select>
          </div>
          
          <div>
            <label>Designs:</label>
            <select
              multiple
              value={formData.design_ids}
              onChange={(e) => {
                const values = Array.from(e.target.selectedOptions, option => parseInt(option.value));
                setFormData({...formData, design_ids: values});
              }}
            >
              {designs.map(design => (
                <option key={design.id} value={design.id}>
                  {design.design_name}
                </option>
              ))}
            </select>
          </div>
        </>
      )}
      
      <button type="submit">Create Product</button>
    </form>
  );
};

export default CreateProduct;
```

### Stock Management Component

```jsx
import React, { useState } from 'react';
import axios from 'axios';

const StockManagement = ({ variantId }) => {
  const [stockData, setStockData] = useState({
    variant_id: variantId,
    movement_type: 'IN',
    quantity: '',
    unit_price: '',
    reference_type: '',
    reference_number: '',
    notes: ''
  });
  
  const [currentBalance, setCurrentBalance] = useState(0);

  const fetchStockBalance = async () => {
    try {
      const token = localStorage.getItem('jwt_token');
      const response = await axios.get(`/api/products/stock/balance/${variantId}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      setCurrentBalance(response.data.current_balance);
    } catch (error) {
      console.error('Error fetching stock balance:', error);
    }
  };

  const handleStockMovement = async (e) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem('jwt_token');
      await axios.post('/api/products/stock/movements/', stockData, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      alert('Stock movement recorded successfully!');
      fetchStockBalance(); // Refresh balance
      
    } catch (error) {
      console.error('Error recording stock movement:', error);
      alert('Error recording stock movement');
    }
  };

  return (
    <div>
      <h3>Stock Management</h3>
      <p>Current Balance: {currentBalance}</p>
      
      <form onSubmit={handleStockMovement}>
        <div>
          <label>Movement Type:</label>
          <select
            value={stockData.movement_type}
            onChange={(e) => setStockData({...stockData, movement_type: e.target.value})}
          >
            <option value="IN">Stock In</option>
            <option value="OUT">Stock Out</option>
            <option value="TRANSFER">Transfer</option>
            <option value="ADJUSTMENT">Adjustment</option>
          </select>
        </div>
        
        <div>
          <label>Quantity:</label>
          <input
            type="number"
            step="0.01"
            value={stockData.quantity}
            onChange={(e) => setStockData({...stockData, quantity: e.target.value})}
            required
          />
        </div>
        
        <div>
          <label>Unit Price:</label>
          <input
            type="number"
            step="0.01"
            value={stockData.unit_price}
            onChange={(e) => setStockData({...stockData, unit_price: e.target.value})}
          />
        </div>
        
        <div>
          <label>Reference Number:</label>
          <input
            type="text"
            value={stockData.reference_number}
            onChange={(e) => setStockData({...stockData, reference_number: e.target.value})}
          />
        </div>
        
        <div>
          <label>Notes:</label>
          <textarea
            value={stockData.notes}
            onChange={(e) => setStockData({...stockData, notes: e.target.value})}
          />
        </div>
        
        <button type="submit">Record Movement</button>
      </form>
    </div>
  );
};

export default StockManagement;
```

---

## 8. ERROR HANDLING

### Common Error Responses

**400 Bad Request**
```javascript
{
  "detail": "Product 'Smart Plus Shirt' already exists"
}
```

**401 Unauthorized**
```javascript
{
  "detail": "Not authenticated"
}
```

**404 Not Found**
```javascript
{
  "detail": "Product not found"
}
```

**422 Unprocessable Entity**
```javascript
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "product_name"],
      "msg": "Field required"
    }
  ]
}
```

**500 Internal Server Error**
```javascript
{
  "detail": "Failed to create product: Database connection error"
}
```

### Frontend Error Handling Example

```javascript
const apiCall = async (url, method = 'GET', data = null) => {
  try {
    const token = localStorage.getItem('jwt_token');
    const config = {
      method,
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    };
    
    if (data) {
      config.body = JSON.stringify(data);
    }
    
    const response = await fetch(url, config);
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'API request failed');
    }
    
    return await response.json();
    
  } catch (error) {
    console.error('API Error:', error);
    
    // Handle specific error cases
    if (error.message.includes('Not authenticated')) {
      // Redirect to login
      window.location.href = '/login';
    }
    
    throw error;
  }
};
```

---

## 9. DATA VALIDATION RULES

### Product Name
- Required
- String type
- Must be unique within system

### Product Code  
- Optional (auto-generated if not provided)
- String type
- Must be unique if provided

### Prices
- Optional
- Decimal type with 2 decimal places
- Must be positive values

### Stock Quantity
- Required for stock movements
- Decimal type
- Must be greater than 0 for movements

### Movement Types
- Required for stock operations
- Must be one of: `IN`, `OUT`, `TRANSFER`, `ADJUSTMENT`

---

## 10. PAGINATION & FILTERING

All list endpoints support pagination:

```javascript
// Standard pagination parameters
{
  "page": 1,        // Page number (starts from 1)
  "per_page": 50,   // Items per page (max 100)
  "total": 150,     // Total items
  "products": [...] // Current page data
}
```

### Frontend Pagination Helper

```javascript
const usePagination = (fetchFunction) => {
  const [data, setData] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [perPage, setPerPage] = useState(20);
  const [loading, setLoading] = useState(false);

  const fetchData = async (filters = {}) => {
    setLoading(true);
    try {
      const response = await fetchFunction({
        ...filters,
        page,
        per_page: perPage
      });
      
      setData(response.products || response.variants || response.entries);
      setTotal(response.total);
    } catch (error) {
      console.error('Fetch error:', error);
    } finally {
      setLoading(false);
    }
  };

  return {
    data,
    total,
    page,
    perPage,
    loading,
    setPage,
    setPerPage,
    fetchData,
    totalPages: Math.ceil(total / perPage)
  };
};
```

This comprehensive guide should help frontend developers effectively integrate with your Product Management API. The API provides full CRUD operations for products, variants, and stock management with robust filtering and pagination capabilities.
