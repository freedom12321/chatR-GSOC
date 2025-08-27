#' Analyze Your Data with ChatR
#'
#' Get intelligent analysis plans and guidance for your datasets.
#' ChatR will inspect your data and provide step-by-step analysis recommendations.
#'
#' @param dataset_name Name of the dataset to analyze (character string)
#' @param goal Optional analysis goal or question (character string)
#' @return Analysis plan with step-by-step guidance
#' @export
#' @examples
#' # Load sample data
#' data(mtcars)
#' 
#' # Get analysis plan for mtcars
#' chatr_analyze("mtcars")
#' 
#' # Get analysis plan with specific goal
#' chatr_analyze("mtcars", "predict fuel efficiency")
#' 
#' # Quick summary
#' chatr_data_summary("mtcars")
chatr_analyze <- function(dataset_name = NULL, goal = "", host = "http://localhost:8000") {
  
  # Check if dataset exists
  if (!is.null(dataset_name) && !exists(dataset_name, envir = .GlobalEnv)) {
    stop(paste("Dataset '", dataset_name, "' not found in your environment.", 
               "\nTip: Load your data first, e.g., data(mtcars) or my_data <- read.csv('file.csv')"))
  }
  
  # Check if ChatR backend is running, auto-start if needed
  if (!.is_chatr_running(host)) {
    cat("ChatR backend not running. Starting automatically...\n")
    
    # Try to auto-start the backend
    started <- .auto_start_chatr_backend()
    
    if (!started) {
      cat("Failed to auto-start ChatR backend. Please start manually:\n")
      cat("  In terminal: chatr serve\n")
      return(invisible(NULL))
    }
    
    # Wait for startup
    Sys.sleep(3)
    
    if (!.is_chatr_running(host)) {
      cat("ChatR backend failed to start. Please start manually:\n")
      cat("  In terminal: chatr serve\n")
      return(invisible(NULL))
    }
    
    cat("ChatR backend started successfully!\n")
  }
  
  # Make API call to ChatR
  tryCatch({
    response <- .send_chatr_request(
      endpoint = "/analyze_data",
      data = list(
        dataset_name = dataset_name,
        user_goal = goal
      ),
      host = host
    )
    
    if (response$status == "success") {
      # Display formatted response with proper newlines
      cat("\n")
      formatted_response <- .format_chatr_output(response$response)
      cat(formatted_response)
      cat("\n")
    } else {
      cat("Error:", response$error, "\n")
    }
    
  }, error = function(e) {
    cat("Error connecting to ChatR service:", e$message, "\n")
    cat("Tip: Make sure ChatR is running with: chatr serve\n")
  })
}

#' Quick Data Summary
#'
#' Get a quick overview of your dataset structure and characteristics.
#'
#' @param dataset_name Name of the dataset to summarize
#' @return Quick summary of dataset characteristics
#' @export
#' @examples
#' data(iris)
#' chatr_data_summary("iris")
chatr_data_summary <- function(dataset_name, host = "http://localhost:8000") {
  
  if (!exists(dataset_name, envir = .GlobalEnv)) {
    stop(paste("Dataset '", dataset_name, "' not found in your environment."))
  }
  
  # Check if ChatR backend is running, auto-start if needed
  if (!.is_chatr_running(host)) {
    cat("ChatR backend not running. Starting automatically...\n")
    
    # Try to auto-start the backend
    started <- .auto_start_chatr_backend()
    
    if (!started) {
      cat("Failed to auto-start ChatR backend. Please start manually:\n")
      cat("  In terminal: chatr serve\n")
      return(invisible(NULL))
    }
    
    # Wait for startup
    Sys.sleep(3)
    
    if (!.is_chatr_running(host)) {
      cat("ChatR backend failed to start. Please start manually:\n")
      cat("  In terminal: chatr serve\n")
      return(invisible(NULL))
    }
    
    cat("ChatR backend started successfully!\n")
  }
  
  tryCatch({
    response <- .send_chatr_request(
      endpoint = "/data_summary", 
      data = list(dataset_name = dataset_name),
      host = host
    )
    
    if (response$status == "success") {
      cat("\n")
      formatted_response <- .format_chatr_output(response$response)
      cat(formatted_response)
      cat("\n")
    } else {
      cat("Error:", response$error, "\n")
    }
    
  }, error = function(e) {
    cat("Error:", e$message, "\n")
  })
}

