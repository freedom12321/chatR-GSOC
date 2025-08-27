# ChatR Complete - Full Functionality R Client
# Preserves ALL features: RAG, LLM, data analysis, external sources, etc.
# Works with existing backend: chatr serve

# Load required libraries
suppressPackageStartupMessages({
  if (!require(httr, quietly = TRUE)) install.packages("httr")
  if (!require(jsonlite, quietly = TRUE)) install.packages("jsonlite")
  library(httr)
  library(jsonlite)
})

cat("🤖 ChatR Complete Client Loading...\n")

# Core connection functions
.test_connection <- function(host = "http://localhost:8000") {
  tryCatch({
    response <- httr::GET(
      paste0(host, "/health"), 
      httr::timeout(5),
      httr::user_agent("ChatR-Complete-Client")
    )
    status <- httr::status_code(response)
    if (status == 200) {
      return(TRUE)
    } else {
      cat("❌ Health check failed - Status:", status, "\n")
      return(FALSE)
    }
  }, error = function(e) {
    cat("❌ Connection error:", e$message, "\n")
    return(FALSE)
  })
}

.send_request <- function(endpoint, data = NULL, method = "POST", host = "http://localhost:8000", timeout = 90) {
  tryCatch({
    cat("🔄 Processing request...\n")
    
    if (method == "GET") {
      response <- httr::GET(
        url = paste0(host, endpoint),
        httr::timeout(timeout),
        httr::user_agent("ChatR-Complete-Client")
      )
    } else {
      response <- httr::POST(
        url = paste0(host, endpoint),
        body = if(is.null(data)) NULL else jsonlite::toJSON(data, auto_unbox = TRUE),
        httr::content_type("application/json"),
        httr::timeout(timeout),
        httr::user_agent("ChatR-Complete-Client")
      )
    }
    
    status <- httr::status_code(response)
    cat("📡 Response received (Status:", status, ")\n")
    
    if (status == 200) {
      return(httr::content(response, as = "parsed"))
    } else {
      error_msg <- paste("HTTP", status)
      if (status == 500) error_msg <- paste(error_msg, "- Server Error")
      if (status == 404) error_msg <- paste(error_msg, "- Endpoint Not Found")
      cat("❌ HTTP Error:", error_msg, "\n")
      return(list(status = "error", error = error_msg))
    }
  }, error = function(e) {
    if (grepl("timeout", e$message, ignore.case = TRUE)) {
      cat("⏰ Request timed out - This query might be complex and need more time\n")
      cat("💡 Try: Shorter queries, or check if backend is processing heavy data\n")
    } else {
      cat("❌ Request error:", e$message, "\n")
    }
    return(list(status = "error", error = as.character(e)))
  })
}

# Auto-start functionality (preserved from original)
.auto_start_backend <- function() {
  cat("🚀 Attempting to auto-start ChatR backend...\n")
  
  # Find ChatR executable
  chatr_paths <- c(
    "/Users/lihanxia/Documents/chatR-GSOC/venv/bin/chatr",
    Sys.which("chatr")
  )
  
  chatr_cmd <- ""
  for (path in chatr_paths) {
    if (path != "" && file.exists(path)) {
      chatr_cmd <- path
      break
    }
  }
  
  if (chatr_cmd == "") {
    cat("❌ ChatR executable not found\n")
    cat("📋 Please ensure:\n")
    cat("   1. ChatR is installed: pip install -e /Users/lihanxia/Documents/chatR-GSOC\n")
    cat("   2. Virtual environment is activated\n")
    return(FALSE)
  }
  
  cat("✅ Found ChatR at:", chatr_cmd, "\n")
  
  # Start backend
  tryCatch({
    if (.Platform$OS.type == "unix") {
      cmd <- paste0("bash -c 'source /Users/lihanxia/Documents/chatR-GSOC/venv/bin/activate && ", 
                   chatr_cmd, " serve --port 8000 > /tmp/chatr.log 2>&1 &'")
      system(cmd, wait = FALSE)
    } else {
      cmd <- paste0("start /b ", chatr_cmd, " serve --port 8000")
      system(cmd, wait = FALSE)
    }
    
    cat("⏳ Starting backend... (logs: /tmp/chatr.log)\n")
    
    # Wait for startup
    for (i in 1:20) {
      Sys.sleep(1)
      cat(".")
      if (.test_connection()) {
        cat(" ✅\n")
        return(TRUE)
      }
    }
    
    cat(" ❌\n")
    cat("Backend failed to start in 20 seconds\n")
    return(FALSE)
    
  }, error = function(e) {
    cat("❌ Auto-start failed:", e$message, "\n")
    return(FALSE)
  })
}

