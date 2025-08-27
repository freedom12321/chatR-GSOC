\name{chatr_list_data}
\alias{chatr_list_data}
\title{List Available Data Objects}
\usage{
chatr_list_data(host = "http://localhost:8000")
}
\arguments{
\item{host}{Character. ChatR backend host URL}
}
\value{
Invisible. Prints list of analyzable data objects to console.
}
\description{
Shows all data objects in your R environment that ChatR can analyze,
including data.frames, matrices, and vectors with their characteristics.
}
\details{
This function scans your R global environment and identifies data objects
suitable for analysis. For each object, it shows:
\itemize{
  \item Object name and type (data.frame, matrix, vector)
  \item Dimensions (rows × columns for data.frames/matrices)
  \item Column information for data.frames
  \item Suggested analysis approaches
}
}
\examples{
\dontrun{
# See what data is available for analysis
chatr_list_data()

# Load some data first
data(mtcars)
data(iris)
chatr_list_data()
}
}
\seealso{
\code{\link{chatr_analyze}} to analyze specific datasets,
\code{\link{chatr_data_summary}} for dataset details
}