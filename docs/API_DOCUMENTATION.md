# Garments ERP API Documentation

## Base URL
```
http://localhost:8000/api
```

## Authentication
All API endpoints require JWT authentication except for login. Include the JWT token in the Authorization header:
```
Authorization: Bearer <your_jwt_token>
```

## Admin Authentication Required
Some endpoints require admin privileges. These are marked with 🔒 **Admin Only**.

---

## VENDOR API ENDPOINTS

### 1. Get All Vendors
**GET** `/vendors/`

**Response:**
```typescript
{
  message: string;
  data: Array<{
    id: string;
    vendor_id: string;
    vendor_name: string;
    contact_person?: string;
    phone: string;
    email?: string;
    address: string;
    city?: string;
    state?: string;
    pincode?: string;
    gst_number?: string;
    vendor_type: string;
    payment_terms?: string;
    credit_limit?: number;
    acc_code: string; // Account code for vendor payables
    is_active: boolean;
    created_at: string;
    updated_at: string;
  }>;
}
```

### 2. Get Vendor by ID
**GET** `/vendors/{vendor_id}`

**Parameters:**
- `vendor_id` (path): Vendor ID

**Response:** Same as single vendor object from Get All Vendors

### 3. Search Vendors
**GET** `/vendors/search/{search_term}`

**Parameters:**
- `search_term` (path): Search term for vendor name, email, phone, or city

**Response:** Same format as Get All Vendors

### 4. Get Vendors by Status
**GET** `/vendors/status/{status}`

**Parameters:**
- `status` (path): "active" or "inactive"

**Response:** Same format as Get All Vendors

### 5. Create Vendor 🔒 **Admin Only**
**POST** `/vendors/`

**Request Body:**
```typescript
{
  vendor_name: string;
  contact_person?: string;
  phone: string;
  email?: string;
  address: string;
  city?: string;
  state?: string;
  pincode?: string;
  gst_number?: string;
  vendor_type: string;
  payment_terms?: string;
  credit_limit?: number;
  is_active?: boolean; // defaults to true
}
```

**Response:**
```typescript
{
  message: string;
  data: {
    // Same as vendor object with generated fields
    id: string;
    vendor_id: string; // Auto-generated (VND001, VND002, etc.)
    acc_code: string; // Auto-generated account code (2107xxx)
    // ... other fields
  }
}
```

### 6. Update Vendor 🔒 **Admin Only**
**PUT** `/vendors/{vendor_id}`

**Parameters:**
- `vendor_id` (path): Vendor ID

**Request Body:** Same as Create Vendor (all fields optional for update)

**Response:** Same format as Create Vendor

### 7. Delete Vendor 🔒 **Admin Only**
**DELETE** `/vendors/{vendor_id}`

**Parameters:**
- `vendor_id` (path): Vendor ID

**Response:**
```typescript
{
  message: string;
}
```

---

## EMPLOYEE CATEGORY API ENDPOINTS

### 1. Get All Employee Categories
**GET** `/employee-categories/`

**Response:**
```typescript
{
  message: string;
  data: Array<{
    id: string;
    name: string;
    salary_structure: "Monthly" | "Daily" | "Piece-rate";
    base_rate: number;
    description?: string;
    is_active: boolean;
    created_at: string;
    updated_at: string;
  }>;
}
```

### 2. Get Employee Category by ID
**GET** `/employee-categories/{category_id}`

**Parameters:**
- `category_id` (path): Category ID

**Response:** Same as single category object from Get All Categories

### 3. Create Employee Category 🔒 **Admin Only**
**POST** `/employee-categories/`

**Request Body:**
```typescript
{
  name: string;
  salary_structure: "Monthly" | "Daily" | "Piece-rate";
  base_rate: number;
  description?: string;
  is_active?: boolean; // defaults to true
}
```

**Response:**
```typescript
{
  message: string;
  data: {
    // Same as category object with generated ID
    id: string; // Auto-generated
    // ... other fields
  }
}
```

### 4. Update Employee Category 🔒 **Admin Only**
**PUT** `/employee-categories/{category_id}`

**Parameters:**
- `category_id` (path): Category ID

**Request Body:** Same as Create Category (all fields optional for update)

**Response:** Same format as Create Category

### 5. Delete Employee Category 🔒 **Admin Only**
**DELETE** `/employee-categories/{category_id}`

**Parameters:**
- `category_id` (path): Category ID

**Response:**
```typescript
{
  message: string;
}
```

---

## EMPLOYEE API ENDPOINTS

### 1. Get All Employees
**GET** `/employees/`

