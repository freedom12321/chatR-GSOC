#' Advanced Code Generation with Environment Awareness
#'
#' ChatR's most powerful feature - an AI pair programmer that can see your R environment,
#' write production-quality code, and execute it with your permission. This function
#' provides interactive code generation, complete script creation, and intelligent
#' coding assistance tailored to your specific data and requirements.
#'
#' @param query Character. Describe what you want to accomplish in R (required)
#' @param mode Character. Generation mode (default: "interactive"):
#'   \itemize{
#'     \item \code{"interactive"}: Generate code with explanations and examples
#'     \item \code{"script"}: Create complete, professional analysis scripts  
#'     \item \code{"execute"}: Generate and optionally run code immediately
#'   }
#' @param execute_code Logical. Whether to run generated code automatically (default: FALSE)
#' @param save_script Character. File path to save generated script (optional)
#' @param host Character. ChatR backend URL (default: "http://localhost:8000")
#'
#' @return Invisibly returns a list containing:
#'   \itemize{
#'     \item \code{code}: Generated R code as character string
#'     \item \code{explanation}: Text explanation of the approach
#'     \item \code{full_response}: Complete formatted response
#'   }
#'
#' @details
#' This function represents ChatR's advanced AI programming assistant that:
#' \itemize{
#'   \item Sees your R environment (data, objects, loaded packages)
#'   \item Writes context-aware, production-quality R code
#'   \item Provides detailed explanations and best practices
#'   \item Can execute code with your permission for immediate results
#'   \item Generates complete analysis scripts from simple descriptions
#'   \item Offers interactive coding sessions for step-by-step development
#' }
#'
#' The generated code follows R best practices, includes error handling,
#' and is tailored to your specific data structures and analysis needs.
#'
#' @section Modes:
#' \describe{
#'   \item{interactive}{Best for learning and exploring. Generates code with
#'     detailed explanations, examples, and educational content.}
#'   \item{script}{Creates complete, professional scripts ready for production.
#'     Includes package loading, error handling, and full workflows.}
#'   \item{execute}{For quick tasks. Generates code and optionally runs it
#'     immediately for instant results.}
#' }
#'
#' @section Environment Awareness:
#' ChatR automatically detects and considers:
#' \itemize{
#'   \item Available datasets and their structures  
#'   \item Loaded packages and functions
#'   \item Variable types and data characteristics
#'   \item Previous analysis context
#' }
#'
#' @export
#' @family Advanced ChatR Functions
#' @seealso \code{\link{chatr_code_session}} for interactive sessions,
#'   \code{\link{chatr_generate_script}} for script generation
#'
#' @examples
#' \dontrun{
#' # Load some data first
#' data(mtcars)
#' data(iris)
#'
#' # Interactive mode - Learn with explanations
#' chatr_code("create a scatter plot of mpg vs hp with a trend line")
#' chatr_code("show me different ways to handle missing data")
#' 
#' # Script mode - Generate complete analysis
#' chatr_code("comprehensive exploratory data analysis of mtcars", 
#'           mode = "script", save_script = "mtcars_analysis.R")
#' 
#' # Execute mode - Quick results  
#' chatr_code("calculate correlation matrix for numeric variables",
#'           mode = "execute", execute_code = TRUE)
#' 
#' # Advanced examples
#' chatr_code("build a machine learning model to predict species in iris")
#' chatr_code("create publication-quality plots with proper themes")
#' chatr_code("write a function that automatically detects outliers")
#' }
#'
#' @keywords programming datascience AI assistant
chatr_code <- function(query, mode = "interactive", execute_code = FALSE, 
                      save_script = NULL, host = "http://localhost:8000") {
  
  if (!is.character(query) || nchar(trimws(query)) == 0) {
    stop("Please provide a valid query describing what you want to code.")
  }
  
  # Check if ChatR backend is running
  if (!.is_chatr_running(host)) {
    cat("ChatR backend not running. Starting automatically...\n")
    
    started <- .auto_start_chatr_backend()
    if (!started) {
      cat("Failed to auto-start ChatR backend. Please start manually:\n")
      cat("  In terminal: chatr serve\n")
      return(invisible(NULL))
    }
    
    Sys.sleep(3)
    if (!.is_chatr_running(host)) {
      cat("ChatR backend failed to start. Please start manually:\n")
      cat("  In terminal: chatr serve\n")
      return(invisible(NULL))
    }
    
    cat("ChatR backend started successfully!\n")
  }
  
  # Make API call to advanced code generation endpoint
  tryCatch({
    request_data <- list(
      query = query,
      mode = mode,
      execute_code = execute_code,
      environment_context = .get_r_environment_summary()
    )
    
    # Use existing chat endpoint instead of new generate_code endpoint
    response <- .send_chatr_request(
      endpoint = "/chat",
      data = list(query = paste("ADVANCED CODE MODE:", mode, "-", query, "\nEnvironment:", request_data$environment_context)),
      host = host
    )
    
    if (response$status == "success") {
      # Format and display the response
      cat("\n")
      cat("🚀 ChatR Advanced Code Generation\n")
      cat("=" %x% 50, "\n\n")
      
      formatted_response <- .format_chatr_output(response$response)
      cat(formatted_response)
      
      # Extract code from response for execution and saving
      extracted_code <- .extract_code_blocks(response$response)
      
      # Handle code execution if requested
      if (execute_code && !is.null(extracted_code)) {
        cat("\n")
        cat("⚡ EXECUTING CODE...\n")
        cat("=" %x% 50, "\n")
        
        tryCatch({
          # Execute the generated R code
          eval(parse(text = extracted_code), envir = .GlobalEnv)
          cat("✅ Code executed successfully!\n")
        }, error = function(e) {
          cat("❌ Error executing code:", e$message, "\n")
        })
      }
      
      # Save script if requested
      if (!is.null(save_script) && !is.null(extracted_code)) {
        tryCatch({
          writeLines(extracted_code, save_script)
          cat("\n💾 Script saved to:", save_script, "\n")
        }, error = function(e) {
          cat("Error saving script:", e$message, "\n")
        })
      }
      
      cat("\n")
      
      # Return the generated code invisibly for further use
      return(invisible(list(
        code = extracted_code,
        explanation = .extract_explanation(response$response),
        full_response = response$response
      )))
      
    } else {
      cat("Error:", response$error, "\n")
      return(invisible(NULL))
    }
    
  }, error = function(e) {
    cat("Error connecting to ChatR service:", e$message, "\n")
    cat("Tip: Make sure ChatR is running with: chatr serve\n")
    return(invisible(NULL))
  })
}