#' List Available Data Objects
#'
#' Show all data objects in your R environment that ChatR can analyze.
#'
#' @return List of available datasets with their characteristics
#' @export
#' @examples
#' chatr_list_data()
chatr_list_data <- function(host = "http://localhost:8000") {
  
  # Check if ChatR backend is running, auto-start if needed
  if (!.is_chatr_running(host)) {
    cat("ChatR backend not running. Starting automatically...\n")
    
    # Try to auto-start the backend
    started <- .auto_start_chatr_backend()
    
    if (!started) {
      cat("Failed to auto-start ChatR backend. Please start manually:\n")
      cat("  In terminal: chatr serve\n")
      return(invisible(NULL))
    }
    
    # Wait for startup
    Sys.sleep(3)
    
    if (!.is_chatr_running(host)) {
      cat("ChatR backend failed to start. Please start manually:\n")
      cat("  In terminal: chatr serve\n")
      return(invisible(NULL))
    }
    
    cat("ChatR backend started successfully!\n")
  }
  
  tryCatch({
    response <- httr::GET(paste0(host, "/list_data"))
    
    if (httr::status_code(response) == 200) {
      result <- httr::content(response, as = "parsed")
      if (result$status == "success") {
        cat("\n")
        cat(gsub("\\n", "\n", result$response))
        cat("\n")
      } else {
        cat("Error:", result$error, "\n")
      }
    } else {
      cat("Error: HTTP", httr::status_code(response), "\n")
    }
    
  }, error = function(e) {
    cat("Error:", e$message, "\n")
  })
}

#' Smart Analysis Assistant
#'
#' Interactive helper that guides you through data analysis.
#' This function will look at your data and suggest appropriate analyses.
#'
#' @export
#' @examples
#' # Start interactive analysis assistant
#' chatr_assistant()
chatr_assistant <- function() {
  
  cat("🎯 ChatR Smart Analysis Assistant\n")
  cat("==================================\n\n")
  
  # Get available data
  env_objects <- ls(envir = .GlobalEnv)
  data_objects <- c()
  
  for (obj in env_objects) {
    obj_value <- get(obj, envir = .GlobalEnv)
    if (is.data.frame(obj_value) || is.matrix(obj_value) || is.vector(obj_value)) {
      data_objects <- c(data_objects, obj)
    }
  }
  
  if (length(data_objects) == 0) {
    cat("No data objects found in your environment.\n")
    cat("Try loading some data first:\n")
    cat("  data(mtcars)           # Load built-in dataset\n")
    cat("  my_data <- read.csv()  # Load your own data\n\n")
    return(invisible())
  }
  
  cat("Available datasets:\n")
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
  
  cat("\nWhich dataset would you like to analyze? (Enter number or name): ")
  choice <- readline()
  
  # Parse choice
  if (grepl("^[0-9]+$", choice)) {
    choice_num <- as.numeric(choice)
    if (choice_num >= 1 && choice_num <= length(data_objects)) {
      selected_dataset <- data_objects[choice_num]
    } else {
      cat("Invalid choice. Please try again.\n")
      return(invisible())
    }
  } else if (choice %in% data_objects) {
    selected_dataset <- choice
  } else {
    cat("Dataset not found. Please try again.\n")
    return(invisible())
  }
  
  cat("\nWhat's your analysis goal? (optional, press Enter to skip): ")
  goal <- readline()
  
  cat("\n🔍 Analyzing your data...\n\n")
  
  # Call analysis function
  chatr_analyze(selected_dataset, goal)
}

#' Data Analysis Tips and Best Practices
#'
#' Get general tips for data analysis based on your data type.
#'
#' @param data_type Type of analysis ("exploratory", "predictive", "descriptive")
#' @return Tips and best practices
#' @export
chatr_analysis_tips <- function(data_type = "exploratory") {
  
  tips <- switch(data_type,
    "exploratory" = c(
      "1. Start with summary statistics: summary(data)",
      "2. Check for missing values: sapply(data, function(x) sum(is.na(x)))",
      "3. Visualize distributions: hist() for numeric, barplot() for categorical",
      "4. Look for outliers: boxplot(data$numeric_column)",
      "5. Explore relationships: plot(data$x, data$y) or pairs(data)",
      "6. Check correlations: cor(data) for numeric variables"
    ),
    "predictive" = c(
      "1. Define your target variable clearly",
      "2. Split data into training/testing sets",
      "3. Check for multicollinearity: cor(predictors)",
      "4. Validate model assumptions (residual plots)",
      "5. Use cross-validation: train() from caret package",
      "6. Evaluate performance: RMSE, R², confusion matrix"
    ),
    "descriptive" = c(
      "1. Focus on central tendency: mean, median, mode",
      "2. Measure variability: standard deviation, range, IQR",
      "3. Create clear visualizations with proper labels",
      "4. Use appropriate summary tables",
      "5. Consider your audience when presenting results",
      "6. Include confidence intervals where appropriate"
    ),
    c("Please specify: 'exploratory', 'predictive', or 'descriptive'")
  )
  
  cat(paste("📊", data_type, "Analysis Tips:\n"))
  cat(paste(tips, collapse = "\n"))
  cat("\n\nFor personalized guidance, try: chatr_analyze('your_dataset_name')\n")
}

