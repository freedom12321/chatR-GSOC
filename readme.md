# ChatR: An Intelligent, Local Assistant for R Programmers

## The Problem
R users, especially package developers and new contributors, face a common challenge: existing large language models often provide inaccurate or incomplete R code. They struggle with third-party packages, fail to provide precise answers about R contribution workflows, and are often too resource-intensive or proprietary for many users. The result is a frustrating, time-consuming experience that limits learning and collaboration.

---

## The ChatR Solution
**ChatR** is a lightweight, open, and reliable AI assistant built specifically for R users. It runs locally on your machine without needing a powerful GPU or a proprietary API key.

Think of ChatR as your personal, knowledgeable R expert who can search documentation, run code, and explain complex concepts clearly.

### Key Capabilities:
- **Local & Open**: Built with open models via Ollama (e.g., `llama3.2:3b-instruct`), it runs locally with no GPU required.
- **Context-Aware Retrieval**: Uses a **Retrieval-Augmented Generation (RAG)** pipeline to pull package documentation, examples, and vignettes.
- **Live R Tool-Calling**: Safely executes R code to verify its behavior and provide live outputs.
- **Educational Support**: Teaches concepts step-by-step with tiered support, from a single function to a multi-step analysis pipeline.
- **Easy-to-Use Delivery**: Ships as a command-line interface (CLI) and an R package (with an RStudio gadget).

## 🚀 Quick Start

### For R Users (Recommended - Full AI Functionality)
```r
# 1. Install ChatR with full backend (one-time setup)
source("https://raw.githubusercontent.com/freedom12321/chatR-GSOC/main/install_chatr.R")
install_chatr()

# 2. Use immediately with full AI power
library(chatr)
chatr("How do I create a linear regression with diagnostics?")  # ✅ Full LLM analysis
chatr_analyze("mtcars")  # ✅ AI-powered dataset analysis
chatr_repl()  # ✅ Interactive chat interface
chatr_code("machine learning model")  # ✅ Smart code generation
```

### ⚠️ **Important: Full Functionality Requires Backend**

**ChatR has two parts:**
- **R Package**: Functions like `chatr()`, `chatr_analyze()` (interface)
- **Python Backend**: LLM + RAG system (the AI brain)

**For FULL AI functionality, you need BOTH:**

#### **Option 1: Complete Installation (Recommended)**
```r
# This installs BOTH R package AND Python backend automatically
source("https://raw.githubusercontent.com/freedom12321/chatR-GSOC/main/install_chatr.R")
install_chatr()  # ✅ Sets up everything: Python CLI + R package + LLM
```

#### **Option 2: Manual Backend Setup**
```bash
# 1. Install Python backend first
git clone https://github.com/freedom12321/chatR-GSOC.git
cd chatR-GSOC
pip install -e .
ollama pull llama3.2:3b-instruct

# 2. Start backend server
chatr serve

# 3. Then install R package
# R -e "devtools::install('r_package')"
```

#### **What Happens Without Backend:**
```r
# R package only (no backend running):
library(chatr)
chatr("help me")  
# Result: ❌ "ChatR backend not running" + setup instructions
#         ❌ No AI responses, no code generation, no analysis
```

#### **What You Get With Complete Setup:**
```r
# R package + Backend running:
library(chatr)
chatr("help me")  
# Result: ✅ Full AI analysis with code examples
#         ✅ Smart suggestions and explanations
#         ✅ All advanced features work
```

### For CLI Users
```bash
# Install and setup
git clone https://github.com/freedom12321/chatR-GSOC.git
cd chatR-GSOC && pip install -e . && ollama pull llama3.2:3b-instruct

# Use immediately  
chatr chat "How do I merge dataframes in R?"
chatr serve  # Start backend for R package integration
```

📖 **[Full Setup Guide →](SETUP.md)** | 📚 **[Complete User Guide →](USER_GUIDE.md)**

---

## ✨ What Makes ChatR Special

