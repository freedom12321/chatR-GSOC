\name{help_explain}
\alias{help_explain}
\title{Intelligent R Function Help}
\usage{
help_explain(func, package = NULL, host = "http://localhost:8000")
}
\arguments{
\item{func}{Character. Name of R function to explain}
\item{package}{Character. Package name (optional)}
\item{host}{Character. ChatR backend host URL}
}
\value{
Invisible character string containing function explanation
}
\description{
Get intelligent, context-aware explanations of R functions with examples
and practical usage guidance.
}
\details{
Unlike standard R help, \code{help_explain} provides:
\itemize{
  \item Plain-English explanations of what functions do
  \item Practical examples with real data
  \item Common use cases and workflows
  \item Comparison with related functions
  \item Tips and best practices
  \item Common pitfalls to avoid
}

The explanations are generated using ChatR's RAG system, combining
official documentation with community knowledge and best practices.
}
\examples{
\dontrun{
# Get help with base R functions
help_explain("lm")
help_explain("apply")
help_explain("merge")

# Get help with package functions
help_explain("ggplot", "ggplot2")
help_explain("filter", "dplyr")
help_explain("read_csv", "readr")

# Statistical functions
help_explain("t.test")
help_explain("cor.test")
help_explain("aov")
}
}
\seealso{
\code{\link{chatr}} for general R questions,
\code{\link{analyze_code}} for code analysis
}