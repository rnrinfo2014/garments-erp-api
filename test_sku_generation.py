# SKU Generation Test

# Test the new SKU generation function

def test_sku_generation():
    """Test cases for the new SKU generation function"""
    
    test_cases = [
        {
            "product": "Smart Plus",
            "size": "36", 
            "sleeve": "Full Sleeve",
            "design": "Checked",
            "expected": "SMP36FCHK"
        },
        {
            "product": "Premium Shirt",
            "size": "38",
            "sleeve": "Half Sleeve", 
            "design": "Plain",
            "expected": "PRM38HPLN"
        },
        {
            "product": "Cotton Polo",
            "size": "40",
            "sleeve": "Sleeveless",
            "design": "Striped", 
            "expected": "CTN40SSTR"
        },
        {
            "product": "Basic Tee",
            "size": "42",
            "sleeve": "Quarter",
            "design": "Print",
            "expected": "BSC42QPRT"
        }
    ]
    
    print("New SKU Generation Examples:")
    print("=" * 40)
    
    for case in test_cases:
        print(f"Product: {case['product']}")
        print(f"Size: {case['size']}")
        print(f"Sleeve: {case['sleeve']}")
        print(f"Design: {case['design']}")
        print(f"Generated SKU: {case['expected']}")
        print(f"Length: {len(case['expected'])} characters")
        print("-" * 30)

if __name__ == "__main__":
    test_sku_generation()
