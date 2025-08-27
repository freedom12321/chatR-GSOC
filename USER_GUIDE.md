# ChatR User Guide

Complete guide to using ChatR - your intelligent, local assistant for R programming.

## Table of Contents

1. [Getting Started](#getting-started)
2. [R Package Functions](#r-package-functions)
3. [CLI Usage](#cli-usage)  
4. [Advanced Features](#advanced-features)
5. [RStudio Integration](#rstudio-integration)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)

---

## Getting Started

### Prerequisites
- ChatR installed ([Setup Guide](SETUP.md))
- Backend running: `chatr serve` (auto-starts from R)

### First Steps

#### R Package
```r
# Load ChatR
library(chatr)

# Basic query
chatr("How do I create a scatter plot?")

# Get function help
help_explain("mean")

# Analyze data
data(mtcars)
chatr_analyze("mtcars")
```

#### CLI
```bash
# Direct question
chatr chat "How do I load a CSV file?"

# Interactive mode
chatr chat --interactive

# Check status
chatr status
```

---

## R Package Functions

### 🗣️ Interactive Functions

#### `chatr(query)`
Main ChatR function - ask any R-related question.

```r
# Basic queries
chatr("How do I handle missing values?")
chatr("Show me different ways to create plots")
chatr("What's the difference between data.frame and tibble?")

# Context-aware queries (knows your environment)
data(iris)
chatr("analyze the relationship between sepal length and width")
```

#### `help_explain(function, package = NULL)`
Get intelligent help for R functions with examples.

```r
help_explain("lm")
help_explain("ggplot", "ggplot2") 
help_explain("mutate", "dplyr")

# More detailed than ?function
help_explain("apply")  # Shows when to use vs lapply, sapply
```

#### `analyze_code(code)`
Review and get suggestions for your R code.

```r
analyze_code("
  data <- read.csv('file.csv')
  plot(data$x, data$y)
  model <- lm(y ~ x, data)
")

# Returns: style suggestions, improvements, potential issues
```

### 📊 Data Analysis Functions

#### `chatr_analyze(dataset_name)`
Comprehensive analysis of any dataset in your environment.

```r
data(mtcars)
chatr_analyze("mtcars")

# Output includes:
# - Data structure summary
# - Missing value analysis  
# - Distribution descriptions
# - Correlation insights
# - Suggested next steps
```

#### `chatr_data_summary(dataset_name)`
Quick statistical summary with insights.

```r
chatr_data_summary("iris")
chatr_data_summary("mtcars")

# Faster than chatr_analyze, focuses on key statistics
```

#### `chatr_list_data()`
Show all available datasets and variables in environment.

```r
chatr_list_data()

# Useful before asking ChatR about your data
# ChatR uses this to understand your context
```

### 🧠 Advanced Code Generation

#### `chatr_code(query, mode = "interactive", execute_code = FALSE, save_script = NULL)`
Generate R code with advanced options.

```r
# Interactive code generation
chatr_code("create a correlation heatmap")

# Execute code immediately  
chatr_code("plot histogram of mpg", execute_code = TRUE)

# Save to script
chatr_code(
  "complete data cleaning workflow",
  mode = "script", 
  save_script = "cleaning.R"
)

# Modes: "interactive", "script", "analysis"
```

#### `chatr_generate_script(task, dataset_name = NULL, output_file = NULL)`
Create complete R scripts for complex tasks.

```r
# Generate analysis script
chatr_generate_script(
  task = "exploratory data analysis with machine learning",
  dataset_name = "mtcars",
  output_file = "mtcars_analysis.R"
)

# Generate visualization script  
chatr_generate_script(
  task = "create publication-ready plots",
  dataset_name = "iris",
  output_file = "iris_plots.R"
)
```

#### `chatr_code_session()`
Interactive programming session with step-by-step guidance.

```r
chatr_code_session()

# Interactive prompts:
# > What would you like to code?
# > Should I execute this code? (y/n/ask)
# > Continue with next step? (y/n/quit)
```

### 💡 Smart Assistance

#### `chatr_suggest_code(context = "")`
Get context-aware code suggestions.

```r
# Based on current environment
chatr_suggest_code()

# With specific context
chatr_suggest_code("I want to visualize the relationship between variables")
```

#### `chatr_analysis_tips(topic = "")`
Best practices and tips for R analysis.

```r
chatr_analysis_tips("linear regression")
chatr_analysis_tips("data cleaning")
chatr_analysis_tips()  # General tips based on your environment
```

### 🔧 Utility Functions

#### `chatr_serve(port = 8000, host = "localhost")`
Start ChatR backend server (auto-starts when needed).

```r
chatr_serve()  # Start on default port
chatr_serve(port = 8001)  # Custom port
```

---

## CLI Usage

### Basic Commands

#### `chatr chat`
Ask questions about R programming.

```bash
# Direct question
chatr chat "How do I create a boxplot?"

# Interactive mode
chatr chat --interactive
chatr chat -i

# With specific config
chatr chat --config /path/to/config.json "question"

# Verbose output for debugging
chatr chat --verbose "question"
```

#### `chatr init`
Initialize ChatR configuration and setup.

```bash
chatr init              # First-time setup
chatr init --force      # Reinitialize 
```

#### `chatr status`
Show ChatR configuration and system status.

```bash
chatr status

# Shows:
# - Configuration file location
# - Cache and index directories  
# - Ollama settings
# - Model information
```

#### `chatr serve`
Start API server for R package integration.

```bash
chatr serve                          # Default: localhost:8000
chatr serve --host 0.0.0.0           # Network accessible
chatr serve --port 8080              # Custom port
chatr serve --reload                 # Auto-reload for development
```

### Interactive Mode

In interactive mode (`chatr chat -i`):

```
> You: How do I merge data frames?
> ChatR: [Detailed explanation with examples]

> You: Show me an example with real data
> ChatR: [Code examples using common datasets]

> You: quit
Goodbye!
```

**Commands in interactive mode:**
- `quit`, `exit`, `q` - Exit
- `Ctrl+C` - Force exit
- Any R question - Get help

---

## Advanced Features

### Environment Awareness

ChatR automatically detects your R environment:

```r
# Load some data
data(mtcars, iris)
my_data <- data.frame(x = 1:10, y = rnorm(10))

# ChatR knows about your data
chatr("compare mtcars and iris datasets")
chatr("what analysis can I do with my_data?")

# Check what ChatR sees
chatr_list_data()
```

### Smart Code Generation

```r
# Context-aware generation
data(airquality)
chatr_code("handle missing values in this dataset")  # Knows about airquality

# Different generation modes
chatr_code("create plots", mode = "interactive")    # Step by step
chatr_code("create plots", mode = "script")         # Complete script  
chatr_code("create plots", mode = "analysis")       # Analysis-focused
```

### Multi-step Workflows

```r
# ChatR can handle complex, multi-step requests
chatr_generate_script(
  task = "complete machine learning pipeline: 
          load data, clean, explore, model, evaluate",
  dataset_name = "mtcars",
  output_file = "ml_pipeline.R"
)
```

### Code Execution Options

```r
# Review before execution
chatr_code("create summary statistics")  # Shows code, no execution

# Execute immediately
chatr_code("create summary statistics", execute_code = TRUE)

# Save to file
chatr_code("create plots", save_script = "plots.R")

# Combine options
chatr_code("analysis", execute_code = TRUE, save_script = "analysis.R")
```

---

## RStudio Integration

### Addins (RStudio Menu: Tools > Addins)

#### ChatR Assistant
- **Function**: `chatr_addin()`
- **Description**: Open ChatR in RStudio gadget/pane
- **Usage**: Interactive ChatR without leaving RStudio

#### Analyze Selection
- **Function**: `chatr_analyze_selection()`  
- **Description**: Analyze highlighted R code
- **Usage**: Select code → Run addin → Get analysis

#### Help at Cursor
- **Function**: `chatr_help_cursor()`
- **Description**: Get help for function under cursor
- **Usage**: Place cursor on function → Run addin

#### Smart Complete
- **Function**: `chatr_smart_complete()`
- **Description**: AI-powered code completion
- **Usage**: Partial code → Run addin → Get suggestions

### Keyboard Shortcuts

Set up custom shortcuts in RStudio:
- Tools → Modify Keyboard Shortcuts
- Search for "ChatR"
- Assign shortcuts (e.g., Ctrl+Alt+C for ChatR Assistant)

### Integration Examples

```r
# In RStudio console or script:

# 1. Write partial code
ggplot(mtcars, aes(x = mpg, y = 

# 2. Use ChatR addin or function
chatr_smart_complete()  # Suggests completions

# 3. Highlight problematic code
bad_code <- "
  data <- read.csv('file.csv')  
  plot(data$x, data$y)
"

# 4. Select text and use "Analyze Selection" addin
# Or: chatr_analyze_selection()
```

---

## Best Practices

### Getting Better Results

#### 1. Be Specific
```r
# Good
chatr("How do I create a scatter plot with regression line using ggplot2?")

# Better  
chatr("Create a scatter plot of mpg vs hp from mtcars with regression line and confidence interval using ggplot2")
```

#### 2. Provide Context
```r
# Load your data first
data(mtcars)

# Then ask context-aware questions
chatr("what's the best way to analyze this automotive dataset?")  # Knows it's mtcars
```

#### 3. Use Environment Awareness
```r
# Let ChatR see your workspace
chatr_list_data()

# Ask about your specific situation  
chatr("I have these datasets loaded, which analysis makes most sense?")
```

#### 4. Iterate and Refine
```r
chatr("create a plot")                           # General
chatr("create a better plot with custom colors") # Refine
chatr("save the plot as high-resolution PNG")    # Extend
```

### Workflow Integration

#### 1. Exploratory Analysis
```r
# 1. Quick overview
data(diamonds)
chatr_data_summary("diamonds")

# 2. Deep analysis  
chatr_analyze("diamonds")

# 3. Generate analysis script
chatr_generate_script("comprehensive EDA", "diamonds", "diamond_eda.R")
```

#### 2. Problem Solving
```r
# 1. Describe your problem
chatr("I have missing values in my time series data, what should I do?")

# 2. Get specific code
chatr_code("handle missing values in time series")

# 3. Review and execute
chatr_code("impute missing values", execute_code = TRUE)
```

#### 3. Learning New Concepts
```r
# 1. Learn the concept
chatr("explain machine learning cross-validation")

# 2. See examples
help_explain("cv.glm", "boot")

# 3. Practice with your data
chatr_code("implement cross-validation on my dataset")
```

---

## Troubleshooting

### Common Issues

#### 1. "Backend not running"
```r
# Solution: Start backend
chatr_serve()

# Or check if running
httr::GET("http://localhost:8000/health")
```

#### 2. "Function not found"  
```r
# Solution: Load package
library(chatr)

# Or reinstall
devtools::install("r_package")
```

#### 3. Empty/Poor Responses
```r
# Check Ollama is running
system("ollama serve")

# Check model is available
system("ollama list")

# Try different phrasing
chatr("rephrase: how do I create plots?")
```

#### 4. Code Generation Issues
```r
# Enable debug mode
options(chatr.debug = TRUE)

# Check generated code manually
result <- chatr_code("create plot", execute_code = FALSE)
cat(result$code)
```

### Debug Mode

```r
# Enable debugging
options(chatr.debug = TRUE)

# All ChatR functions will show detailed information
chatr("test query")  # Shows request/response details
```

### Getting Help

#### Within R
```r
# Package help
help(package = "chatr")

# Function help
?chatr
?chatr_analyze
?chatr_code

# Examples
example("chatr")
```

#### Community
- **Issues**: [GitHub Issues](https://github.com/your-org/chatR-GSOC/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/chatR-GSOC/discussions)
- **Email**: chatr-support@example.com

---

## Use Cases & Examples

### Data Scientists

```r
# Quick dataset exploration
data(boston, package = "MASS")  
chatr_analyze("boston")

# Generate modeling script
chatr_generate_script(
  "regression analysis with diagnostics", 
  "boston", 
  "boston_analysis.R"
)
```

### R Students

```r
# Learn concepts
chatr("what's the difference between lapply and sapply?")

# Practice problems
chatr("give me practice problems for data manipulation")

# Check homework
analyze_code("my_solution_code_here")
```

### Package Developers

```r
# API questions
chatr("how do I create S3 methods?")

# Documentation
help_explain("roxygen2::roxygenise")

# Code review
analyze_code("my_function_implementation")
```

### Analysts

```r
# Business questions
chatr("how to analyze customer churn data?")

# Report generation
chatr_generate_script("quarterly sales analysis", "sales_data", "q4_report.R")
```

---

## Advanced Configuration

### Custom Backend Settings

```r
# Use different host/port
options(chatr.host = "http://custom-server:8080")

# Longer timeouts
options(chatr.timeout = 120)

# Different model (if available)
options(chatr.model = "llama3.1:8b-instruct")
```

### Performance Tuning

```r
# Adjust R execution timeout
options(chatr.r_timeout = 60)  # seconds

# Cache settings
options(chatr.cache_size = 1000)  # number of cached responses

# Verbose logging
options(chatr.verbose = TRUE)
```

---

**🎉 You're now ready to use ChatR effectively!**

**Need help?** Check our [troubleshooting section](#troubleshooting) or [ask the community](https://github.com/your-org/chatR-GSOC/discussions).

**Want to contribute?** See our [contributing guide](CONTRIBUTING.md).