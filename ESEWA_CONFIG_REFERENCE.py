# eSewa Configuration Reference
# This file shows how to configure eSewa for different environments

# ============================================
# TEST/SANDBOX ENVIRONMENT (CURRENT)
# ============================================
# Used for development and testing
# URL: https://uat.esewa.com.np

TEST_CONFIG = {
    'MERCHANT_CODE': 'EPAYTEST',
    'MERCHANT_SECRET_KEY': '',  # Empty for test or use provided test secret
    'INITIATE_URL': 'https://uat.esewa.com.np/epay/initiate',
    'VERIFY_URL': 'https://uat.esewa.com.np/api/verification',
    'RETURN_URL': 'http://localhost:8000/membership/esewa-callback/',
    'SUCCESS_URL': 'http://localhost:8000/membership/esewa-success/',
    'FAILURE_URL': 'http://localhost:8000/membership/esewa-failure/',
}

# ============================================
# PRODUCTION ENVIRONMENT
# ============================================
# Used for live transactions
# URL: https://esewa.com.np

PRODUCTION_CONFIG = {
    'MERCHANT_CODE': 'YOUR_PRODUCTION_MERCHANT_CODE',  # Get from eSewa
    'MERCHANT_SECRET_KEY': 'YOUR_PRODUCTION_SECRET_KEY',  # Keep secret!
    'INITIATE_URL': 'https://esewa.com.np/epay/initiate',
    'VERIFY_URL': 'https://esewa.com.np/api/verification',
    'RETURN_URL': 'https://yourdomain.com/membership/esewa-callback/',
    'SUCCESS_URL': 'https://yourdomain.com/membership/esewa-success/',
    'FAILURE_URL': 'https://yourdomain.com/membership/esewa-failure/',
}

# ============================================
# How to Update Configuration
# ============================================

# Option 1: Direct Update (Simple, for development)
# Edit membership/esewa.py:
#
# class EsewaConfig:
#     MERCHANT_CODE = 'YOUR_CODE'
#     MERCHANT_SECRET_KEY = 'YOUR_SECRET'
#     INITIATE_URL = 'https://...'
#     # etc...

# Option 2: Environment Variables (Recommended for production)
# Add to your .env file:
#
# ESEWA_MERCHANT_CODE=YOUR_CODE
# ESEWA_SECRET_KEY=YOUR_SECRET
# ESEWA_ENV=production  # or 'test'

# Option 3: Django Settings
# Add to trainwise/settings.py:
#
# ESEWA_CONFIG = {
#     'MERCHANT_CODE': os.getenv('ESEWA_MERCHANT_CODE', 'EPAYTEST'),
#     'MERCHANT_SECRET_KEY': os.getenv('ESEWA_SECRET_KEY', ''),
#     # ...
# }

# ============================================
# Test Account Information
# ============================================

# eSewa provides test credentials for development
# Visit: https://uat.esewa.com.np
#
# Test Merchant Code: EPAYTEST
# Test User Email: test@esewa.com.np  (or create your own)
# Test Amount: Any amount
# Test Product Code: TRAINWISE (already set)

# ============================================
# Important Security Notes
# ============================================

# 1. NEVER commit MERCHANT_SECRET_KEY to version control
# 2. Use environment variables in production
# 3. Keep SECRET_KEY secure and rotate periodically
# 4. Always use HTTPS in production
# 5. Verify all eSewa responses server-side
# 6. Log all transactions for audit trail

# ============================================
# Migration from Test to Production
# ============================================

# Step 1: Get Production Credentials
# - Contact eSewa for merchant account
# - Receive MERCHANT_CODE and SECRET_KEY
# - Get production URL access

# Step 2: Update Configuration
# - Update MERCHANT_CODE
# - Update MERCHANT_SECRET_KEY
# - Change INITIATE_URL to production
# - Change VERIFY_URL to production
# - Update callback URLs to your domain

# Step 3: Test Thoroughly
# - Test payment flow end-to-end
# - Verify success/failure handling
# - Check transaction logs
# - Monitor for errors

# Step 4: Deploy
# - Deploy updated code
# - Verify configuration in production
# - Monitor first transactions closely
# - Have rollback plan ready

# ============================================
# eSewa Test Credentials (Common)
# ============================================

# Default Test Merchant:
# Code: EPAYTEST
# Name: Test Merchant

# You can create test accounts at:
# https://uat.esewa.com.np

# Test Payment Flow:
# 1. Amount: Any amount (e.g., ₹100)
# 2. Merchant: EPAYTEST
# 3. Product: TRAINWISE (or your product code)
# 4. Signature: Generated if SECRET_KEY provided

# ============================================
# Troubleshooting Checklist
# ============================================

# [ ] Merchant code is correct
# [ ] Using correct environment URL (test vs production)
# [ ] Callback URLs are accessible from eSewa servers
# [ ] Firewall allows outbound HTTPS requests
# [ ] eSewa account is active and verified
# [ ] Test amount is sufficient (for test account)
# [ ] Transaction UUID is unique for each payment
# [ ] Payment status is being verified correctly
# [ ] Database migration was applied
# [ ] Django settings are correct
# [ ] Logs are being generated (check django logs)

# ============================================
# Sample Payment Verification Flow
# ============================================

# When user completes eSewa payment:
#
# 1. eSewa redirects to: /membership/esewa-callback/
#    with parameters: status, transaction_uuid, product_code, etc.
#
# 2. System retrieves Payment record using transaction_uuid
#
# 3. Status check:
#    - COMPLETE: Mark as 'Paid', activate subscription
#    - PENDING: Mark as 'Pending', check later
#    - FAILED/Other: Mark as 'Failed', keep subscription inactive
#
# 4. Update database and display result to user
#
# 5. Log transaction for audit trail

# ============================================
# Contact & Support
# ============================================

# eSewa Support: support@esewa.com.np
# eSewa Website: https://esewa.com.np
# Documentation: https://django-tutorial.dev/course/payment-integration/esewa-integration/
# Our Support: Check app documentation or contact admin

print("""
╔════════════════════════════════════════════════════════════╗
║         eSewa Configuration Reference Guide               ║
║                                                            ║
║  Current Status: TEST/SANDBOX MODE (EPAYTEST)            ║
║  Environment: https://uat.esewa.com.np                   ║
║  Ready for development and testing                        ║
║════════════════════════════════════════════════════════════╝
""")