.ensure_backend <- function(host = "http://localhost:8000") {
  if (.test_connection(host)) {
    return(TRUE)
  }
  
  cat("🔄 Backend not responding. Checking port...\n")
  
  # Check if port is occupied
  port_check <- system("lsof -ti:8000", ignore.stdout = TRUE, ignore.stderr = TRUE)
  if (port_check == 0) {
    cat("⚠️  Port 8000 is occupied. Waiting for backend...\n")
    Sys.sleep(3)
    if (.test_connection(host)) {
      return(TRUE)
    }
  }
  
  # Try auto-start
  cat("🚀 Attempting to start backend automatically...\n")
  if (.auto_start_backend()) {
    return(TRUE)
  }
  
  cat("❌ Please start backend manually: chatr serve\n")
  return(FALSE)
}

# ============================================================================
# MAIN CHATR FUNCTIONS - FULL FUNCTIONALITY PRESERVED
# ============================================================================

#' Main ChatR function - Full conversational AI with RAG
#' @param query Character. Your question or request
#' @param host Character. Backend host URL
#' @return Invisible response text
chatr <- function(query = NULL, host = "http://localhost:8000") {
  if (is.null(query)) {
    cat("📝 Usage: chatr('your question here')\n")
    return(invisible(NULL))
  }
  
  if (!.ensure_backend(host)) {
    return(invisible(NULL))
  }
  
  result <- .send_request("/chat", list(query = query), "POST", host, 120)
  
  if (result$status == "success") {
    cat("\n🤖 ChatR Response:\n")
    cat(paste(rep("=", 60), collapse = ""), "\n")
    cat(result$response, "\n")
    cat(paste(rep("=", 60), collapse = ""), "\n\n")
    return(invisible(result$response))
  } else {
    cat("❌ Query failed:", result$error, "\n")
    return(invisible(NULL))
  }
}

#' Smart Data Analysis - Full AI-powered analysis planning
#' @param dataset_name Character. Name of dataset in environment  
#' @param goal Character. Optional analysis goal
#' @param host Character. Backend host URL
chatr_analyze <- function(dataset_name = NULL, goal = "", host = "http://localhost:8000") {
  if (!is.null(dataset_name) && !exists(dataset_name, envir = .GlobalEnv)) {
    cat("❌ Dataset '", dataset_name, "' not found in your R environment\n")
    cat("💡 Available objects:", paste(ls(envir = .GlobalEnv), collapse = ", "), "\n")
    return(invisible(NULL))
  }
  
  if (!.ensure_backend(host)) {
    return(invisible(NULL))
  }
  
  result <- .send_request("/analyze_data", 
                         list(dataset_name = dataset_name, user_goal = goal), 
                         "POST", host, 120)
  
  if (result$status == "success") {
    cat("\n📊 Smart Data Analysis Plan:\n")
    cat(paste(rep("=", 60), collapse = ""), "\n")
    cat(result$response, "\n")
    cat(paste(rep("=", 60), collapse = ""), "\n\n")
  } else {
    cat("❌ Analysis failed:", result$error, "\n")
  }
}

#' Quick Data Summary - Dataset characteristics 
#' @param dataset_name Character. Name of dataset to summarize
#' @param host Character. Backend host URL
chatr_data_summary <- function(dataset_name, host = "http://localhost:8000") {
  if (!exists(dataset_name, envir = .GlobalEnv)) {
    cat("❌ Dataset '", dataset_name, "' not found\n")
    return(invisible(NULL))
  }
  
  if (!.ensure_backend(host)) {
    return(invisible(NULL))
  }
  
  result <- .send_request("/data_summary", 
                         list(dataset_name = dataset_name), 
                         "POST", host, 60)
  
  if (result$status == "success") {
    cat("\n📋 Data Summary:\n")
    cat(paste(rep("-", 40), collapse = ""), "\n")
    cat(result$response, "\n")
    cat(paste(rep("-", 40), collapse = ""), "\n\n")
  } else {
    cat("❌ Summary failed:", result$error, "\n")
  }
}

