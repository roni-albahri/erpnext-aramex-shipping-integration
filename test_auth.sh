#!/bin/bash

# Test GitHub Authentication
echo "=== Testing GitHub Authentication ==="
echo ""

# Test main workspace
echo "📁 Testing Main Workspace..."
cd /project/sandbox/user-workspace
git fetch --dry-run 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ Main workspace authentication working"
else
    echo "❌ Main workspace authentication failed"
    echo "   Run: git push origin main"
    echo "   Use your PAT when prompted for password"
fi

# Test ERPNext Aramex Shipping
echo ""
echo "📁 Testing ERPNext Aramex Shipping..."
cd /project/sandbox/user-workspace/erpnext_aramex_shipping
git fetch --dry-run 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ ERPNext Aramex Shipping authentication working"
else
    echo "❌ ERPNext Aramex Shipping authentication failed"
    echo "   Run: git push origin main"
    echo "   Use your PAT when prompted for password"
fi

echo ""
echo "=== Test Complete ==="
echo "If authentication fails, follow the steps in AUTHENTICATION_SETUP.md"