#' Interactive AI Programming Session
#'
#' Launch an interactive coding session with ChatR's AI programming assistant.
#' In this mode, ChatR can see your R environment, understand your data, and
#' write custom code step-by-step based on your natural language requests.
#' Perfect for exploratory programming, learning, and iterative development.
#'
#' @param host Character. ChatR backend URL (default: "http://localhost:8000")
#'
#' @details
#' This function starts an interactive command-line session where you can:
#' \itemize{
#'   \item Request code generation using natural language
#'   \item Choose whether to execute generated code immediately
#'   \item Get step-by-step programming guidance  
#'   \item Receive context-aware suggestions based on your data
#'   \item Learn R programming through AI-generated examples
#' }
#'
#' ChatR continuously monitors your R environment, so it can reference your
#' specific datasets, variables, and loaded packages when generating code.
#'
#' @section Session Commands:
#' \describe{
#'   \item{help}{Show available commands and usage examples}
#'   \item{env}{Display current R environment summary}
#'   \item{quit, exit, q}{End the interactive session}
#' }
#'
#' @section Execution Modes:
#' For each code generation request, you can choose:
#' \describe{
#'   \item{y (yes)}{Execute all generated code automatically}
#'   \item{n (no)}{Show code but don't execute anything}
#'   \item{ask}{Prompt for confirmation before each code block}
#' }
#'
#' @return NULL (invisible). The function runs interactively until you quit.
#' 
#' @export
#' @family Advanced ChatR Functions
#' @seealso \code{\link{chatr_code}} for single requests,
#'   \code{\link{chatr_generate_script}} for script generation
#'
#' @examples
#' \dontrun{
#' # Start interactive session
#' chatr_code_session()
#' 
#' # Example session flow:
#' # > What would you like me to code? 
#' # create a histogram of mpg from mtcars
#' # > Should I execute the code? (y/n/ask): ask
#' # [ChatR shows generated code]
#' # > Execute this code? (y/n): y
#' # [Code runs and creates histogram]
#' }
#' 
#' @keywords programming interactive AI assistant session
chatr_code_session <- function(host = "http://localhost:8000") {
  
  cat("🎯 ChatR Interactive Code Session\n")
  cat("="  %x% 50, "\n")
  cat("I can see your R environment and write/execute code for you!\n")
  cat("Type 'quit', 'exit', or 'q' to end the session.\n")
  cat("Type 'help' for available commands.\n\n")
  
  # Show current environment
  .show_environment_summary()
  
  while (TRUE) {
    cat("\n💻 What would you like me to code? ")
    user_input <- readline()
    user_input <- trimws(user_input)
    
    if (tolower(user_input) %in% c("quit", "exit", "q")) {
      cat("👋 Goodbye! Happy coding!\n")
      break
    }
    
    if (tolower(user_input) == "help") {
      .show_session_help()
      next
    }
    
    if (tolower(user_input) == "env") {
      .show_environment_summary()
      next
    }
    
    if (nchar(user_input) == 0) {
      next
    }
    
    # Ask if user wants to execute the code
    cat("🔧 Should I execute the code I generate? (y/n/ask): ")
    exec_choice <- readline()
    exec_choice <- tolower(trimws(exec_choice))
    
    execute_mode <- switch(exec_choice,
      "y" = TRUE,
      "yes" = TRUE,
      "n" = FALSE,
      "no" = FALSE,
      "ask" = "ask",
      "ask" # default
    )
    
    # Generate and potentially execute code
    result <- chatr_code(
      query = user_input,
      mode = "interactive",
      execute_code = (execute_mode == TRUE),
      host = host
    )
    
    # If execution mode is "ask", prompt for each code block
    if (execute_mode == "ask" && !is.null(result$code)) {
      cat("\n🤔 Execute this code? (y/n): ")
      if (tolower(trimws(readline())) %in% c("y", "yes")) {
        tryCatch({
          eval(parse(text = result$code), envir = .GlobalEnv)
          cat("✅ Code executed successfully!\n")
        }, error = function(e) {
          cat("❌ Error executing code:", e$message, "\n")
        })
      }
    }
  }
}