#' List Available Data - Show all analyzable datasets
#' @param host Character. Backend host URL
chatr_list_data <- function(host = "http://localhost:8000") {
  if (!.ensure_backend(host)) {
    return(invisible(NULL))
  }
  
  result <- .send_request("/list_data", NULL, "GET", host, 30)
  
  if (result$status == "success") {
    cat("\n📂 Available Data Objects:\n")
    cat(paste(rep("-", 40), collapse = ""), "\n")
    cat(result$response, "\n")
    cat(paste(rep("-", 40), collapse = ""), "\n\n")
  } else {
    cat("❌ List failed:", result$error, "\n")
  }
}

#' Code Analysis - Analyze R code for improvements
#' @param code Character. R code to analyze
#' @param host Character. Backend host URL
analyze_code <- function(code, host = "http://localhost:8000") {
  if (!.ensure_backend(host)) {
    return(invisible(NULL))
  }
  
  result <- .send_request("/analyze", list(code = code), "POST", host, 60)
  
  if (result$status == "success") {
    cat("\n🔍 Code Analysis:\n")
    cat(paste(rep("-", 40), collapse = ""), "\n")
    cat(result$analysis, "\n")
    cat(paste(rep("-", 40), collapse = ""), "\n\n")
  } else {
    cat("❌ Analysis failed:", result$error, "\n")
  }
}

#' Function Help - Get intelligent help for R functions
#' @param func Character. Function name
#' @param package Character. Package name (optional)
#' @param host Character. Backend host URL
help_explain <- function(func, package = NULL, host = "http://localhost:8000") {
  if (!.ensure_backend(host)) {
    return(invisible(NULL))
  }
  
  query <- if (is.null(package)) {
    paste("Help me understand the R function:", func)
  } else {
    paste("Help me understand the R function:", func, "from package", package)
  }
  
  chatr(query, host)
}

# ============================================================================
# INTERACTIVE ANALYSIS ASSISTANT - FULL FUNCTIONALITY
# ============================================================================

#' Interactive Analysis Assistant - Guided data analysis
chatr_assistant <- function(host = "http://localhost:8000") {
  cat("🎯 ChatR Interactive Analysis Assistant\n")
  cat(paste(rep("=", 50), collapse = ""), "\n\n")
  
  if (!.ensure_backend(host)) {
    return(invisible(NULL))
  }
  
  # Get available datasets
  env_objects <- ls(envir = .GlobalEnv)
  data_objects <- c()
  
  for (obj in env_objects) {
    obj_value <- get(obj, envir = .GlobalEnv)
    if (is.data.frame(obj_value) || is.matrix(obj_value) || is.vector(obj_value)) {
      data_objects <- c(data_objects, obj)
    }
  }
  
  if (length(data_objects) == 0) {
    cat("📂 No data objects found in your environment.\n")
    cat("💡 Try loading some data first:\n")
    cat("   data(mtcars)           # Built-in dataset\n")
    cat("   my_data <- read.csv()  # Your own data\n\n")
    return(invisible(NULL))
  }
  
  cat("📊 Available datasets:\n")
  for (i in seq_along(data_objects)) {
    obj <- get(data_objects[i], envir = .GlobalEnv)
    if (is.data.frame(obj)) {
      cat(sprintf("  %d. %s (%d rows × %d columns)\n", i, data_objects[i], nrow(obj), ncol(obj)))
    } else if (is.matrix(obj)) {
      cat(sprintf("  %d. %s (matrix: %d × %d)\n", i, data_objects[i], nrow(obj), ncol(obj)))
    } else {
      cat(sprintf("  %d. %s (vector: length %d)\n", i, data_objects[i], length(obj)))
    }
  }
  
  cat("\n❓ Which dataset would you like to analyze? (Enter number or name): ")
  choice <- readline()
  
  # Parse choice
  selected_dataset <- NULL
  if (grepl("^[0-9]+$", choice)) {
    choice_num <- as.numeric(choice)
    if (choice_num >= 1 && choice_num <= length(data_objects)) {
      selected_dataset <- data_objects[choice_num]
    }
  } else if (choice %in% data_objects) {
    selected_dataset <- choice
  }
  
  if (is.null(selected_dataset)) {
    cat("❌ Invalid choice. Please try again.\n")
    return(invisible(NULL))
  }
  
  cat("\n🎯 What's your analysis goal? (optional, press Enter to skip): ")
  goal <- readline()
  
  cat("\n🔍 Analyzing your data...\n\n")
  chatr_analyze(selected_dataset, goal, host)
}

