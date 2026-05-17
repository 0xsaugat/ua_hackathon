#!/usr/bin/env python3
"""
Test suite for email validation rules.
"""
from validators import validate_email_address

print("=" * 80)
print("Email Validation Rules Test Suite")
print("=" * 80)

# Test cases: (email, should_be_valid, rule_description)
test_cases = [
    # VALID cases
    ("user@example.com", True, "Basic ASCII email"),
    ("राम@नेपाल.नेपाल", True, "Nepali IDN email"),
    ("josé@españa.es", True, "Spanish IDN email"),
    ("mailbox9@क्यान.संगठन", True, "Nepali variant domain"),
    ("test.user@example.co.uk", True, "Dot in local part (allowed in middle)"),
    ("user+tag@example.com", True, "Plus sign in local part"),
    ("user_name@example.com", True, "Underscore in local part"),
    ("user-name@example.com", True, "Hyphen in local part"),
    
    # INVALID: Missing @ symbol
    ("userexample.com", False, "Missing @ symbol"),
    
    # INVALID: Multiple @ symbols
    ("user@@example.com", False, "Double @ symbol"),
    ("user@exam@ple.com", False, "Multiple @ symbols"),
    
    # INVALID: Local part starts with dot
    (".user@example.com", False, "Local part starts with dot"),
    
    # INVALID: Local part ends with dot
    ("user.@example.com", False, "Local part ends with dot"),
    
    # INVALID: Domain ends with dot
    ("user@example.com.", False, "Domain ends with dot"),
    
    # INVALID: Consecutive dots
    ("user..name@example.com", False, "Consecutive dots in local part"),
    ("user@example..com", False, "Consecutive dots in domain"),
    
    # INVALID: Domain without TLD
    ("user@localhost", False, "Domain without dot/TLD"),
    ("user@example", False, "Domain without TLD"),
    
    # INVALID: Spaces
    ("user name@example.com", False, "Space in local part"),
    ("user@exam ple.com", False, "Space in domain"),
    
    # INVALID: Empty local part
    ("@example.com", False, "Empty local part"),
    
    # INVALID: Empty domain
    ("user@", False, "Empty domain"),
    
    # INVALID: Dot right after @
    ("user@.example.com", False, "Domain starts with dot"),
]

passed = 0
failed = 0

for email, should_be_valid, description in test_cases:
    result = validate_email_address(email)
    
    # Check if result matches expectation
    is_correct = result.valid == should_be_valid
    
    status = "✓ PASS" if is_correct else "✗ FAIL"
    expected = "VALID" if should_be_valid else "INVALID"
    actual = "VALID" if result.valid else "INVALID"
    
    print(f"\n{status}")
    print(f"  Rule: {description}")
    print(f"  Email: {email}")
    print(f"  Expected: {expected} | Actual: {actual}")
    
    if not is_correct:
        print(f"  Error: {result.error_message}")
        failed += 1
    else:
        passed += 1

print("\n" + "=" * 80)
print(f"Results: {passed} passed, {failed} failed out of {len(test_cases)} tests")
print("=" * 80)

if failed == 0:
    print("✓ All validation rules verified!")
else:
    print(f"✗ {failed} test(s) failed")
