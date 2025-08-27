#' ChatR RStudio Add-ins
#'
#' These functions provide RStudio add-in integration for ChatR.
#' They can be accessed through the RStudio Addins menu.

#' Launch ChatR Interactive Assistant
#'
#' @export
chatr_addin <- function() {
  chatr()
}

#' Get Help for Function at Cursor
#'
#' @export
chatr_help_cursor <- function() {
  if (!rstudioapi::isAvailable()) {
    message("This function requires RStudio")
    return()
  }
  
  # Get current cursor position and context
  context <- rstudioapi::getActiveDocumentContext()
  
  if (is.null(context)) {
    message("No active document found")
    return()
  }
  
  # Get current line and cursor position
  current_line <- context$contents[context$selection[[1]]$range$start[1]]
  cursor_col <- context$selection[[1]]$range$start[2]
  
  # Extract function name at cursor (simplified)
  # This is a basic implementation - could be much more sophisticated
  words <- strsplit(current_line, "[^a-zA-Z0-9_.]")[[1]]
  words <- words[words != ""]
  
  if (length(words) > 0) {
    # Find the word closest to cursor position
    # For simplicity, just take the last word that could be a function
    func_name <- tail(words, 1)
    
    if (nchar(func_name) > 0) {
      message(paste("Getting help for:", func_name))
      help_explain(func_name)
    } else {
      message("No function found at cursor")
    }
  }
}

#' Get Code Suggestions for Current Context
#'
#' @export
chatr_suggest_code <- function() {
  if (!rstudioapi::isAvailable()) {
    message("This function requires RStudio")
    return()
  }
  
  context <- rstudioapi::getActiveDocumentContext()
  
  if (is.null(context)) {
    message("No active document found")
    return()
  }
  
  # Get current document content up to cursor
  current_row <- context$selection[[1]]$range$start[1]
  current_col <- context$selection[[1]]$range$start[2]
  
  # Get context around cursor (previous few lines)
  start_row <- max(1, current_row - 3)
  context_lines <- context$contents[start_row:current_row]
  
  # Build context prompt
  code_context <- paste(context_lines, collapse = "\n")
  
  if (nchar(trimws(code_context)) > 0) {
    prompt <- paste("Based on this R code context, suggest what I might want to write next:\n\n```r\n", 
                    code_context, "\n```\n\nProvide a brief, practical suggestion.")
    
    # Get suggestion
    suggestion <- chatr(prompt, launch_ui = FALSE)
    
    # Show in a dialog or console
    if (rstudioapi::isAvailable()) {
      rstudioapi::showDialog("ChatR Code Suggestion", suggestion)
    } else {
      message("ChatR Suggestion:\n", suggestion)
    }
  } else {
    message("No code context found")
  }
}

#' Analyze Selected R Code
#'
#' @export
chatr_analyze_selection <- function() {
  if (!rstudioapi::isAvailable()) {
    message("This function requires RStudio")
    return()
  }
  
  context <- rstudioapi::getActiveDocumentContext()
  
  if (is.null(context)) {
    message("No active document found")
    return()
  }
  
  # Get selected text
  selection <- context$selection[[1]]
  selected_text <- selection$text
  
  if (nchar(trimws(selected_text)) > 0) {
    message("Analyzing selected code...")
    result <- analyze_code(selected_text)
  } else {
    # If no selection, analyze current line
    current_row <- context$selection[[1]]$range$start[1]
    current_line <- context$contents[current_row]
    
    if (nchar(trimws(current_line)) > 0) {
      message("Analyzing current line...")
      result <- analyze_code(current_line)
    } else {
      message("No code selected or found on current line")
    }
  }
}

#' Smart Code Completion Helper
#'
#' This function provides intelligent code suggestions based on context.
#' It's designed to be called from custom key bindings.
#'
#' @export
chatr_smart_complete <- function() {
  if (!rstudioapi::isAvailable()) {
    return()
  }
  
  context <- rstudioapi::getActiveDocumentContext()
  
  if (is.null(context)) {
    return()
  }
  
  # Get current position
  current_row <- context$selection[[1]]$range$start[1]
  current_col <- context$selection[[1]]$range$start[2]
  current_line <- context$contents[current_row]
  
  # Get text before cursor on current line
  text_before_cursor <- substr(current_line, 1, current_col - 1)
  
  # Simple pattern matching for common R patterns
  if (grepl("\\$\\s*$", text_before_cursor)) {
    # User typed object$ - suggest column names or methods
    obj_name <- gsub(".*?([a-zA-Z0-9_.]+)\\$\\s*$", "\\1", text_before_cursor)
    prompt <- paste("I have an R object called '", obj_name, "' and I typed '$'. What are likely completions? Give me just the top 3 most common options, one per line.")
    suggestion <- chatr(prompt, launch_ui = FALSE)
    
    # Show suggestion in status bar or as tooltip
    message("ChatR suggests: ", suggestion)
  } else if (grepl("\\s+(lm|glm|ggplot)\\s*\\($", text_before_cursor)) {
    # User started a common function - suggest parameters
    func_name <- gsub(".*\\s+([a-zA-Z]+)\\s*\\($", "\\1", text_before_cursor)
    prompt <- paste("I'm calling the", func_name, "function in R. What are the most important parameters I should consider? Give a brief example.")
    suggestion <- chatr(prompt, launch_ui = FALSE)
    
    message("ChatR suggests: ", suggestion)
  }
}


















