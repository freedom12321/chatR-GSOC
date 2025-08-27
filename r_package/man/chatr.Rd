\name{chatr}
\alias{chatr}
\title{ChatR: Intelligent R Assistant}
\usage{
chatr(query = NULL, host = "http://localhost:8000", launch_ui = NULL)
}
\arguments{
\item{query}{Character. Your question or request to ChatR}
\item{host}{Character. ChatR backend host URL (default: "http://localhost:8000")}
\item{launch_ui}{Logical. Whether to launch Shiny UI (default: TRUE in RStudio)}
}
\value{
Invisible character string containing ChatR's response
}
\description{
Main ChatR function providing conversational AI assistance for R programming.
Uses Retrieval-Augmented Generation (RAG) to search R documentation and 
provide context-aware help with R programming tasks.
}
\details{
ChatR combines local LLM capabilities with comprehensive R documentation
to provide intelligent assistance. It can:
\itemize{
  \item Answer R programming questions
  \item Explain functions and concepts
  \item Provide code examples
  \item Suggest best practices
  \item Help with statistical analysis
}

The function requires a running ChatR backend (start with \code{chatr serve} 
in terminal, or it will attempt to auto-start).
}
\examples{
\dontrun{
# Ask a programming question
chatr("How do I create a scatter plot with ggplot2?")

# Get help with statistical concepts
chatr("Explain the assumptions of linear regression")

# Debug code issues
chatr("I get 'object not found' error with dplyr")

# Learn new techniques
chatr("How to perform principal component analysis step by step")

# Launch interactive UI (in RStudio)
chatr()
}
}
\seealso{
\code{\link{chatr_analyze}} for data analysis planning,
\code{\link{help_explain}} for function-specific help
}