#' Professional R Script Generation
#'
#' Generate complete, production-ready R analysis scripts using AI. This function
#' creates comprehensive, well-documented scripts that include package loading,
#' error handling, data processing, analysis, and results output. Perfect for
#' creating reproducible research workflows and professional data analysis projects.
#'
#' @param task Character. High-level description of the analysis or task to accomplish (required)
#' @param dataset_name Character. Name of the dataset in your environment to analyze (optional)
#' @param output_file Character. File path where the script should be saved (optional)
#' @param include_comments Logical. Include detailed explanatory comments (default: TRUE)
#' @param host Character. ChatR backend URL (default: "http://localhost:8000")
#'
#' @return Invisibly returns the generated script content as character string
#'
#' @details
#' This function generates professional-quality R scripts that include:
#' \itemize{
#'   \item Automatic package installation and loading with error checking
#'   \item Data import and validation sections
#'   \item Comprehensive exploratory data analysis
#'   \item Statistical analysis and modeling appropriate to the task
#'   \item Professional visualizations with proper themes and labels
#'   \item Results export and saving functionality
#'   \item Detailed comments explaining each step and decision
#'   \item Error handling and input validation
#'   \item Reproducible research structure
#' }
#'
#' The generated scripts follow R best practices and coding standards,
#' making them suitable for production use, academic research, and
#' collaborative projects.
#'
#' @section Script Structure:
#' Generated scripts typically include these sections:
#' \describe{
#'   \item{Setup}{Package loading, environment configuration}
#'   \item{Data Import}{Data loading and initial validation}
#'   \item{Data Preparation}{Cleaning, transformation, feature engineering}
#'   \item{Exploratory Analysis}{Summary statistics, initial visualizations}
#'   \item{Main Analysis}{Core statistical analysis or modeling}
#'   \item{Results & Visualization}{Final plots, tables, summaries}
#'   \item{Export}{Save results, plots, and processed data}
#' }
#'
#' @export
#' @family Advanced ChatR Functions
#' @seealso \code{\link{chatr_code}} for interactive code generation,
#'   \code{\link{chatr_code_session}} for step-by-step development
#'
#' @examples
#' \dontrun{
#' # Load some data first
#' data(mtcars)
#' data(iris)
#'
#' # Generate comprehensive analysis script
#' chatr_generate_script(
#'   task = "complete exploratory data analysis with machine learning",
#'   dataset_name = "mtcars", 
#'   output_file = "mtcars_analysis.R"
#' )
#'
#' # Generate script for specific analysis  
#' chatr_generate_script(
#'   task = "linear regression analysis with assumption checking",
#'   dataset_name = "iris",
#'   output_file = "iris_regression.R",
#'   include_comments = TRUE
#' )
#'
#' # Generate general data science workflow
#' chatr_generate_script(
#'   task = "automated data quality assessment and cleaning pipeline",
#'   output_file = "data_quality_pipeline.R"
#' )
#' }
#'
#' @keywords programming script generation workflow analysis
chatr_generate_script <- function(task, dataset_name = NULL, output_file = NULL,
                                 include_comments = TRUE, host = "http://localhost:8000") {
  
  cat("📝 Generating R Analysis Script\n")
  cat("="  %x% 40, "\n")
  cat("Task:", task, "\n")
  if (!is.null(dataset_name)) cat("Dataset:", dataset_name, "\n")
  cat("\n")
  
  # Enhanced query for script generation
  enhanced_query <- paste(
    "Generate a complete, professional R script for:",
    task,
    if (!is.null(dataset_name)) paste("Using dataset:", dataset_name),
    if (include_comments) "Include detailed comments and explanations.",
    "Make it production-ready with error handling and best practices."
  )
  
  result <- chatr_code(
    query = enhanced_query,
    mode = "script",
    execute_code = FALSE,
    save_script = output_file,
    host = host
  )
  
  if (!is.null(output_file)) {
    cat("📁 Script saved to:", output_file, "\n")
  }
  
  return(invisible(result))
}