# Internal helper functions (if not available from main chatr package)

.is_chatr_running <- function(host) {
  tryCatch({
    response <- httr::GET(paste0(host, "/health"), httr::timeout(2))
    httr::status_code(response) == 200
  }, error = function(e) FALSE)
}

.format_chatr_output <- function(text) {
  # Convert literal \n to actual newlines
  text <- gsub("\\\\n", "\n", text)
  
  # Enhanced formatting with code blocks and output blocks
  lines <- strsplit(text, "\n")[[1]]
  formatted_lines <- character()
  i <- 1
  
  while (i <= length(lines)) {
    line <- lines[i]
    
    # Detect R code blocks (lines starting with ```r or ``` followed by R code)
    if (grepl("^```r?\\s*$", line)) {
      # Start of code block
      formatted_lines <- c(formatted_lines, 
                          "",
                          "┌─ R CODE ─────────────────────────────────────────┐")
      i <- i + 1
      
      # Process code content
      while (i <= length(lines) && !grepl("^```\\s*$", lines[i])) {
        code_line <- lines[i]
        formatted_lines <- c(formatted_lines, paste("│", code_line))
        i <- i + 1
      }
      
      formatted_lines <- c(formatted_lines, 
                          "└──────────────────────────────────────────────────┘")
      
      # Check if there's output following this code block
      if (i + 1 <= length(lines) && 
          (grepl("^\\s*#>", lines[i + 1]) || grepl("^\\s*\\[1\\]", lines[i + 1]) || 
           grepl("=== .* ===", lines[i + 1]))) {
        
        formatted_lines <- c(formatted_lines, 
                            "",
                            "┌─ OUTPUT ─────────────────────────────────────────┐")
        i <- i + 1
        
        # Process output content
        while (i <= length(lines) && 
               (grepl("^\\s*#>", lines[i]) || grepl("^\\s*\\[1\\]", lines[i]) || 
                grepl("=== .* ===", lines[i]) || grepl("^\\s*[A-Za-z]", lines[i]) ||
                grepl("^\\s*[0-9]", lines[i]) || nchar(trimws(lines[i])) == 0)) {
          output_line <- lines[i]
          formatted_lines <- c(formatted_lines, paste("│", output_line))
          i <- i + 1
          
          # Stop if we hit the next section or code block
          if (i <= length(lines) && (grepl("^##", lines[i]) || grepl("^```", lines[i]))) {
            break
          }
        }
        
        formatted_lines <- c(formatted_lines, 
                            "└──────────────────────────────────────────────────┘",
                            "")
        i <- i - 1  # Adjust for the while loop increment
      }
    }
    # Detect output blocks (lines with === markers)
    else if (grepl("=== .* ===", line)) {
      formatted_lines <- c(formatted_lines, 
                          "",
                          "┌─ RESULTS ────────────────────────────────────────┐")
      
      # Add the header
      header <- gsub("=== (.*) ===", "\\1", line)
      formatted_lines <- c(formatted_lines, paste("│", toupper(header)))
      formatted_lines <- c(formatted_lines, "│")
      
      i <- i + 1
      # Process results content
      while (i <= length(lines) && !grepl("=== .* ===", lines[i]) && !grepl("^##", lines[i])) {
        if (nchar(trimws(lines[i])) > 0) {
          formatted_lines <- c(formatted_lines, paste("│", lines[i]))
        } else {
          formatted_lines <- c(formatted_lines, "│")
        }
        i <- i + 1
        
        # Stop if we hit next section
        if (i <= length(lines) && grepl("^```", lines[i])) {
          break
        }
      }
      
      formatted_lines <- c(formatted_lines, 
                          "└──────────────────────────────────────────────────┘",
                          "")
      i <- i - 1  # Adjust for the while loop increment
    }
    # Handle markdown tables
    else if (grepl("^\\s*\\|.*\\|\\s*$", line)) {
      # Split by | and clean up each cell
      cells <- strsplit(line, "\\|")[[1]]
      cells <- trimws(cells)
      cells <- cells[cells != ""]  # Remove empty cells
      
      # Format as a properly aligned table row
      if (length(cells) > 0) {
        # Pad cells to minimum width for better alignment
        formatted_cells <- sprintf("%-12s", cells)
        formatted_lines <- c(formatted_lines, paste(formatted_cells, collapse = " | "))
      } else {
        formatted_lines <- c(formatted_lines, line)
      }
    }
    # Handle table separator lines
    else if (grepl("^\\s*\\|[-:]*\\|", line)) {
      formatted_lines <- c(formatted_lines, paste(rep("-", 80), collapse = ""))
    }
    # Regular lines
    else {
      formatted_lines <- c(formatted_lines, line)
    }
    
    i <- i + 1
  }
  
  return(paste(formatted_lines, collapse = "\n"))
}


















