\name{chatr_repl}
\alias{chatr_repl}
\alias{chatr_chat}
\title{Simple Chat/REPL Interface for ChatR}
\usage{
chatr_repl(host = "http://localhost:8001", welcome_message = NULL, max_history = 10)

chatr_chat()
}
\arguments{
\item{host}{ChatR server host (default: "http://localhost:8001")}

\item{welcome_message}{Custom welcome message}

\item{max_history}{Maximum number of conversation turns to keep}
}
\description{
Provides an interactive chat interface within R console.
Users can type queries and get responses while maintaining context.

\code{chatr_chat()} is a convenience function equivalent to \code{chatr_repl()}.
}
\details{
The REPL (Read-Eval-Print Loop) interface provides an interactive chat experience
where you can ask R questions and get immediate responses. The interface maintains
conversation context and provides several built-in commands:

\strong{Available Commands:}
\itemize{
  \item \code{/help} - Show help message
  \item \code{/clear} - Clear conversation history
  \item \code{/history} - Show conversation history
  \item \code{/status} - Check server status
  \item \code{/quit}, \code{/exit}, \code{/q} - Exit REPL
}

\strong{Features:}
\itemize{
  \item Interactive question-answer sessions
  \item Colorful terminal output with syntax highlighting
  \item Conversation history maintenance
  \item Multiline input support (end lines with \\)
  \item Context preservation across questions
  \item Server connection monitoring
}

The function requires a running ChatR server. Start the server with \code{chatr serve}
or ensure it's running at the specified host before using the REPL.
}
\examples{
\dontrun{
# Start ChatR server first
chatr_serve()

# Start interactive chat session
chatr_repl()

# Quick start (same as above)
chatr_chat()

# Start with custom host
chatr_repl(host = "http://localhost:8002")

# Example session:
# > How do I create a data frame?
# ChatR: Use data.frame(): df <- data.frame(x = 1:3, y = c("a", "b", "c"))
# > What about reading CSV files?
# ChatR: Use read.csv(): data <- read.csv("file.csv")
# > /history
# [Shows conversation history]
# > /quit
}
}
\seealso{
\code{\link{chatr}}, \code{\link{chatr_serve}}, \code{\link{help_explain}}
}
\author{
ChatR Team
}
\keyword{interface}
\keyword{interactive}