# Helper functions

.get_r_environment_summary <- function() {
  env_objects <- ls(envir = .GlobalEnv)
  
  if (length(env_objects) == 0) {
    return("No objects in R environment.")
  }
  
  summary_parts <- c("Available R objects:")
  
  for (obj_name in env_objects[1:min(10, length(env_objects))]) {
    tryCatch({
      obj <- get(obj_name, envir = .GlobalEnv)
      
      if (is.data.frame(obj)) {
        summary_parts <- c(summary_parts, 
          sprintf("- %s: data.frame (%d x %d)", obj_name, nrow(obj), ncol(obj)))
      } else if (is.matrix(obj)) {
        summary_parts <- c(summary_parts,
          sprintf("- %s: matrix (%d x %d)", obj_name, nrow(obj), ncol(obj)))
      } else if (is.vector(obj) && length(obj) > 1) {
        summary_parts <- c(summary_parts,
          sprintf("- %s: %s vector (length %d)", obj_name, class(obj)[1], length(obj)))
      } else {
        summary_parts <- c(summary_parts,
          sprintf("- %s: %s", obj_name, class(obj)[1]))
      }
    }, error = function(e) {
      summary_parts <<- c(summary_parts, sprintf("- %s: (error accessing)", obj_name))
    })
  }
  
  if (length(env_objects) > 10) {
    summary_parts <- c(summary_parts, sprintf("... and %d more objects", length(env_objects) - 10))
  }
  
  return(paste(summary_parts, collapse = "\n"))
}

.show_environment_summary <- function() {
  cat("📊 Current R Environment:\n")
  cat("-" %x% 30, "\n")
  cat(.get_r_environment_summary(), "\n")
}

