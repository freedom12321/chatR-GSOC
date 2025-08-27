\name{chatr_analyze}
\alias{chatr_analyze}
\title{Smart Data Analysis Planning}
\usage{
chatr_analyze(dataset_name = NULL, goal = "", host = "http://localhost:8000")
}
\arguments{
\item{dataset_name}{Character. Name of dataset in your R environment to analyze}
\item{goal}{Character. Optional analysis goal or research question}
\item{host}{Character. ChatR backend host URL}
}
\value{
Invisible. Prints comprehensive analysis plan to console.
}
\description{
AI-powered data analysis assistant that inspects your dataset and creates
comprehensive, step-by-step analysis plans tailored to your data structure
and research goals.
}
\details{
\code{chatr_analyze} performs intelligent data inspection and generates:
\itemize{
  \item Data structure overview (types, dimensions, missing values)
  \item Variable role identification (predictors, outcomes, identifiers)
  \item Suggested statistical analyses based on data characteristics
  \item Step-by-step R code for each analysis
  \item Visualization recommendations
  \item Best practices and potential issues to watch for
}

The function automatically detects:
\itemize{
  \item Numeric variables (continuous/discrete)
  \item Categorical variables (factors/characters)
  \item Missing data patterns
  \item Appropriate statistical tests
  \item Modeling approaches
}
}
\examples{
\dontrun{
# Analyze built-in datasets
data(mtcars)
chatr_analyze("mtcars")

data(iris)
chatr_analyze("iris")

# With specific analysis goals
chatr_analyze("mtcars", "predict fuel efficiency")
chatr_analyze("sales_data", "identify factors affecting revenue")

# Your own data
my_data <- read.csv("data.csv")
chatr_analyze("my_data")

# General exploratory analysis
chatr_analyze("survey_data", "exploratory data analysis")
}
}
\seealso{
\code{\link{chatr_list_data}} to see available datasets,
\code{\link{chatr_data_summary}} for quick dataset overview,
\code{\link{chatr_assistant}} for interactive analysis
}