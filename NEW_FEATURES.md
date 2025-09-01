# 🚀 ChatR: Enhanced Features & User Guide
**Version: 0.2.0** | **Last Updated: September 1, 2025**

## 📋 Table of Contents
1. [Quick Start](#-quick-start)
2. [New Features](#-new-features)
3. [Installation Guide](#-installation-guide)
4. [Usage Examples](#-usage-examples)
5. [MCP Integration](#-mcp-integration)
6. [Troubleshooting](#-troubleshooting)

---

## 🚀 Quick Start

### For R Users (Recommended)
```r
# 1. Install from GitHub (one command)
source("https://raw.githubusercontent.com/freedom12321/chatR-GSOC/main/install_chatr.R")
install_chatr()

# 2. Use immediately
library(chatr)
chatr("How do I create a linear regression?")
chatr_repl()  # Start interactive chat
```

### For CLI Users  
```bash
# 1. Clone and install
git clone https://github.com/freedom12321/chatR-GSOC.git
cd chatR-GSOC
pip install -e .

# 2. Initialize and use
chatr init
chatr serve --port 8001  # Start main server
chatr mcp --port 8002    # Start MCP server
```

---

## ✨ New Features

### 1. 💬 Interactive Chat/REPL Interface
**Real-time R programming assistance in your console!**

```r
# Start interactive session
chatr_repl()

# Quick alias
chatr_chat()
```

**Features:**
- ✅ **Interactive REPL**: Ask questions, get contextual answers
- ✅ **Built-in Commands**: `/help`, `/clear`, `/history`, `/status`, `/quit`
- ✅ **Context Memory**: Remembers conversation history
- ✅ **Auto Server Start**: No manual backend setup needed
- ✅ **Rich Output**: Colored terminal interface

**Example Session:**
```
=== ChatR Interactive REPL ===
Connected to: http://localhost:8001
Ready! Ask me anything about R...

> How do I create a scatter plot with ggplot2?
ChatR: Use ggplot(data, aes(x = var1, y = var2)) + geom_point()

> How do I add colors by group?
ChatR: Add aes(color = group_variable) to your ggplot() call

> /quit
Thanks for using ChatR REPL! Goodbye!
```

### 2. 🤖 MCP Endpoints for AI Frameworks
**Integrate ChatR with Cursor, Copilot, and custom agents!**

**Server Details:**
- **Main ChatR**: `http://localhost:8001` (CLI/R package)
- **MCP Server**: `http://localhost:8002` (agentic frameworks)

**Available Tools:**
| Tool | Description | Example Use |
|------|-------------|-------------|
| `r_execute` | Run R code safely | Execute data analysis scripts |
| `r_help` | Get function docs | Look up function parameters |
| `r_search` | Search R documentation | Find relevant functions |
| `r_explain` | AI concept explanation | Understand R concepts |
| `r_package_info` | Package information | Explore package functions |
| `r_vignettes` | Package tutorials | Access learning materials |

### 3. 🔧 Enhanced R Documentation Indexing  
**Improved knowledge base with 100+ R functions indexed**

- ✅ **120+ Functions**: From `stats`, `base`, `utils`, `graphics` packages
- ✅ **Enhanced Descriptions**: Function signatures and arguments
- ✅ **Better Performance**: Faster documentation lookup
- ✅ **Context-Aware**: Links to related functions

---

## 📦 Installation Guide

### Method 1: R Users (Complete Setup)
```r
# Automatic installation (handles both R package + Python backend)
source("https://raw.githubusercontent.com/freedom12321/chatR-GSOC/main/install_chatr.R")
install_chatr()

# Verify installation
library(chatr)
?chatr  # Should show help documentation
```

### Method 2: Manual Installation
```bash
# 1. Clone repository
git clone https://github.com/freedom12321/chatR-GSOC.git
cd chatR-GSOC

# 2. Install Python components
pip install -e .

# 3. Install R package
R -e "devtools::install('r_package/')"

# 4. Initialize (first-time only)  
chatr init
```

### Method 3: Development Setup
```bash
# For contributors
git clone https://github.com/freedom12321/chatR-GSOC.git
cd chatR-GSOC
./quick_setup.sh
```

---

## 💡 Usage Examples

### Basic R Package Usage
```r
library(chatr)

# Ask questions
chatr("How do I read a CSV file with custom headers?")

# Get function help
help_explain("lm")

# Analyze data
data(mtcars)
chatr_analyze("mtcars")

# Interactive chat
chatr_repl()
```

### CLI Usage
```bash
# Direct questions
chatr chat "How do I create a boxplot in R?"

# Interactive mode
chatr chat --interactive

# Server management
chatr serve --port 8001
chatr status
```

### Advanced Features
```r
# Code analysis
analyze_code("
  data <- read.csv('file.csv')
  plot(data$x, data$y)
")

# Data analysis with AI suggestions
chatr_analysis_tips("exploratory")
```

---

## 🔌 MCP Integration

### Start MCP Server
```bash
# Start on separate port (doesn't interfere with main ChatR)
chatr mcp --port 8002
```

### Integration Examples

#### Cursor IDE
```json
// Add to Cursor configuration
{
  "mcp_servers": {
    "chatr": {
      "url": "http://localhost:8002/mcp/",
      "tools": ["r_execute", "r_help", "r_search"]
    }
  }
}
```

#### Custom Python Script
```python
import requests

# Execute R code
def run_r(code):
    response = requests.post(
        "http://localhost:8002/mcp/execute",
        json={"tool": "r_execute", "parameters": {"code": code}}
    )
    return response.json()["result"]["stdout"]

# Get R help
def get_r_help(func):
    response = requests.post(
        "http://localhost:8002/mcp/execute", 
        json={"tool": "r_help", "parameters": {"function_name": func}}
    )
    return response.json()["result"]["help_content"]

# Usage
result = run_r("mean(c(1,2,3,4,5))")  # "3"
help_text = get_r_help("lm")
```

#### JavaScript/Web Integration
```javascript
async function askChatR(query) {
    const response = await fetch('http://localhost:8002/mcp/execute', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            tool: 'r_explain',
            parameters: {query: query}
        })
    });
    
    const result = await response.json();
    return result.result.explanation;
}
```

### Test MCP Integration
```bash
# Health check
curl http://localhost:8002/mcp/health

# List tools
curl http://localhost:8002/mcp/tools

# Execute R code
curl -X POST http://localhost:8002/mcp/execute \
  -H "Content-Type: application/json" \
  -d '{"tool": "r_execute", "parameters": {"code": "summary(mtcars)"}}'
```

---

## 🔧 Troubleshooting

### Common Issues

#### R Package Issues
```r
# If chatr_repl() not found
library(chatr)
?chatr_repl  # Check if function is loaded

# Reinstall if needed
source("install_chatr.R")
install_chatr()
```

#### Server Connection Issues
```bash
# Check server status
chatr status

# Restart server
chatr serve --port 8001

# Check if port is in use
lsof -i :8001
```

#### MCP Server Issues
```bash
# Start MCP server separately
chatr mcp --port 8002

# Test MCP endpoints
curl http://localhost:8002/mcp/health
```

### System Requirements
- **R**: Version 3.5.0 or higher
- **Python**: Version 3.8 or higher  
- **Ollama**: For local LLM (auto-installed)
- **Memory**: 4GB RAM minimum (8GB recommended)

---

## 🎯 Key Benefits

### For R Users
✅ **Interactive Learning**: Ask questions while coding  
✅ **Instant Help**: No need to search documentation  
✅ **Context Aware**: Understands your data and workflow  
✅ **Offline Capable**: Works without internet  

### For Developers  
✅ **MCP Integration**: Works with modern AI tools  
✅ **API Access**: REST endpoints for custom integrations  
✅ **Local & Secure**: No data leaves your machine  
✅ **Open Source**: Fully transparent and customizable  

### For Organizations
✅ **No API Keys**: No external service dependencies  
✅ **Private & Secure**: Runs entirely locally  
✅ **Cost Effective**: No usage-based pricing  
✅ **Production Ready**: Stable and well-tested  

---

## 🚀 Getting Help

- **R Help**: `?chatr` or `help(package = "chatr")`
- **CLI Help**: `chatr --help`
- **GitHub Issues**: [Report bugs or request features](https://github.com/freedom12321/chatR-GSOC/issues)
- **Documentation**: Check the `/docs` folder for detailed guides

---

**Ready to supercharge your R programming with AI assistance? Start with `chatr_repl()` and explore the possibilities!** 🎉

*Last updated: September 1, 2025*