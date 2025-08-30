# Bill Book Management System Documentation

## Overview

The Bill Book system in your Garments ERP manages sales bill numbering, tax handling, and bill sequencing. Each bill book acts as a "register" that determines how sales bills are numbered and how taxes are calculated.

## Key Features

### 1. Tax Types
The system supports three tax handling modes:

- **INCLUDE_TAX**: Tax is included in item rates. The system will separate the tax amount during calculation.
- **EXCLUDE_TAX**: Tax is calculated and added on top of item rates.
- **WITHOUT_TAX**: No tax calculations are performed.

### 2. Automatic Bill Numbering
Each bill book maintains its own sequence of bill numbers with:
- Custom prefix (e.g., "INV", "BILL", "SLS")
- Starting number (default: 1)
- Auto-incrementing counter
- Format: `{prefix}{number:04d}` (e.g., INV0001, INV0002, etc.)

## API Endpoints

### Bill Book Management

#### Create Bill Book
```http
POST /bill-books/
```

**Request Body:**
```json
{
  "book_name": "Tax Invoice Book",
  "book_code": "TAX_INV",
  "prefix": "INV",
  "tax_type": "INCLUDE_TAX",
  "starting_number": 1,
  "status": "ACTIVE"
}
```

#### List Bill Books
```http
GET /bill-books/?page=1&per_page=10&tax_type=INCLUDE_TAX
```

**Query Parameters:**
- `search`: Search in book name or code
- `status`: Filter by status (ACTIVE, INACTIVE, CLOSED)
- `tax_type`: Filter by tax type
- `page`: Page number
- `per_page`: Items per page

#### Get Bill Book Details
```http
GET /bill-books/{bill_book_id}
```

#### Update Bill Book
```http
PUT /bill-books/{bill_book_id}
```

### Bill Number Generation

#### Get Next Bill Number (Preview)
```http
GET /bill-books/{bill_book_id}/next-bill-number
```

**Response:**
```json
{
  "bill_book_id": 1,
  "bill_book_name": "Tax Invoice Book",
  "prefix": "INV",
  "next_number": 5,
  "next_bill_number": "INV0005",
  "tax_type": "INCLUDE_TAX",
  "current_last_bill_no": 4
}
```

#### Generate and Reserve Bill Number
```http
POST /bill-books/{bill_book_id}/generate-bill-number
```

**Response:**
```json
{
  "bill_book_id": 1,
  "bill_book_name": "Tax Invoice Book",
  "prefix": "INV",
  "bill_number": 5,
  "full_bill_number": "INV0005",
  "tax_type": "INCLUDE_TAX",
  "tax_type_description": "Tax is included in item rates - will be separated during calculation"
}
```

## Sales Integration Workflow

### 1. Creating a Sales Bill

When creating a sales bill, follow this workflow:

1. **Select Bill Book**: User selects which bill book to use
2. **Generate Bill Number**: Call the generate bill number API
3. **Create Sales Record**: Use the generated bill number and bill book details
4. **Handle Tax Calculation**: Apply tax logic based on bill book's tax_type

### 2. Tax Calculation Logic

Based on the bill book's `tax_type`:

#### INCLUDE_TAX
```javascript
// Item rate includes tax, separate it
const taxRate = 0.18; // 18% GST
const rateWithTax = 118.00;
const rateWithoutTax = rateWithTax / (1 + taxRate);
const taxAmount = rateWithTax - rateWithoutTax;

// Example: ₹118 becomes ₹100 + ₹18 tax
```

#### EXCLUDE_TAX
```javascript
// Add tax on top of item rate
const taxRate = 0.18; // 18% GST
const rateWithoutTax = 100.00;
const taxAmount = rateWithoutTax * taxRate;
const totalRate = rateWithoutTax + taxAmount;

// Example: ₹100 + ₹18 tax = ₹118 total
```

#### WITHOUT_TAX
```javascript
// No tax calculations
const finalRate = itemRate;
const taxAmount = 0;
```

## Frontend Integration Examples

### React Component Example

