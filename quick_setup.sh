#!/bin/bash

# ChatR Quick Setup Script
# Run this to set up ChatR for first-time use

set -e  # Exit on any error

echo "🚀 Setting up ChatR..."

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

echo "📁 Working directory: $SCRIPT_DIR"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Check R
if ! command -v R &> /dev/null; then
    echo "⚠️  R is recommended but not found. Install R for full functionality."
    echo "   Download from: https://cran.r-project.org/"
else
    echo "✅ R found: $(R --version | head -1)"
fi

# Activate virtual environment
if [ -d "venv" ]; then
    echo "📦 Activating existing virtual environment..."
    source venv/bin/activate
else
    echo "📦 Creating new virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
fi

# Install dependencies
echo "📥 Installing Python dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Install ChatR in development mode
echo "🔧 Installing ChatR..."
pip install -q -e .

# Test installation
echo "🧪 Testing installation..."
if python -c "import chatr; print('✅ ChatR Python package imported successfully')" 2>/dev/null; then
    echo "✅ ChatR installation successful"
else
    echo "❌ ChatR installation failed"
    exit 1
fi

# Test CLI
if python -m chatr --help > /dev/null 2>&1; then
    echo "✅ ChatR CLI working"
else
    echo "❌ ChatR CLI failed"
    exit 1
fi

# Check Ollama (optional)
if command -v ollama &> /dev/null; then
    echo "✅ Ollama found"
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo "✅ Ollama server running"
    else
        echo "⚠️  Ollama server not running. Start with: ollama serve"
    fi
else
    echo "⚠️  Ollama not found. Install from: https://ollama.ai"
fi

echo ""
echo "🎉 ChatR setup complete!"
echo ""
echo "📚 Next steps:"
echo "   1. Activate environment: source venv/bin/activate"
echo "   2. Start server: chatr serve &"
echo "   3. Try CLI: python -m chatr chat --interactive"
echo "   4. See CLI_GUIDE.md for CLI usage"
echo "   5. See R_GUIDE.md for R package usage"
echo ""
echo "💡 Tip: Add this to your shell profile for quick access:"
echo "   alias chatr-env='cd $SCRIPT_DIR && source venv/bin/activate'"