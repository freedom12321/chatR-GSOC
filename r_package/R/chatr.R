#' ChatR: An Intelligent R Assistant
#'
#' @description
#' ChatR is a local AI assistant for R programmers that provides intelligent
#' help, code suggestions, and documentation lookup.
#'
#' @docType package
#' @name chatr-package
NULL

#' Chat with ChatR Assistant
#'
#' Start an interactive chat session with the ChatR assistant.
#'
#' @param query Character. Optional initial query to ask ChatR.
#' @param host Character. ChatR backend host (default: "http://localhost:8001").
#' @param launch_ui Logical. Whether to launch the Shiny UI (default: TRUE in RStudio).
#'
#' @return Character response from ChatR or launches UI
#' @export
#'
#' @examples
#' \dontrun{
#' # Ask a quick question
#' chatr("How do I create a linear regression in R?")
#' 
#' # Launch interactive UI
#' chatr()
#' }
chatr <- function(query = NULL, host = "http://localhost:8001", launch_ui = NULL) {
  
  # Determine if we should launch UI
  if (is.null(launch_ui)) {
    launch_ui <- rstudioapi::isAvailable() && is.null(query)
  }
  
  # Check if ChatR backend is running, auto-start if needed
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
    
    message("ChatR backend started successfully!")
  }
  
  if (!is.null(query)) {
    # Direct query mode
    response <- .query_chatr(query, host)
    cat(response, "\n")
    return(invisible(response))
  } else if (launch_ui) {
    # Launch Shiny UI
    .launch_chatr_ui(host)
  } else {
    # Console chat mode
    .console_chat(host)
  }
}

#' Get Help with R Function
#'
#' Get intelligent help and examples for an R function using ChatR.
#'
#' @param func Character. Function name to get help for.
#' @param package Character. Package name (optional).
#' @param host Character. ChatR backend host.
#'
#' @return Character response with function help
#' @export
#'
#' @examples
#' \dontrun{
#' help_explain("lm")
#' help_explain("ggplot", "ggplot2")
#' }
help_explain <- function(func, package = NULL, host = "http://localhost:8001") {
  
  if (!.is_chatr_running(host)) {
    stop("ChatR backend is not running. Please start it first.")
  }
  
  query <- if (is.null(package)) {
    paste("Help me understand the R function:", func)
  } else {
    paste("Help me understand the R function:", func, "from package", package)
  }
  
  response <- .query_chatr(query, host)
  cat(response, "\n")
  invisible(response)
}

#' Run ChatR Code Analysis
#'
#' Analyze R code and get suggestions for improvement.
#'
#' @param code Character. R code to analyze.
#' @param host Character. ChatR backend host.
#'
#' @return List with analysis results
#' @export
#'
#' @examples
#' \dontrun{
#' analyze_code("
#'   data <- read.csv('file.csv')
#'   plot(data$x, data$y)
#' ")
#' }
analyze_code <- function(code, host = "http://localhost:8001") {
  
  if (!.is_chatr_running(host)) {
    stop("ChatR backend is not running. Please start it first.")
  }
  
  # Send code analysis request
  response <- .send_chatr_request(
    endpoint = "/analyze",
    data = list(code = code),
    host = host
  )
  
  if (response$status == "success") {
    cat("Code Analysis:\n")
    cat(response$analysis, "\n")
    return(invisible(response))
  } else {
    stop("Analysis failed: ", response$error)
  }
}

#' Start ChatR Backend Server
#'
#' Start the ChatR backend server for the R package to communicate with.
#'
#' @param port Integer. Port to run the server on (default: 8001).
#' @param host Character. Host to bind to (default: "localhost").
#'
#' @return Invisible NULL
#' @export
chatr_serve <- function(port = 8001, host = "localhost") {
  message("Starting ChatR backend server...")
  
  # Find the correct ChatR command path
  chatr_paths <- c(
    "/Users/lihanxia/Documents/chatR-GSOC/venv/bin/chatr",
    paste0(Sys.getenv("HOME"), "/Documents/chatR-GSOC/venv/bin/chatr"),
    paste0(getwd(), "/venv/bin/chatr"),
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
    message("ChatR command not found in expected locations.")
    message("Trying alternative Python approach...")
    
    # Try alternative Python approach
    python_paths <- c(
      "/Users/lihanxia/Documents/chatR-GSOC/venv/bin/python",
      paste0(Sys.getenv("HOME"), "/Documents/chatR-GSOC/venv/bin/python"),
      "python3",
      "python"
    )
    
    for (python_path in python_paths) {
      if (python_path != "" && (file.exists(python_path) || Sys.which(python_path) != "")) {
        chatr_cmd <- paste(python_path, "-m chatr.cli.main serve --host", host, "--port", port)
        break
      }
    }
  } else {
    chatr_cmd <- paste(chatr_cmd, "serve --host", host, "--port", port)
  }
  
  if (chatr_cmd == "") {
    stop("Cannot find ChatR installation. Please ensure ChatR is installed properly.")
  }
  
  message("Starting server with command: ", chatr_cmd)
  
  # Try to start the server (simple approach that works)
  if (.Platform$OS.type == "unix") {
    system(paste(chatr_cmd, "> /tmp/chatr_serve.log 2>&1"), wait = FALSE)
  } else {
    shell(paste("start /b", chatr_cmd), wait = FALSE)
  }
  
  # Wait a moment for server to start
  message("Waiting for server to start...")
  Sys.sleep(3)
  
  # Check if server started successfully
  server_url <- paste0("http://", host, ":", port)
  if (.is_chatr_running(server_url)) {
    message("✅ ChatR server started successfully at ", server_url)
  } else {
    message("⚠️ Server startup may need more time. Check /tmp/chatr_serve.log for details.")
    message("Try running your ChatR commands - the server might still be starting.")
  }
  
  invisible(NULL)
}