.show_session_help <- function() {
  cat("\n🆘 ChatR Code Session Help\n")
  cat("="  %x% 30, "\n")
  cat("Available commands:\n")
  cat("• help     - Show this help\n")
  cat("• env      - Show current R environment\n")
  cat("• quit/q   - End session\n\n")
  cat("Example requests:\n")
  cat("• 'create a scatter plot of mpg vs hp'\n")
  cat("• 'calculate correlation between all numeric columns'\n")
  cat("• 'clean the data by removing missing values'\n")
  cat("• 'create a new variable combining existing ones'\n")
  cat("• 'run a linear regression model'\n")
}

# Helper functions - reused from main chatr package

.is_chatr_running <- function(host) {
  tryCatch({
    response <- httr::GET(paste0(host, "/health"), httr::timeout(2))
    httr::status_code(response) == 200
  }, error = function(e) FALSE)
}

.send_chatr_request <- function(endpoint, data, host) {
  tryCatch({
    response <- httr::POST(
      url = paste0(host, endpoint),
      body = jsonlite::toJSON(data, auto_unbox = TRUE),
      httr::content_type("application/json"),
      httr::timeout(120)
    )
    
    if (httr::status_code(response) == 200) {
      return(httr::content(response, as = "parsed"))
    } else {
      return(list(
        status = "error",
        error = paste("HTTP", httr::status_code(response))
      ))
    }
  }, error = function(e) {
    list(
      status = "error",
      error = as.character(e)
    )
  })
}

.auto_start_chatr_backend <- function() {
  tryCatch({
    # Try different ways to find and start ChatR
    chatr_paths <- c(
      Sys.which("chatr"),  # System PATH
      path.expand("~/chatR-GSOC/venv/bin/chatr"),  # User's home directory
      path.expand("~/Documents/chatR-GSOC/venv/bin/chatr"),  # Common location
      "/usr/local/bin/chatr",  # System installation
      paste0(Sys.getenv("HOME"), "/.local/bin/chatr")  # Local user installation
    )
    
    chatr_cmd <- ""
    for (path in chatr_paths) {
      if (path != "" && file.exists(path)) {
        chatr_cmd <- path
        break
      }
    }
    
    if (chatr_cmd == "") {
      message("ChatR command not found. Please ensure:")
      message("  1. ChatR is installed: pip install -e .")
      message("  2. Virtual environment is activated")
      return(FALSE)
    }
    
    message(paste("Found ChatR at:", chatr_cmd))
    
    # Start ChatR backend in background with proper environment
    if (.Platform$OS.type == "unix") {
      # Unix/Mac - use bash to properly handle background process
      cmd <- paste0("bash -c '", chatr_cmd, " serve --port 8000 > /tmp/chatr.log 2>&1 &'")
      system(cmd, wait = FALSE)
    } else {
      # Windows  
      cmd <- paste0("start /b ", chatr_cmd, " serve --port 8000")
      system(cmd, wait = FALSE)
    }
    
    message("ChatR backend starting... (check /tmp/chatr.log for details)")
    return(TRUE)
    
  }, error = function(e) {
    message("Error starting ChatR backend: ", e$message)
    return(FALSE)
  })
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
    # Regular lines
    else {
      formatted_lines <- c(formatted_lines, line)
    }
    
    i <- i + 1
  }
  
  return(paste(formatted_lines, collapse = "\n"))
}

