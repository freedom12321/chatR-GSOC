#' Simple Chat/REPL Interface for ChatR
#'
#' Provides an interactive chat interface within R console.
#' Users can type queries and get responses while maintaining context.
#'
#' @param host ChatR server host (default: "http://localhost:8001")
#' @param welcome_message Custom welcome message
#' @param max_history Maximum number of conversation turns to keep
#' @export
#' @examples
#' \dontrun{
#' # Start interactive chat session
#' chatr_repl()
#' 
#' # Start with custom host
#' chatr_repl(host = "http://localhost:8002")
#' }
chatr_repl <- function(host = "http://localhost:8001", 
                       welcome_message = NULL, 
                       max_history = 10) {
  
  # Check if ChatR backend is running, auto-start if needed (same as chatr function)
  if (!.is_chatr_running(host)) {
    message("ChatR backend not running. Starting automatically...")
    
    # Try to auto-start the backend
    started <- .auto_start_chatr_backend()
    
    if (!started) {
      message("Failed to auto-start ChatR backend. Please start manually:")
      message("  In terminal: chatr serve")
      return(invisible(NULL))
    }
    
    # Wait for startup
    Sys.sleep(3)
    
    if (!.is_chatr_running(host)) {
      message("ChatR backend failed to start. Please start manually:")
      message("  In terminal: chatr serve") 
      return(invisible(NULL))
    }
  }
  
  # Initialize conversation history
  conversation_history <- list()
  
  # Welcome message
  if (is.null(welcome_message)) {
    welcome_message <- paste0(
      "\n", crayon::blue("=== ChatR Interactive REPL ==="), "\n",
      crayon::green("Connected to: "), host, "\n",
      crayon::yellow("Type your R questions and get instant help!"), "\n",
      crayon::cyan("Commands:"), "\n",
      "  ", crayon::bold("/help"), " - Show help\n",
      "  ", crayon::bold("/clear"), " - Clear conversation history\n",
      "  ", crayon::bold("/history"), " - Show conversation history\n",
      "  ", crayon::bold("/quit"), " or ", crayon::bold("/exit"), " - Exit chat\n",
      crayon::magenta("Press Enter twice for multiline input"), "\n",
      crayon::green("Ready! Ask me anything about R..."), "\n"
    )
  }
  
  cat(welcome_message)
  
  # Main REPL loop
  while (TRUE) {
    # Get user input
    tryCatch({
      # Prompt
      cat(crayon::blue("\n> "))
      user_input <- readline()
      
      # Handle empty input
      if (is.null(user_input) || nchar(trimws(user_input)) == 0) {
        next
      }
      
      # Handle commands
      if (startsWith(user_input, "/")) {
        command_result <- .handle_repl_command(user_input, conversation_history, host)
        
        if (command_result$action == "quit") {
          break
        } else if (command_result$action == "clear") {
          conversation_history <- list()
          cat(crayon::green("Conversation history cleared.\n"))
          next
        } else if (command_result$action == "history") {
          .show_conversation_history(conversation_history)
          next
        } else if (command_result$action == "help") {
          .show_repl_help()
          next
        }
      }
      
      # Handle multiline input (experimental)
      if (endsWith(trimws(user_input), "\\")) {
        cat(crayon::yellow("... "))
        additional_input <- readline()
        user_input <- paste0(gsub("\\\\$", "", user_input), "\n", additional_input)
      }
      
      # Send query to ChatR
      cat(crayon::yellow("Thinking...\n"))
      
      response <- tryCatch({
        chatr(user_input, host = host, launch_ui = FALSE)
      }, error = function(e) {
        crayon::red(paste("Error:", e$message))
      })
      
      if (!is.null(response) && !inherits(response, "try-error")) {
        # Display response
        cat(crayon::green("ChatR: "), response, "\n")
        
        # Add to conversation history
        conversation_history <- append(conversation_history, list(list(
          timestamp = Sys.time(),
          query = user_input,
          response = response
        )))
        
        # Limit history size
        if (length(conversation_history) > max_history) {
          conversation_history <- conversation_history[-(1:(length(conversation_history) - max_history))]
        }
      }
      
    }, interrupt = function(e) {
      cat(crayon::yellow("\nUse /quit to exit gracefully.\n"))
    }, error = function(e) {
      cat(crayon::red("Error in REPL: "), e$message, "\n")
    })
  }
  
  cat(crayon::blue("Thanks for using ChatR REPL! Goodbye!\n"))
  invisible(conversation_history)
}

# Helper function to handle REPL commands
.handle_repl_command <- function(command, history, host) {
  command <- tolower(trimws(command))
  
  if (command %in% c("/quit", "/exit", "/q")) {
    return(list(action = "quit"))
  } else if (command == "/clear") {
    return(list(action = "clear"))
  } else if (command == "/history") {
    return(list(action = "history"))
  } else if (command == "/help") {
    return(list(action = "help"))
  } else if (command == "/status") {
    # Check server status
    tryCatch({
      response <- httr::GET(paste0(host, "/health"))
      if (httr::status_code(response) == 200) {
        cat(crayon::green("Server status: Online\n"))
      } else {
        cat(crayon::red("Server status: Error\n"))
      }
    }, error = function(e) {
      cat(crayon::red("Server status: Offline\n"))
    })
    return(list(action = "continue"))
  } else {
    cat(crayon::red("Unknown command: "), command, "\n")
    cat(crayon::cyan("Use /help to see available commands.\n"))
    return(list(action = "continue"))
  }
}

# Helper function to show conversation history
.show_conversation_history <- function(history) {
  if (length(history) == 0) {
    cat(crayon::yellow("No conversation history.\n"))
    return()
  }
  
  cat(crayon::blue("=== Conversation History ===\n"))
  for (i in seq_along(history)) {
    entry <- history[[i]]
    timestamp <- format(entry$timestamp, "%H:%M:%S")
    cat(crayon::cyan(paste0("[", timestamp, "]")), 
        crayon::bold("You:"), entry$query, "\n")
    cat(crayon::cyan(paste0("[", timestamp, "]")), 
        crayon::green("ChatR:"), substr(entry$response, 1, 100), "...\n\n")
  }
}

# Helper function to show REPL help
.show_repl_help <- function() {
  cat(crayon::blue("=== ChatR REPL Help ===\n"))
  cat(crayon::green("Available commands:\n"))
  cat("  ", crayon::bold("/help"), " - Show this help message\n")
  cat("  ", crayon::bold("/clear"), " - Clear conversation history\n")
  cat("  ", crayon::bold("/history"), " - Show conversation history\n")
  cat("  ", crayon::bold("/status"), " - Check server status\n")
  cat("  ", crayon::bold("/quit, /exit, /q"), " - Exit REPL\n")
  cat(crayon::yellow("\nTips:\n"))
  cat("- Ask natural language questions about R\n")
  cat("- Context is maintained across questions\n")
  cat("- Use Ctrl+C then /quit for clean exit\n")
  cat("- End lines with \\\\ for multiline input\n")
}

#' Quick start ChatR REPL
#'
#' Convenience function to quickly start ChatR REPL with default settings
#'
#' @export
chatr_chat <- function() {
  chatr_repl()
}








