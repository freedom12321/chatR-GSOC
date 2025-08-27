\name{chatr_serve}
\alias{chatr_serve}
\title{Start ChatR Backend Server}
\usage{
chatr_serve(port = 8000, host = "localhost")
}
\arguments{
\item{port}{Integer. Port to run the server on (default: 8000)}
\item{host}{Character. Host to bind to (default: "localhost")}
}
\value{
Invisible NULL. Starts server in background.
}
\description{
Starts the ChatR backend server that provides AI and RAG capabilities
to the R package functions.
}
\details{
\code{chatr_serve} launches the Python ChatR backend server that handles:
\itemize{
  \item Local LLM processing via Ollama
  \item RAG (Retrieval-Augmented Generation) system
  \item External data source integration
  \item R code execution and analysis
}

The server runs in the background and provides API endpoints for all
ChatR R functions. This function attempts to start the server automatically
by calling the ChatR Python CLI.

\strong{Prerequisites:}
\itemize{
  \item ChatR Python package installed
  \item Ollama installed and running
  \item Virtual environment activated (if used)
}
}
\examples{
\dontrun{
# Start server on default port
chatr_serve()

# Start on different port
chatr_serve(port = 8001)

# Check if server is running
# In browser: http://localhost:8000/health

# Stop server: Ctrl+C in terminal where it's running
}
}
\note{
If auto-start fails, manually start the server in terminal:
\code{cd /path/to/chatR-GSOC && source venv/bin/activate && chatr serve}
}
\seealso{
\code{\link{chatr}} and other package functions require a running backend
}