#' Analysis Tips - Best practices guidance
#' @param data_type Character. Type of analysis
chatr_analysis_tips <- function(data_type = "exploratory") {
  tips <- switch(data_type,
    "exploratory" = c(
      "🔍 Start with summary statistics: summary(data)",
      "❓ Check for missing values: sapply(data, function(x) sum(is.na(x)))",
      "📊 Visualize distributions: hist() for numeric, barplot() for categorical", 
      "📦 Look for outliers: boxplot(data$numeric_column)",
      "🔗 Explore relationships: plot(data$x, data$y) or pairs(data)",
      "📈 Check correlations: cor(data) for numeric variables"
    ),
    "predictive" = c(
      "🎯 Define your target variable clearly",
      "✂️ Split data into training/testing sets", 
      "🔗 Check for multicollinearity: cor(predictors)",
      "✅ Validate model assumptions (residual plots)",
      "🔄 Use cross-validation: train() from caret package",
      "📊 Evaluate performance: RMSE, R², confusion matrix"
    ),
    "descriptive" = c(
      "📊 Focus on central tendency: mean, median, mode",
      "📏 Measure variability: standard deviation, range, IQR",
      "📈 Create clear visualizations with proper labels",
      "📋 Use appropriate summary tables",
      "👥 Consider your audience when presenting results", 
      "📊 Include confidence intervals where appropriate"
    ),
    c("❓ Please specify: 'exploratory', 'predictive', or 'descriptive'")
  )
  
  cat(paste("📚", toupper(data_type), "Analysis Tips:\n"))
  cat(paste(tips, collapse = "\n"), "\n")
  cat("\n💡 For personalized guidance: chatr_analyze('your_dataset_name')\n")
}

# ============================================================================
# STARTUP AND STATUS
# ============================================================================

# Test connection and show status
if (.test_connection()) {
  cat("✅ Connected to ChatR backend!\n")
  cat("🧠 Full AI capabilities available (RAG + LLM + External Data)\n")
} else {
  cat("⚠️  Backend not running\n")
  cat("🚀 Start with: chatr serve (or functions will auto-start)\n")
}

cat("\n📚 Available Functions (ALL FUNCTIONALITY PRESERVED):\n")
cat("═══════════════════════════════════════════════════════\n")
cat("🤖 Main Functions:\n")
cat("   • chatr('your question')           - Full conversational AI\n")
cat("   • chatr_analyze('dataset_name')    - Smart data analysis plans\n")
cat("   • chatr_list_data()               - Show available datasets\n")
cat("   • chatr_data_summary('dataset')   - Quick dataset summary\n")
cat("\n🔧 Analysis Tools:\n") 
cat("   • analyze_code('R code here')     - Code improvement suggestions\n")
cat("   • help_explain('function_name')   - Intelligent function help\n")
cat("   • chatr_assistant()               - Interactive guided analysis\n")
cat("   • chatr_analysis_tips('type')     - Best practices guidance\n")
cat("\n🚀 Quick Start:\n")
cat("   data(mtcars)\n")
cat("   chatr_analyze('mtcars')\n")
cat("   chatr('how to do linear regression with assumptions')\n")
cat("═══════════════════════════════════════════════════════\n\n")

cat("🎉 ChatR Complete Client Ready!\n")
cat("💫 All features preserved: RAG, LLM, External Sources, Data Analysis\n\n")