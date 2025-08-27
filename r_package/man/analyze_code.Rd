\name{analyze_code}
\alias{analyze_code}
\title{R Code Analysis and Improvement}
\usage{
analyze_code(code, host = "http://localhost:8000")
}
\arguments{
\item{code}{Character. R code to analyze}
\item{host}{Character. ChatR backend host URL}
}
\value{
Invisible. Prints code analysis and suggestions to console.
}
\description{
Analyzes R code and provides suggestions for improvements including
performance optimization, style, and best practices.
}
\details{
\code{analyze_code} examines your R code and provides feedback on:
\itemize{
  \item Performance optimizations (vectorization opportunities)
  \item Code style and readability improvements
  \item Best practice recommendations
  \item Potential bugs or issues
  \item Alternative approaches
  \item Package suggestions for better solutions
}

Particularly useful for:
\itemize{
  \item Converting loops to vectorized operations
  \item Improving code readability
  \item Finding more efficient solutions
  \item Learning R best practices
}
}
\examples{
\dontrun{
# Analyze inefficient loop code
bad_code <- "
for (i in 1:nrow(data)) {
  result[i] <- data$x[i] * 2
}
"
analyze_code(bad_code)

# Analyze data manipulation code
data_code <- "
subset(data, x > 5 & y < 10)
"
analyze_code(data_code)

# Analyze plotting code
plot_code <- "
plot(data$x, data$y)
"
analyze_code(plot_code)
}
}
\seealso{
\code{\link{chatr}} for general programming help,
\code{\link{help_explain}} for function explanations
}