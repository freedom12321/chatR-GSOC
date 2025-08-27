\name{chatr_assistant}
\alias{chatr_assistant}
\title{Interactive Data Analysis Assistant}
\usage{
chatr_assistant(host = "http://localhost:8000")
}
\arguments{
\item{host}{Character. ChatR backend host URL}
}
\value{
Invisible. Launches interactive analysis workflow.
}
\description{
Interactive assistant that guides you through data analysis by showing
available datasets, asking about your goals, and providing customized
analysis plans.
}
\details{
\code{chatr_assistant} provides a guided, interactive experience:
\enumerate{
  \item Scans your R environment for data objects
  \item Displays available datasets with their characteristics
  \item Prompts you to select a dataset for analysis
  \item Asks about your analysis goals (optional)
  \item Generates a customized analysis plan
  \item Provides step-by-step guidance
}

Perfect for:
\itemize{
  \item Beginners learning data analysis
  \item Exploring new datasets
  \item Getting unstuck on analysis approaches
  \item Learning best practices interactively
}
}
\examples{
\dontrun{
# Load some data and start interactive analysis
data(mtcars)
data(iris)
chatr_assistant()

# The assistant will:
# 1. Show available datasets (mtcars, iris)
# 2. Let you choose which to analyze
# 3. Ask about your analysis goals
# 4. Create a customized analysis plan
}
}
\seealso{
\code{\link{chatr_analyze}} for direct dataset analysis,
\code{\link{chatr_list_data}} to see available data,
\code{\link{chatr_analysis_tips}} for analysis guidance
}