\name{chatr-package}
\alias{chatr-package}
\docType{package}
\title{ChatR: An Intelligent, Local Assistant for R Programmers}
\description{
ChatR is a lightweight, open, and reliable AI assistant built specifically 
for R users. It runs locally on your machine without needing a powerful GPU 
or proprietary API key, providing context-aware help, code suggestions, 
and intelligent data analysis planning.
}
\details{
\tabular{ll}{
Package: \tab chatr\cr
Type: \tab Package\cr
Version: \tab 0.1.0\cr
License: \tab MIT\cr
}

ChatR provides several key capabilities:
\itemize{
  \item \strong{Conversational AI:} Ask questions in natural language about R programming
  \item \strong{Smart Data Analysis:} Automatic dataset inspection and analysis planning
  \item \strong{Context-Aware Help:} Function explanations with practical examples
  \item \strong{Code Analysis:} Suggestions for improving R code performance and style
  \item \strong{Interactive Assistance:} Guided workflows for data analysis
}

\strong{Core Technologies:}
\itemize{
  \item \strong{Local LLM:} Uses Ollama for offline AI capabilities
  \item \strong{RAG System:} Retrieval-Augmented Generation with R documentation
  \item \strong{Hybrid Search:} Combines BM25 sparse retrieval with dense embeddings
  \item \strong{Live Data Sources:} R-universe packages, community feeds, academic papers
}

\strong{Main Functions:}
\itemize{
  \item \code{\link{chatr}}: Main conversational AI interface
  \item \code{\link{chatr_analyze}}: Smart data analysis planning
  \item \code{\link{chatr_list_data}}: Show available datasets
  \item \code{\link{help_explain}}: Intelligent function help
  \item \code{\link{analyze_code}}: Code analysis and improvement
  \item \code{\link{chatr_assistant}}: Interactive analysis assistant
}

\strong{Getting Started:}
\enumerate{
  \item Start ChatR backend: \code{chatr serve} (in terminal)
  \item Load package: \code{library(chatr)}
  \item Try: \code{chatr("How do I create a scatter plot?")}
  \item Analyze data: \code{data(mtcars); chatr_analyze("mtcars")}
}
}
\examples{
\dontrun{
# Basic usage
library(chatr)

# Ask R programming questions
chatr("How do I read a CSV file in R?")
chatr("What's the difference between apply and lapply?")

# Analyze your data
data(mtcars)
chatr_analyze("mtcars")
chatr_analyze("mtcars", "predict fuel efficiency")

# Get function help
help_explain("lm")
help_explain("ggplot", "ggplot2")

# Analyze and improve code
code <- "for(i in 1:100) result[i] <- i^2"
analyze_code(code)

# Interactive analysis
chatr_assistant()
}
}
\author{
ChatR Team
}
\keyword{package}