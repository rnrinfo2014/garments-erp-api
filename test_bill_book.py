#!/usr/bin/env python3
"""
Test script for the new Bill Book functionality
"""

import requests
import json

def test_bill_book_api():
    """Test the bill book API endpoints"""
    
    base_url = 'http://localhost:8000'
    
    print('Testing Bill Book System...')
    print('=' * 50)
    
    try:
        # Test 1: List existing bill books
        print('\n1. Testing bill book listing...')
        response = requests.get(f'{base_url}/bill-books/')
        print(f'   Status Code: {response.status_code}')
        
        if response.status_code == 200:
            print('   ✅ API is accessible')
            data = response.json()
            print(f'   📊 Found {data.get("total", 0)} bill books')
            
            # Show existing bill books
            for book in data.get('bill_books', []):
                print(f'   📚 {book["book_name"]} ({book["book_code"]})')
                print(f'      Tax Type: {book["tax_type"]}')
                print(f'      Prefix: {book["prefix"]}')
                print(f'      Last Bill No: {book["last_bill_no"]}')
                print(f'      Starting Number: {book.get("starting_number", "N/A")}')
                print()
            
            # Test 2: Test bill number generation if we have bill books
            if data.get('bill_books'):
                first_book = data['bill_books'][0]
                book_id = first_book['id']
                
                print(f'2. Testing bill number generation for "{first_book["book_name"]}"...')
                
                # Get next bill number (preview)
                response = requests.get(f'{base_url}/bill-books/{book_id}/next-bill-number')
                if response.status_code == 200:
                    next_data = response.json()
                    print(f'   📋 Next bill number preview: {next_data["next_bill_number"]}')
                    print(f'   📋 Tax type: {next_data["tax_type"]}')
                else:
                    print(f'   ❌ Failed to get next bill number: {response.status_code}')
                
                # Generate and reserve bill number
                response = requests.post(f'{base_url}/bill-books/{book_id}/generate-bill-number')
                if response.status_code == 200:
                    gen_data = response.json()
                    print(f'   🎫 Generated bill number: {gen_data["full_bill_number"]}')
                    print(f'   📝 Tax handling: {gen_data["tax_type_description"]}')
                else:
                    print(f'   ❌ Failed to generate bill number: {response.status_code}')
            
        else:
            print(f'   ❌ API returned status {response.status_code}')
            if response.text:
                print(f'   Error: {response.text}')
                
    except requests.exceptions.ConnectionError:
        print('❌ Could not connect to API')
        print('Make sure the server is running on port 8000')
        print('Start it with: python -m uvicorn main:app --host 0.0.0.0 --port 8000')
        
    except Exception as e:
        print(f'❌ Unexpected error: {e}')

def show_tax_calculation_examples():
    """Show examples of tax calculations for different tax types"""
    
    print('\n' + '=' * 50)
    print('Tax Calculation Examples')
    print('=' * 50)
    
    # Example item
    base_amount = 100.00
    tax_rate = 0.18  # 18% GST
    
    print(f'\nExample item: ₹{base_amount} (base), Tax Rate: {tax_rate*100}%')
    print('-' * 40)
    
    # INCLUDE_TAX example
    print('\n1. INCLUDE_TAX (price includes tax):')
    rate_with_tax = base_amount * (1 + tax_rate)  # ₹118
    rate_without_tax = rate_with_tax / (1 + tax_rate)  # ₹100
    tax_amount = rate_with_tax - rate_without_tax  # ₹18
    
    print(f'   Item rate displayed: ₹{rate_with_tax:.2f}')
    print(f'   Rate without tax: ₹{rate_without_tax:.2f}')
    print(f'   Tax amount: ₹{tax_amount:.2f}')
    print(f'   Total: ₹{rate_with_tax:.2f}')
    
    # EXCLUDE_TAX example
    print('\n2. EXCLUDE_TAX (tax added on top):')
    rate_without_tax = base_amount  # ₹100
    tax_amount = rate_without_tax * tax_rate  # ₹18
    total_amount = rate_without_tax + tax_amount  # ₹118
    
    print(f'   Item rate displayed: ₹{rate_without_tax:.2f}')
    print(f'   Tax amount: ₹{tax_amount:.2f}')
    print(f'   Total: ₹{total_amount:.2f}')
    
    # WITHOUT_TAX example
    print('\n3. WITHOUT_TAX (no tax calculations):')
    final_rate = base_amount  # ₹100
    tax_amount = 0  # ₹0
    
    print(f'   Item rate: ₹{final_rate:.2f}')
    print(f'   Tax amount: ₹{tax_amount:.2f}')
    print(f'   Total: ₹{final_rate:.2f}')

if __name__ == "__main__":
    test_bill_book_api()
    show_tax_calculation_examples()
    
    print('\n' + '=' * 50)
    print('✅ Bill Book system is ready!')
    print('\nNext steps:')
    print('1. Create bill books for different sales types')
    print('2. Update your frontend to use the new tax_type field')
    print('3. Implement the bill number generation in sales flow')
    print('4. Test tax calculations with real data')