# Internal functions

.is_chatr_running <- function(host) {
  tryCatch({
    response <- httr::GET(paste0(host, "/health"), httr::timeout(2))
    httr::status_code(response) == 200
  }, error = function(e) FALSE)
}

.query_chatr <- function(query, host) {
  response <- .send_chatr_request(
    endpoint = "/chat",
    data = list(query = query),
    host = host
  )
  
  if (response$status == "success") {
    return(response$response)
  } else {
    return(paste("Error:", response$error))
  }
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

.console_chat <- function(host) {
  cat("ChatR Console Mode\n")
  cat("Type 'quit' or 'exit' to leave.\n\n")
  
  while (TRUE) {
    query <- readline("You: ")
    
    if (tolower(trimws(query)) %in% c("quit", "exit", "q")) {
      cat("Goodbye!\n")
      break
    }
    
    if (nchar(trimws(query)) > 0) {
      response <- .query_chatr(query, host)
      cat("ChatR:", response, "\n\n")
    }
  }
}

.launch_chatr_ui <- function(host) {
  # This will be implemented as a Shiny gadget
  message("Launching ChatR UI...")
  
  ui <- miniUI::miniPage(
    miniUI::gadgetTitleBar("ChatR Assistant"),
    miniUI::miniContentPanel(
      shiny::div(
        style = "height: 400px; overflow-y: scroll; border: 1px solid #ccc; padding: 10px; margin-bottom: 10px;",
        id = "chatHistory",
        shiny::div("Welcome to ChatR! Ask me anything about R programming.")
      ),
      shiny::fluidRow(
        shiny::column(10,
          shiny::textInput("queryInput", NULL, placeholder = "Ask ChatR anything...")
        ),
        shiny::column(2,
          shiny::actionButton("sendBtn", "Send", class = "btn-primary")
        )
      )
    )
  )
  
  server <- function(input, output, session) {
    
    chat_history <- shiny::reactiveVal(list())
    
    send_query <- function() {
      query <- input$queryInput
      if (nchar(trimws(query)) > 0) {
        # Add user message
        history <- chat_history()
        history <- append(history, list(list(role = "user", content = query)))
        
        # Get response
        response <- .query_chatr(query, host)
        history <- append(history, list(list(role = "assistant", content = response)))
        
        chat_history(history)
        
        # Clear input
        shiny::updateTextInput(session, "queryInput", value = "")
        
        # Update chat display
        chat_html <- .format_chat_history(history)
        shiny::removeUI("#chatHistory")
        shiny::insertUI(
          selector = ".gadget-content",
          where = "afterBegin",
          ui = shiny::div(
            style = "height: 400px; overflow-y: scroll; border: 1px solid #ccc; padding: 10px; margin-bottom: 10px;",
            id = "chatHistory",
            shiny::HTML(chat_html)
          )
        )
      }
    }
    
    shiny::observeEvent(input$sendBtn, send_query())
    
    shiny::observeEvent(input$queryInput, {
      if (!is.null(input$queryInput) && input$queryInput != "" && 
          length(grep("\n$", input$queryInput)) > 0) {
        send_query()
      }
    })
    
    shiny::observeEvent(input$done, {
      shiny::stopApp()
    })
  }
  
  shiny::runGadget(ui, server, viewer = shiny::browserViewer())
}

.format_chat_history <- function(history) {
  html_parts <- character(0)
  
  for (msg in history) {
    if (msg$role == "user") {
      html_parts <- c(html_parts, paste0(
        "<div style='margin-bottom: 10px;'><strong>You:</strong> ",
        htmltools::htmlEscape(msg$content), "</div>"
      ))
    } else {
      # Convert markdown-like formatting for assistant responses
      content <- gsub("```r\n([^`]+)\n```", "<pre><code class='language-r'>\\1</code></pre>", msg$content)
      content <- gsub("\\*\\*([^*]+)\\*\\*", "<strong>\\1</strong>", content)
      content <- gsub("\\*([^*]+)\\*", "<em>\\1</em>", content)
      
      html_parts <- c(html_parts, paste0(
        "<div style='margin-bottom: 10px; padding: 10px; background-color: #f8f9fa; border-left: 3px solid #007bff;'>",
        "<strong>ChatR:</strong><br>", content, "</div>"
      ))
    }
  }
  
  paste(html_parts, collapse = "\n")
}

# Auto-start ChatR backend
.auto_start_chatr_backend <- function() {
  tryCatch({
    # Use the same logic as chatr_serve() for consistency
    chatr_paths <- c(
      # Your existing paths (preserved for your local setup)
      "/Users/lihanxia/Documents/chatR-GSOC/venv/bin/chatr",
      paste0(Sys.getenv("HOME"), "/Documents/chatR-GSOC/venv/bin/chatr"),
      paste0(getwd(), "/venv/bin/chatr"),
      Sys.which("chatr"),
      # Additional paths for GitHub users
      paste0(Sys.getenv("HOME"), "/.local/bin/chatr"),  # pip --user install
      "/usr/local/bin/chatr",  # System-wide pip install
      paste0(Sys.getenv("HOME"), "/anaconda3/bin/chatr"),  # Anaconda users
      paste0(Sys.getenv("HOME"), "/miniconda3/bin/chatr"),  # Miniconda users
      paste0(Sys.getenv("HOME"), "/opt/anaconda3/bin/chatr"),  # Mac Anaconda
      paste0(Sys.getenv("CONDA_PREFIX"), "/bin/chatr"),  # Active conda environment
      paste0(Sys.getenv("VIRTUAL_ENV"), "/bin/chatr"),  # Active virtual environment
      # Common GitHub clone locations
      paste0(Sys.getenv("HOME"), "/chatR-GSOC/venv/bin/chatr"),
      paste0(Sys.getenv("HOME"), "/projects/chatR-GSOC/venv/bin/chatr"),
      paste0(Sys.getenv("HOME"), "/dev/chatR-GSOC/venv/bin/chatr")
    )
    
    chatr_cmd <- ""
    for (path in chatr_paths) {
      if (path != "" && file.exists(path)) {
        chatr_cmd <- paste(path, "serve --port 8001")
        break
      }
    }
    
    # Try Python approach if direct command not found
    if (chatr_cmd == "") {
      python_paths <- c(
        # Your existing paths (preserved)
        "/Users/lihanxia/Documents/chatR-GSOC/venv/bin/python",
        paste0(Sys.getenv("HOME"), "/Documents/chatR-GSOC/venv/bin/python"),
        # System Python paths for GitHub users
        "python3",  # Most common
        "python",
        paste0(Sys.getenv("VIRTUAL_ENV"), "/bin/python"),  # Active venv
        paste0(Sys.getenv("CONDA_PREFIX"), "/bin/python"),  # Active conda
        paste0(Sys.getenv("HOME"), "/anaconda3/bin/python"),  # Anaconda
        paste0(Sys.getenv("HOME"), "/miniconda3/bin/python"),  # Miniconda
        # Common GitHub clone locations
        paste0(Sys.getenv("HOME"), "/chatR-GSOC/venv/bin/python"),
        paste0(Sys.getenv("HOME"), "/projects/chatR-GSOC/venv/bin/python")
      )
      
      for (python_path in python_paths) {
        if (python_path != "" && (file.exists(python_path) || Sys.which(python_path) != "")) {
          chatr_cmd <- paste(python_path, "-m chatr.cli.main serve --port 8001")
          break
        }
      }
    }
    
    if (chatr_cmd == "") {
      message("ChatR installation not found. Use chatr_serve() to start manually.")
      return(FALSE)
    }
    
    message(paste("Found ChatR at:", strsplit(chatr_cmd, " ")[[1]][1]))
    
    # Start ChatR backend in background (simple approach)
    if (.Platform$OS.type == "unix") {
      system(paste(chatr_cmd, "> /tmp/chatr.log 2>&1"), wait = FALSE)
    } else {
      system(paste("start /b", chatr_cmd), wait = FALSE)
    }
    
    message("ChatR backend starting... (check /tmp/chatr.log for details)")
    return(TRUE)
    
  }, error = function(e) {
    message("Error starting ChatR backend: ", e$message)
    message("Try running chatr_serve() manually")
    return(FALSE)
  })
}





























