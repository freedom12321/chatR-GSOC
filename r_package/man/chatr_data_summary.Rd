\name{chatr_data_summary}
\alias{chatr_data_summary}
\title{Quick Data Summary}
\usage{
chatr_data_summary(dataset_name, host = "http://localhost:8000")
}
\arguments{
\item{dataset_name}{Character. Name of dataset in your R environment}
\item{host}{Character. ChatR backend host URL}
}
\value{
Invisible. Prints quick dataset summary to console.
}
\description{
Provides a quick overview of dataset characteristics including data types,
dimensions, missing values, and suggested analysis approaches.
}
\details{
\code{chatr_data_summary} gives you a fast snapshot of your dataset:
\itemize{
  \item Basic structure (dimensions, types)
  \item Missing data patterns
  \item Column characteristics
  \item Suggested analysis types
}

This is faster than \code{chatr_analyze} and perfect for:
\itemize{
  \item Quick data exploration
  \item Understanding unfamiliar datasets
  \item Deciding on analysis approaches
  \item Data quality assessment
}
}
\examples{
\dontrun{
# Quick summaries of built-in datasets
data(mtcars)
chatr_data_summary("mtcars")

data(iris)
chatr_data_summary("iris")

# Your own data
my_data <- read.csv("data.csv")
chatr_data_summary("my_data")
}
}
\seealso{
\code{\link{chatr_analyze}} for complete analysis planning,
\code{\link{chatr_list_data}} for available datasets
}