**Response:**
```typescript
{
  message: string;
  data: Array<{
    id: string;
    employee_id: string;
    name: string;
    category_id: string;
    join_date: string; // ISO date
    phone: string;
    address: string;
    status: "Active" | "Inactive";
    photo_url?: string;
    acc_code: string; // Account code for employee payables
    created_at: string;
    updated_at: string;
    category: {
      id: string;
      name: string;
      salary_structure: "Monthly" | "Daily" | "Piece-rate";
      base_rate: number;
    };
  }>;
}
```

### 2. Get Employee by ID
**GET** `/employees/{employee_id}`

**Parameters:**
- `employee_id` (path): Employee ID

**Response:** Same as single employee object from Get All Employees

### 3. Search Employees
**GET** `/employees/search/{search_term}`

**Parameters:**
- `search_term` (path): Search term for employee name, phone, or employee_id

**Response:** Same format as Get All Employees

### 4. Get Employees by Status
**GET** `/employees/status/{status}`

**Parameters:**
- `status` (path): "active" or "inactive"

**Response:** Same format as Get All Employees

### 5. Get Employees by Category
**GET** `/employees/category/{category_id}`

**Parameters:**
- `category_id` (path): Category ID

**Response:** Same format as Get All Employees

### 6. Create Employee 🔒 **Admin Only**
**POST** `/employees/`

**Request Body:**
```typescript
{
  name: string;
  category_id: string;
  join_date: string; // ISO date format: "2024-01-15"
  phone: string;
  address: string;
  status?: "Active" | "Inactive"; // defaults to "Active"
  photo_url?: string;
}
```

**Response:**
```typescript
{
  message: string;
  data: {
    // Same as employee object with generated fields
    id: string; // Auto-generated
    employee_id: string; // Auto-generated (EMP-001, EMP-002, etc.)
    acc_code: string; // Auto-generated account code (2108xxx)
    // ... other fields
    category: {
      // Category details
    }
  }
}
```

### 7. Update Employee 🔒 **Admin Only**
**PUT** `/employees/{employee_id}`

**Parameters:**
- `employee_id` (path): Employee ID

**Request Body:** Same as Create Employee (all fields optional for update)

**Response:** Same format as Create Employee

### 8. Delete Employee 🔒 **Admin Only**
**DELETE** `/employees/{employee_id}`

**Parameters:**
- `employee_id` (path): Employee ID

**Response:**
```typescript
{
  message: string;
}
```

---

## AUTHENTICATION ENDPOINTS

### Login
**POST** `/login`

**Request Body:**
```typescript
{
  username: string;
  password: string;
}
```

**Response:**
```typescript
{
  access_token: string;
  token_type: "bearer";
  user_id: string;
  username: string;
  role: string;
}
```

---

## ERROR RESPONSES

### Standard Error Format
```typescript
{
  detail: string; // Error message
}
```

### Common HTTP Status Codes
- `200 OK` - Success
- `201 Created` - Resource created successfully  
- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Authentication required or invalid
- `403 Forbidden` - Insufficient permissions (admin required)
- `404 Not Found` - Resource not found
- `422 Unprocessable Entity` - Validation errors
- `500 Internal Server Error` - Server error

---

## AUTOMATIC ACCOUNT CREATION

### Account Code Patterns
When creating vendors, customers, suppliers, or employees, payable/receivable accounts are automatically created:

- **Customers**: `1301xxx` (Accounts Receivable)
- **Suppliers**: `2106xxx` (Supplier Payables) 
- **Vendors**: `2107xxx` (Vendor Payables)
- **Employees**: `2108xxx` (Employee Payables)

The `acc_code` field in the response contains the automatically generated account code that can be used for accounting transactions.

---

## USAGE EXAMPLES

### Creating an Employee with TypeScript/JavaScript

```typescript
// Login first
const loginResponse = await fetch('http://localhost:8000/api/login', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    username: 'superadmin',
    password: 'admin123'
  })
});
const authData = await loginResponse.json();
const token = authData.access_token;

// Create employee
const employeeResponse = await fetch('http://localhost:8000/api/employees/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    name: 'John Doe',
    category_id: 'MGMT001', // Use actual category ID
    join_date: '2024-01-15',
    phone: '1234567890',
    address: '123 Main St, City, State',
    status: 'Active'
  })
});
const employeeData = await employeeResponse.json();
console.log('Created employee with account:', employeeData.data.acc_code);
```

### Getting All Employees
```typescript
const response = await fetch('http://localhost:8000/api/employees/', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});
const data = await response.json();
console.log('Employees:', data.data);
```

---

## API TESTING

You can test these APIs using:

1. **Swagger UI**: http://localhost:8000/docs
2. **Postman**: Import the OpenAPI spec from http://localhost:8000/openapi.json
3. **curl**: Command line testing
4. **Frontend applications**: React, Vue, Angular, etc.

The server is currently running and ready to handle requests!