```jsx
import React, { useState, useEffect } from 'react';

const SalesForm = () => {
  const [billBooks, setBillBooks] = useState([]);
  const [selectedBillBook, setSelectedBillBook] = useState(null);
  const [billNumber, setBillNumber] = useState('');

  // Load available bill books
  useEffect(() => {
    fetch('/api/bill-books/?status=ACTIVE')
      .then(res => res.json())
      .then(data => setBillBooks(data.bill_books));
  }, []);

  // Generate bill number when bill book is selected
  const handleBillBookChange = async (billBookId) => {
    const billBook = billBooks.find(b => b.id === billBookId);
    setSelectedBillBook(billBook);
    
    // Generate bill number
    const response = await fetch(`/api/bill-books/${billBookId}/generate-bill-number`, {
      method: 'POST'
    });
    const data = await response.json();
    setBillNumber(data.full_bill_number);
  };

  // Calculate tax based on bill book tax type
  const calculateItemTotal = (rate, quantity, taxRate = 0.18) => {
    const baseAmount = rate * quantity;
    
    switch (selectedBillBook?.tax_type) {
      case 'INCLUDE_TAX':
        const amountWithoutTax = baseAmount / (1 + taxRate);
        return {
          baseAmount: amountWithoutTax,
          taxAmount: baseAmount - amountWithoutTax,
          totalAmount: baseAmount
        };
        
      case 'EXCLUDE_TAX':
        const taxAmount = baseAmount * taxRate;
        return {
          baseAmount: baseAmount,
          taxAmount: taxAmount,
          totalAmount: baseAmount + taxAmount
        };
        
      case 'WITHOUT_TAX':
        return {
          baseAmount: baseAmount,
          taxAmount: 0,
          totalAmount: baseAmount
        };
        
      default:
        return { baseAmount, taxAmount: 0, totalAmount: baseAmount };
    }
  };

  return (
    <form>
      <div>
        <label>Bill Book:</label>
        <select onChange={(e) => handleBillBookChange(e.target.value)}>
          <option value="">Select Bill Book</option>
          {billBooks.map(book => (
            <option key={book.id} value={book.id}>
              {book.book_name} ({book.tax_type})
            </option>
          ))}
        </select>
      </div>
      
      <div>
        <label>Bill Number:</label>
        <input type="text" value={billNumber} readOnly />
      </div>
      
      {selectedBillBook && (
        <div className="tax-info">
          <p>Tax Type: {selectedBillBook.tax_type}</p>
          {selectedBillBook.tax_type === 'INCLUDE_TAX' && (
            <small>Item rates include tax. Tax will be separated automatically.</small>
          )}
          {selectedBillBook.tax_type === 'EXCLUDE_TAX' && (
            <small>Tax will be added on top of item rates.</small>
          )}
          {selectedBillBook.tax_type === 'WITHOUT_TAX' && (
            <small>No tax calculations will be performed.</small>
          )}
        </div>
      )}
      
      {/* Rest of the sales form */}
    </form>
  );
};
```

## Database Schema

### bill_books table
```sql
CREATE TABLE bill_books (
    id SERIAL PRIMARY KEY,
    book_name VARCHAR(100) NOT NULL,
    book_code VARCHAR(20) UNIQUE NOT NULL,
    prefix VARCHAR(20) NOT NULL,
    tax_type taxtype NOT NULL DEFAULT 'INCLUDE_TAX',
    last_bill_no INTEGER DEFAULT 0,
    starting_number INTEGER DEFAULT 1,
    status billbookstatus DEFAULT 'ACTIVE',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### sales table (updated)
```sql
ALTER TABLE sales ADD COLUMN bill_book_id INTEGER;
ALTER TABLE sales ADD CONSTRAINT fk_sales_bill_book 
    FOREIGN KEY (bill_book_id) REFERENCES bill_books(id);
```

## Migration Instructions

1. **Backup your database** before running the migration
2. **Run the migration script**:
   ```bash
   python migrate_bill_book_tax_types.py
   ```
3. **Test the new functionality** with sample data
4. **Update your frontend** to use the new tax_type field
5. **Remove old columns** (optional, after testing):
   ```sql
   ALTER TABLE bill_books DROP COLUMN with_tax;
   ALTER TABLE bill_books DROP COLUMN without_tax;
   ```

## Common Use Cases

### 1. Regular Sales (Tax Inclusive)
- Bill Book: "Regular Sales"
- Tax Type: INCLUDE_TAX
- Prefix: "RS"
- Use Case: Retail sales where displayed prices include tax

### 2. B2B Sales (Tax Exclusive)
- Bill Book: "B2B Sales"
- Tax Type: EXCLUDE_TAX
- Prefix: "B2B"
- Use Case: Business-to-business sales where tax is added separately

### 3. Export Sales (No Tax)
- Bill Book: "Export Sales"
- Tax Type: WITHOUT_TAX
- Prefix: "EXP"
- Use Case: Export orders with no domestic tax

## Best Practices

1. **Always select bill book first** before generating bill numbers
2. **Handle tax calculations consistently** based on bill book tax type
3. **Validate bill book status** before use (must be ACTIVE)
4. **Use preview endpoint** to show next bill number without reserving it
5. **Reserve bill numbers only when needed** to avoid gaps in sequence
6. **Implement proper error handling** for bill number generation failures

## Troubleshooting

### Bill Number Gaps
If bill numbers have gaps, check for:
- Failed transactions after bill number generation
- Multiple calls to generate-bill-number without saving sales record

### Tax Calculation Issues
- Verify bill book tax_type is set correctly
- Check tax rate configuration in your business logic
- Ensure consistent rounding rules

### Performance Considerations
- Index bill_book_id in sales table for better query performance
- Consider archiving old bill books instead of deleting them
- Monitor bill number sequence for unusually high values
