#!/bin/bash
# Clear Python cache files
# Run this after modifying function signatures, class constructors, or imports

echo "🧹 Clearing Python cache..."

# Remove __pycache__ directories
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null

# Remove .pyc files
find . -name "*.pyc" -delete 2>/dev/null

# Remove .pyo files (optimized bytecode)
find . -name "*.pyo" -delete 2>/dev/null

# Remove .pyd files (Windows compiled Python files, just in case)
find . -name "*.pyd" -delete 2>/dev/null

echo "✅ Python cache cleared!"
echo ""
echo "💡 Tip: Run this script whenever you:"
echo "   - Modify function signatures"
echo "   - Change class constructors (__init__)"
echo "   - Reorganize imports"
echo "   - See 'unexpected keyword argument' errors"
echo ""
echo "To use: ./clear_cache.sh"