### 🏠 **Completely Local & Private**
- Runs on your machine with open models via [Ollama](https://ollama.ai)
- No GPU required - works with `llama3.2:3b-instruct` (2GB RAM)
- Zero data leaves your computer - complete privacy

### 🎯 **R-Specific Intelligence** 
- **Live R Execution**: Safely runs R code to verify suggestions
- **Package-Aware**: Knows about 120+ indexed R functions from essential packages
- **Educational**: Explains concepts step-by-step with working examples

### 🔧 **Multiple Interfaces**
- **R Package**: Native R functions with full documentation (`?chatr`)
- **Interactive REPL**: Chat interface with `chatr_repl()` for real-time assistance
- **RStudio Integration**: Addins and gadgets for seamless workflow
- **Python CLI**: Cross-platform command-line tool
- **MCP Integration**: Tools for agentic frameworks (Cursor, Copilot)
- **API Server**: Backend for custom integrations

### 🧠 **Advanced Features**
- **Environment Awareness**: Understands your current R session and data
- **Smart Code Generation**: Creates complete scripts with `chatr_generate_script()`
- **Interactive Chat**: Real-time programming assistance with `chatr_repl()`
- **MCP Endpoints**: 6 tools exposed for agentic framework integration
- **Data Analysis Automation**: Intelligent dataset exploration with `chatr_analyze()`

## 🎪 All ChatR Features

| Feature | R Package Function | CLI Command | Description |
|---------|-------------------|-------------|-------------|
| **Interactive Chat** | `chatr()` | `chatr chat` | Natural language R programming assistance |
| **Interactive REPL** | `chatr_repl()` | `chatr chat -i` | Real-time chat interface with context memory |
| **Function Help** | `help_explain()` | `chatr chat` | Intelligent documentation with examples |
| **Code Analysis** | `analyze_code()` | `chatr chat` | Code review and improvement suggestions |
| **Data Exploration** | `chatr_analyze()` | - | Automated dataset analysis and insights |
| **Script Generation** | `chatr_generate_script()` | - | Create complete R scripts from descriptions |
| **Smart Code Generation** | `chatr_code()` | - | Generate and optionally execute R code |
| **Interactive Sessions** | `chatr_code_session()` | - | Step-by-step programming guidance |
| **Environment Summary** | `chatr_list_data()` | - | Show available datasets and variables |
| **Data Summaries** | `chatr_data_summary()` | - | Quick dataset overviews |
| **Smart Completion** | `chatr_smart_complete()` | - | Context-aware code recommendations |
| **Analysis Tips** | `chatr_analysis_tips()` | - | Get best practices for data analysis |
| **Interactive Assistant** | `chatr_assistant()` | - | Guided data analysis workflow |
| **Selected Code Analysis** | `chatr_analyze_selection()` | - | RStudio addin for code analysis |
| **MCP Tools** | - | `chatr mcp` | 6 tools for agentic frameworks (port 8002) |

*Note: CLI uses `chatr chat` for all queries - specific functionality depends on your question*

## 📖 Usage Examples

### Basic Queries
```r
library(chatr)

# Get help with R concepts
chatr("How do I handle missing values in linear regression?")

# Function-specific help with examples  
help_explain("dplyr::mutate")

# Code review and suggestions
analyze_code("
  data <- read.csv('file.csv')
  plot(data$x, data$y)
")
```

### Advanced Data Analysis
```r
# Load your dataset
data(mtcars)

# Get comprehensive analysis
chatr_analyze("mtcars")
# Returns: data summary, distributions, correlations, suggested analyses

# Generate complete analysis script
chatr_generate_script(
  task = "exploratory data analysis with visualizations",
  dataset_name = "mtcars", 
  output_file = "mtcars_eda.R"
)

# Interactive REPL interface
chatr_repl()  # Start interactive chat with context memory

# Interactive code generation with execution
chatr_code("create correlation heatmap", execute_code = TRUE)
```

### Interactive Programming
```r
# Step-by-step programming session
chatr_code_session()  # Interactive guidance

# Environment-aware assistance
chatr_list_data()  # See what data is available
chatr("analyze the relationship between mpg and weight")  # ChatR knows about mtcars
```

### CLI Usage
```bash
# Ask questions directly
chatr chat "How do I create a violin plot in R?"

# Interactive mode
chatr chat --interactive
# > You: How do I merge data frames?
# > ChatR: [detailed explanation with examples]

# Start MCP server for agentic frameworks
chatr mcp --port 8002

# Start main server for R integration
chatr serve
```

## How ChatR Stays Up-to-Date
ChatR avoids large downloads by using a dynamic, two-pronged approach. It combines live registries with a lightweight, rotating local cache.

### 1. Live Discovery (No Bulk Downloads)
- Queries **CRAN** and **r-universe** registries on demand for the latest package lists and metadata.
- Leverages the `pkgsearch` API to find new packages and their documentation in real-time.
- **Outcome**: You can always search for the most current R packages without needing to maintain a giant local corpus.

### 2. Thin Local Cache
- Maintains a small, local cache of only package names, titles, and descriptions.
- **Full documentation is downloaded only on demand** for packages you actually reference, then cached for future reuse.

---

## Technical Architecture
ChatR is powered by a fully local, open-source Retrieval-Augmented Generation (RAG) system.

### Hybrid Retrieval (Fully Local)
You don't need an OpenAI key. ChatR uses a hybrid retrieval system to ensure both speed and semantic accuracy. It combines two methods:

* **Sparse Retrieval (BM25)**: A lightweight, keyword-based search that quickly filters a vast corpus of documentation, acting as the first pass to identify a broad set of potentially relevant documents.
* **Dense Embeddings**: Using local models like `nomic-embed-text`, this approach performs a semantic search on the pre-filtered results from the sparse retrieval. The best matches are then re-ranked, ensuring the most semantically relevant answers rise to the top. This hybrid approach offers the speed of a keyword search with the precision of a vector-based one.

### R Tool-Calling: Secure & Live Execution
A core feature of ChatR is its ability to safely execute R code. It uses sandboxed subprocesses to run `Rscript` with strict time and resource limits. This isolation prevents unintended side effects and ensures a secure environment.

The system captures key outputs, including:
-   Function help pages (`?function`).
-   Source code for packages or functions.
-   Live code outputs, which are then summarized to provide users with verified results.

### RAG System & Data Sources
The RAG system is built on a foundation of meticulously indexed R documentation. It processes and indexes a range of sources, including:

* **CRAN Man Pages and Vignettes**: These are processed and chunked to ensure that each retrieved snippet is contextually rich and highly relevant.
* **Task Views & "Writing R Extensions"**: These resources are included to provide high-level, conceptual knowledge for more complex queries.

### Advanced Task Orchestration (Multi-Package & Multi-Solution)
ChatR will move beyond single-function requests to orchestrate complex, multi-step tasks across multiple packages. When a user asks a high-level question (e.g., *"How do I do linear regression in R?"*), ChatR will use an internal decision-making process to:

- **Identify Multiple Solutions**  
  Recognize that a task can be accomplished in different ways (e.g., using `lm()` from the **stats** package, or `glm()` from **stats** with specific parameters). It will also consider common tidyverse alternatives (e.g., **tidymodels**). This provides the user with a choice of tools.

- **Sequence Package Dependencies**  
  Create a logical workflow of R packages and functions. For example, a linear regression task often requires data manipulation (**dplyr**) and visualization (**ggplot2**) before the modeling step. ChatR will present this sequence, explaining why each step and package is needed.

- **Provide Tiered Suggestions**  
  Offer a brief overview of all possible solutions, then provide a detailed, step-by-step guide for one or two of the most common or recommended approaches. This prevents overwhelming the user while still acknowledging alternative methods.

---

### Interactive & Fluid Workflow Integration
To create a truly interactive experience, ChatR will integrate directly into the user's coding environment. This goes beyond a simple chat box and creates a fluid, code-first workflow.

- **Cursor-Based Code Injection**  
  As the user is typing in their R script or console, ChatR will provide inline, ghost-text suggestions at the cursor's position. This is similar to modern code editors but tailored for R and user-specific use cases.

- **Accept and Run on Demand**  
  The user can accept the suggested code with a single key press (e.g., **Tab**). Once accepted, a follow-up prompt will appear (e.g., *[Press Enter to run]*), allowing the user to immediately execute the code in the R console to see the output. This provides instant feedback and reinforces the learning process.

- **Human-in-the-Loop Validation**  
  The user remains in full control. They can modify the suggested code before accepting it, or simply ignore the suggestion and continue typing. This ensures the assistant is a helpful tool, not a replacement for the programmer's judgment.

The system uses a thin cache for metadata and downloads full documentation on-demand, which keeps its local footprint minimal.
---

## Getting Started

### For R Users (Recommended)
**🎯 Quick Start**: [User Guide](USER_GUIDE.md) | [Setup Guide](SETUP.md)

```r
# 1. Start backend: chatr serve (in terminal)
# 2. Load in R:
source("/path/to/chatR-GSOC/chatr_complete.R")

# 3. Use immediately:
data(mtcars)
chatr_analyze("mtcars")
chatr('how to do linear regression with assumptions')
```

### Prerequisites
- Python 3.8+
- R 4.0+ (for R integration)
- Ollama for local LLM

### Installation
```bash
# Clone and setup
git clone https://github.com/freedom12321/chatR-GSOC.git
cd chatR-GSOC
python -m venv venv
source venv/bin/activate
pip install -e .

# Setup Ollama
curl -fsSL https://ollama.ai/install.sh | sh
ollama pull llama3.2:3b-instruct

# Initialize ChatR
chatr init
chatr serve
```

## Delivery Options
ChatR is designed to be accessible wherever you work.

### Option A: R Integration (Featured)
Complete R client with all AI capabilities:
- **Functions:** `chatr()`, `chatr_repl()`, `chatr_analyze()`, `chatr_list_data()`, `help_explain()`
- **Smart Features:** Auto-start backend, interactive REPL, data analysis planning
- **Usage:** `library(chatr)` then use any function

### Option B: Cross-Platform CLI  
Command-line tool for terminal users:
```bash
chatr chat "How do I create a violin plot?"
chatr chat --interactive  # Interactive mode
chatr mcp --port 8002     # MCP server for agentic frameworks
```

### Option C: MCP Integration
Tools for agentic frameworks (Cursor, Copilot, etc.):
- **MCP Server:** `chatr mcp --port 8002`
- **6 Tools Available:** r_execute, r_help, r_search, r_explain, r_package_info, r_vignettes
- **Usage:** Integrate with agentic frameworks via HTTP endpoints
- **Status:** ✅ Working on port 8002 (separate from main server)
