# ChatR Setup Guide

Complete installation and setup instructions for ChatR - your local AI assistant for R programming.


## 📋 Prerequisites

### Required
- **Python 3.8+** - For CLI and backend
- **R 4.0+** - For R package integration
- **Ollama** - For local LLM inference (auto-installed)

### System Requirements
- **RAM**: 4GB+ (2GB for model, 2GB for system)
- **Storage**: 3GB+ (model + cache)
- **OS**: Linux, macOS, Windows

---

## 🔧 Detailed Installation

### Step 1: Clone Repository
```bash
git clone https://github.com/your-org/chatR-GSOC.git
cd chatR-GSOC
```

### Step 2: Python Setup
```bash
# Create virtual environment
python -m venv venv

# Activate environment
source venv/bin/activate          # Linux/Mac
# venv\Scripts\activate           # Windows

# Install ChatR
pip install -e .
```

### Step 3: Ollama Setup
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh    # Linux/Mac
# winget install Ollama.Ollama                  # Windows

# Pull the model
ollama pull llama3.2:3b-instruct
```

### Step 4: Initialize ChatR
```bash
chatr init
```

### Step 5: R Package (Optional)
```r
# Install R package
devtools::install("r_package")

# Or use the complete installation script
source("install_chatr.R")
install_chatr()
```

---

## ✅ Verification

### Test CLI
```bash
# Check status
chatr status

# Test basic query  
chatr chat "How do I load a CSV file in R?"

# Start interactive mode
chatr chat --interactive
```

### Test R Package
```r
library(chatr)

# Test basic functionality
chatr("Show me basic statistics functions")
help_explain("mean")
chatr_list_data()

# Test advanced features
data(mtcars)
chatr_analyze("mtcars")
```

---

## 🔀 Installation Methods Comparison

| Method | Best For | Time | Requirements |
|--------|----------|------|-------------|
| **Auto-installer** | R users wanting one-click setup | 2 min | R + internet |
| **Quick setup script** | All users wanting automation | 3 min | bash + internet |
| **Manual install** | Developers, customization | 5 min | Python knowledge |
| **R package only** | R-only users | 1 min | Existing ChatR backend |

---

## 🚨 Troubleshooting

### Common Issues

#### 1. `chatr: command not found`
```bash
# Solution: Activate virtual environment
source venv/bin/activate

# Or add to PATH
echo 'export PATH="$PATH:$(pwd)/venv/bin"' >> ~/.bashrc
```

#### 2. Ollama Model Not Found
```bash
# Check available models
ollama list

# Pull required model
ollama pull llama3.2:3b-instruct

# Check Ollama is running
ollama serve
```

#### 3. R Package Not Loading
```r
# Check if installed correctly
library(devtools)
install("r_package", force = TRUE)

# Check R can find the package
.libPaths()
installed.packages()["chatr",]
```

#### 4. Backend Connection Failed
```bash
# Start backend manually
chatr serve

# Check if running
curl http://localhost:8000/health

# In R, check connection
chatr_serve()  # Auto-start backend
```

#### 5. Permission Errors (Linux/Mac)
```bash
# Fix permissions
chmod +x quick_setup.sh
sudo chown -R $USER:$USER venv/
```

### Advanced Troubleshooting

#### Enable Verbose Mode
```bash
chatr chat --verbose "test query"
```

#### Check Configuration
```bash
chatr status
cat ~/.chatr/config.json
```

#### Reset Installation
```bash
# Remove existing config
rm -rf ~/.chatr/

# Reinstall
chatr init
```

---

## ⚙️ Configuration

### Default Configuration
ChatR creates `~/.chatr/config.json` with these defaults:

```json
{
  "ollama_host": "http://localhost:11434",
  "ollama_model": "llama3.2:3b-instruct",
  "embedding_model": "nomic-embed-text",
  "cache_dir": "~/.chatr/cache",
  "index_dir": "~/.chatr/index",
  "r_timeout": 30
}
```

### Customization
```bash
# Edit config
nano ~/.chatr/config.json

# Or use different config
chatr chat --config /path/to/custom/config.json
```

### Common Customizations

#### Use Different Model
```json
{
  "ollama_model": "llama3.1:8b-instruct"
}
```

#### Change Cache Location
```json
{
  "cache_dir": "/path/to/custom/cache"
}
```

#### Adjust R Execution Timeout
```json
{
  "r_timeout": 60
}
```

---

## 🏢 Enterprise/Multi-User Setup

### Shared Backend Server
```bash
# Start server accessible to network
chatr serve --host 0.0.0.0 --port 8000

# Users connect to shared server
export CHATR_HOST=http://server-ip:8000
```

### Docker Deployment
```bash
# Build image
docker build -t chatr .

# Run container
docker run -p 8000:8000 -p 11434:11434 chatr
```

---

## 🔄 Updates

### Update ChatR
```bash
cd chatR-GSOC
git pull
pip install -e . --upgrade
```

### Update Model
```bash
ollama pull llama3.2:3b-instruct
```

### Update R Package
```r
devtools::install("r_package", force = TRUE)
```

---

## 🆘 Getting Help

### Documentation
- **User Guide**: [USER_GUIDE.md](USER_GUIDE.md) - Complete usage documentation
- **README**: [README.md](README.md) - Project overview and quick start

### Community Support
- **GitHub Issues**: [Report bugs](https://github.com/your-org/chatR-GSOC/issues)
- **Discussions**: [Ask questions](https://github.com/your-org/chatR-GSOC/discussions)

### Logs and Debugging
```bash
# View ChatR logs
tail -f ~/.chatr/logs/chatr.log

# View Ollama logs
journalctl -u ollama -f

# R package debug
options(chatr.debug = TRUE)
```

---

## ✅ Success Checklist

After installation, you should be able to:

- [ ] `chatr status` shows configuration
- [ ] `chatr chat "test"` returns a response  
- [ ] `chatr serve` starts without errors
- [ ] `library(chatr)` loads in R
- [ ] `chatr("test")` works in R
- [ ] `chatr_analyze("mtcars")` provides analysis

**🎉 If all checks pass, you're ready to use ChatR!**

**Next**: Read the [User Guide](USER_GUIDE.md) to learn about all features.