.extract_code_blocks <- function(response) {
  # Extract R code blocks from LLM response, filtering out output/error blocks
  
  if (is.null(response) || response == "") return(NULL)
  
  # First try standard markdown code blocks  
  # Use a pattern that works with multiline content
  code_pattern <- "```r[\\s\\S]*?```"
  matches <- regmatches(response, gregexpr(code_pattern, response, perl = TRUE))[[1]]
  
  if (length(matches) > 0) {
    # Extract just the code content (remove ```r and ```)
    code_content <- gsub("```r\\s*|```\\s*$", "", matches, perl = TRUE)
    
    # Clean up the extracted code - remove any non-R lines
    clean_lines <- character()
    for (block in code_content) {
      lines <- strsplit(block, "\\n")[[1]]
      for (line in lines) {
        trimmed <- trimws(line)
        # Keep R code lines, skip empty lines and system messages
        if (nchar(trimmed) > 0 && 
            !grepl("^(Attaching package|The following objects|downloaded|trying URL)", trimmed) &&
            (grepl("^#|^[a-zA-Z_][a-zA-Z0-9_]*\\s*(<-|=|\\()|^library\\(|^data\\(|%>%|\\+$", trimmed) ||
             grepl("^[a-zA-Z_]", trimmed))) {
          clean_lines <- c(clean_lines, line)
        }
      }
    }
    
    if (length(clean_lines) > 0) {
      return(paste(clean_lines, collapse = "\n"))
    }
  }
  
  # Try formatted blocks (ChatR's custom format)
  lines <- strsplit(response, "\n")[[1]]
  clean_code_lines <- character()
  in_code_block <- FALSE
  current_block_lines <- character()
  
  for (i in seq_along(lines)) {
    line <- lines[i]
    
    # Check if we're starting a code block
    if (grepl("┌─ R CODE", line)) {
      in_code_block <- TRUE
      current_block_lines <- character()
      next
    }
    
    # End of code block
    if (grepl("└─", line) && in_code_block) {
      in_code_block <- FALSE
      
      # Analyze the collected block to determine if it contains actual R code
      if (length(current_block_lines) > 0) {
        block_content <- paste(current_block_lines, collapse = "\n")
        
        # Skip if this block appears to be output/error content
        # Check if the block contains system messages or error output patterns
        is_output_block <- any(grepl("^(The downloaded|trying URL|Content type|downloaded [0-9]|==+|Error in|Warning:|gc trigger)", current_block_lines, ignore.case = TRUE)) ||
                          any(grepl("^/var/folders|^/tmp/|^https?://", current_block_lines)) ||
                          any(grepl("used \\(Mb\\)|Ncells|Vcells|limit \\(Mb\\)", current_block_lines)) ||
                          all(grepl("^\\s*$|^\\[1\\]|^NULL", current_block_lines))
        
        # Check context: look at surrounding lines to see if this follows output/error markers
        context_suggests_output <- FALSE
        if (i > 5) {
          context_lines <- lines[max(1, i-10):(i-1)]
          context_suggests_output <- any(grepl("\\*\\*Output:\\*\\*|\\*\\*Error:\\*\\*|\\*\\*Messages:\\*\\*", context_lines, ignore.case = TRUE))
        }
        
        # Only include this block if it looks like actual R code
        if (!is_output_block && !context_suggests_output) {
          # Filter individual lines to remove any remaining non-code content
          filtered_lines <- character()
          for (code_line in current_block_lines) {
            trimmed_line <- trimws(code_line)
            # Keep lines that look like R code (assignments, function calls, comments)
            if (nchar(trimmed_line) > 0 && 
                (grepl("^#|^[a-zA-Z_][a-zA-Z0-9_]*\\s*(<-|=|\\()|^library\\(|^data\\(|^install\\.packages|^[a-zA-Z0-9_]+\\s*\\(", trimmed_line) ||
                 grepl("\\+$|^[a-zA-Z_]", trimmed_line))) {
              filtered_lines <- c(filtered_lines, code_line)
            }
          }
          
          if (length(filtered_lines) > 0) {
            clean_code_lines <- c(clean_code_lines, filtered_lines)
          }
        }
      }
      current_block_lines <- character()
      next
    }
    
    # Collect lines within code blocks
    if (in_code_block && grepl("^│", line)) {
      code_line <- gsub("^│\\s?", "", line)
      current_block_lines <- c(current_block_lines, code_line)
    }
  }
  
  if (length(clean_code_lines) > 0) {
    return(paste(clean_code_lines, collapse = "\n"))
  }
  
  return(NULL)
}

.extract_explanation <- function(response) {
  # Extract explanation text (non-code) from response
  
  if (is.null(response) || response == "") return(NULL)
  
  # Remove code blocks to get just explanation
  explanation <- gsub("```r.*?```", "", response, perl = TRUE)
  explanation <- gsub("```.*?```", "", explanation, perl = TRUE)
  
  # Clean up extra whitespace
  explanation <- gsub("\\n\\s*\\n\\s*\\n", "\\n\\n", trimws(explanation), perl = TRUE)
  
  return(if (nchar(explanation) > 0) explanation else NULL)
}

# String repetition helper
`%x%` <- function(x, n) {
  paste(rep(x, n), collapse = "")
}









