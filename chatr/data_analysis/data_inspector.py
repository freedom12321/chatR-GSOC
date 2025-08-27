"""Smart data inspection and analysis planning for ChatR."""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

from ..r_integration.executor import SecureRExecutor

logger = logging.getLogger(__name__)


class DataInspector:
    """Inspects R data objects and provides analysis recommendations."""
    
    def __init__(self, r_executor: SecureRExecutor):
        self.r_executor = r_executor
    
    def get_environment_data(self) -> Dict[str, Any]:
        """Get all data objects from the current R environment."""
        
        r_code = '''
# Load required library
library(jsonlite)

# Get all objects in the global environment
objects_list <- ls()

# Filter for meaningful data objects (exclude temp variables and functions)
data_objects <- list()

for (obj_name in objects_list) {
    obj <- get(obj_name)
    
    # Check if it's a meaningful data object (focus on data.frames primarily)
    if (is.data.frame(obj) || (is.matrix(obj) && nrow(obj) > 1 && ncol(obj) > 1)) {
        
        tryCatch({
            obj_info <- list(
                name = obj_name,
                class = class(obj)[1],
                dimensions = if(is.data.frame(obj) || is.matrix(obj)) dim(obj) else length(obj),
                summary = "Data object detected"
            )
            
            # Add more details for data.frames
            if (is.data.frame(obj)) {
                obj_info$rows <- nrow(obj)
                obj_info$cols <- ncol(obj)
                obj_info$column_names <- colnames(obj)
                # Convert column types to character to avoid JSON issues
                obj_info$column_types <- as.character(sapply(obj, function(x) class(x)[1]))
            }
            
            data_objects[[obj_name]] <- obj_info
        }, error = function(e) {
            # Skip objects that cause errors
        })
    }
}

# Convert to JSON with proper formatting
cat("JSON_START")
cat(toJSON(data_objects, auto_unbox = TRUE, pretty = FALSE))
cat("JSON_END")
'''
        
        try:
            result = self.r_executor.execute_code(r_code)
            
            if result.success and result.stdout.strip():
                try:
                    # Extract JSON between markers
                    stdout = result.stdout
                    start_marker = "JSON_START"
                    end_marker = "JSON_END"
                    
                    if start_marker in stdout and end_marker in stdout:
                        start_idx = stdout.find(start_marker) + len(start_marker)
                        end_idx = stdout.find(end_marker)
                        json_str = stdout[start_idx:end_idx].strip()
                        
                        if json_str:
                            data_info = json.loads(json_str)
                            return data_info
                        else:
                            logger.warning("No JSON content found between markers")
                            return {}
                    else:
                        logger.warning("JSON markers not found in R output")
                        return {}
                        
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse environment data JSON: {e}")
                    logger.warning(f"Raw output: {result.stdout[:500]}...")
                    return {}
            else:
                logger.warning("Failed to get environment data")
                return {}
                
        except Exception as e:
            logger.error(f"Error getting environment data: {e}")
            return {}
    
    def inspect_dataset(self, dataset_name: str) -> Dict[str, Any]:
        """Perform detailed inspection of a specific dataset."""
        
        r_code = f'''
library(jsonlite)

# Check if dataset exists
if (!exists("{dataset_name}")) {{
    cat("JSON_START")
    cat('{{"error": "Dataset not found"}}')
    cat("JSON_END")
    quit()
}}

data <- get("{dataset_name}")

tryCatch({{
    # Basic information
    info <- list(
        name = "{dataset_name}",
        class = class(data)[1],
        summary = "Dataset inspection"
    )

    if (is.data.frame(data)) {{
        # Data frame analysis
        info$type <- "data.frame"
        info$rows <- nrow(data)
        info$cols <- ncol(data)
        info$column_names <- colnames(data)
        
        # Column types and statistics
        col_info <- list()
        for (col in colnames(data)) {{
            col_data <- data[[col]]
            col_analysis <- list(
                name = col,
                type = class(col_data)[1],
                missing_values = sum(is.na(col_data)),
                missing_percent = round(sum(is.na(col_data)) / length(col_data) * 100, 2)
            )
            
            if (is.numeric(col_data)) {{
                col_analysis$numeric_stats <- list(
                    min = min(col_data, na.rm = TRUE),
                    max = max(col_data, na.rm = TRUE),
                    mean = mean(col_data, na.rm = TRUE),
                    median = median(col_data, na.rm = TRUE),
                    sd = sd(col_data, na.rm = TRUE)
                )
                col_analysis$suggested_role <- "continuous_predictor"
            }} else if (is.factor(col_data) || is.character(col_data)) {{
                unique_values <- length(unique(col_data[!is.na(col_data)]))
                most_freq <- names(sort(table(col_data), decreasing = TRUE))[1]
                col_analysis$categorical_stats <- list(
                    unique_values = unique_values,
                    most_frequent = if(is.null(most_freq)) "None" else as.character(most_freq)
                )
                
                if (unique_values <= 10) {{
                    col_analysis$suggested_role <- "categorical_predictor"
                }} else {{
                    col_analysis$suggested_role <- "identifier_or_text"
                }}
            }} else if (is.logical(col_data)) {{
                col_analysis$logical_stats <- list(
                    true_count = sum(col_data, na.rm = TRUE),
                    false_count = sum(!col_data, na.rm = TRUE)
                )
                col_analysis$suggested_role <- "binary_predictor"
            }}
            
            col_info[[col]] <- col_analysis
        }}
        
        info$columns <- col_info
        
        # Dataset characteristics
        info$characteristics <- list(
            has_missing_values = any(sapply(data, function(x) any(is.na(x)))),
            numeric_columns = sum(sapply(data, is.numeric)),
            categorical_columns = sum(sapply(data, function(x) is.factor(x) || is.character(x))),
            logical_columns = sum(sapply(data, is.logical))
        )
        
    }} else if (is.vector(data)) {{
        # Vector analysis
        info$type <- "vector"
        info$length <- length(data)
        info$data_type <- class(data)[1]
        info$missing_values <- sum(is.na(data))
        
        if (is.numeric(data)) {{
            info$numeric_stats <- list(
                min = min(data, na.rm = TRUE),
                max = max(data, na.rm = TRUE),
                mean = mean(data, na.rm = TRUE),
                median = median(data, na.rm = TRUE),
                sd = sd(data, na.rm = TRUE)
            )
        }}
    }} else if (is.matrix(data)) {{
        # Matrix analysis
        info$type <- "matrix"
        info$rows <- nrow(data)
        info$cols <- ncol(data)
        info$data_type <- class(data)[1]
    }}

    # Convert to JSON
    cat("JSON_START")
    cat(toJSON(info, auto_unbox = TRUE, pretty = FALSE))
    cat("JSON_END")
    
}}, error = function(e) {{
    cat("JSON_START")
    cat('{{"error": "Failed to analyze dataset"}}')
    cat("JSON_END")
}})
'''
        
        try:
            result = self.r_executor.execute_code(r_code)
            
            if result.success and result.stdout.strip():
                try:
                    # Extract JSON between markers
                    stdout = result.stdout
                    start_marker = "JSON_START"
                    end_marker = "JSON_END"
                    
                    if start_marker in stdout and end_marker in stdout:
                        start_idx = stdout.find(start_marker) + len(start_marker)
                        end_idx = stdout.find(end_marker)
                        json_str = stdout[start_idx:end_idx].strip()
                        
                        if json_str:
                            dataset_info = json.loads(json_str)
                            return dataset_info
                        else:
                            logger.warning("No JSON content found between markers")
                            return {"error": "No dataset information found"}
                    else:
                        logger.warning("JSON markers not found in dataset inspection output")
                        return {"error": "Failed to parse dataset information"}
                        
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse dataset inspection JSON: {e}")
                    logger.warning(f"Raw output: {result.stdout[:500]}...")
                    return {"error": "Failed to parse dataset information"}
            else:
                return {"error": "Failed to inspect dataset"}
                
        except Exception as e:
            logger.error(f"Error inspecting dataset: {e}")
            return {"error": str(e)}


class AnalysisPlanGenerator:
    """Generates intelligent analysis plans based on data characteristics."""
    
    def __init__(self, llm_client):
        self.llm_client = llm_client
        # We'll need access to the R executor
        self.r_executor = None
    
    def generate_analysis_plan(self, dataset_info: Dict[str, Any], user_goal: str = "") -> str:
        """Generate a comprehensive analysis plan based on dataset characteristics."""
        
        # Extract key characteristics
        dataset_summary = self._summarize_dataset(dataset_info)
        dataset_name = dataset_info.get('name', 'unknown')
        
        # Execute initial exploration R code to get actual results
        initial_results = self._execute_initial_exploration(dataset_name)
        
        # Create analysis planning prompt with actual results
        planning_prompt = f"""
You are an expert data analyst helping a user analyze their dataset. Based on the dataset characteristics and initial exploration results, provide a comprehensive, step-by-step analysis plan.

Dataset Information:
{dataset_summary}

Initial Exploration Results:
{initial_results}

User Goal: {user_goal if user_goal else "General exploratory data analysis"}

Please provide a complete analysis plan including:

1. **Data Exploration Steps**
   - Reference the actual data shown above
   - Additional summary statistics to explore
   - Missing data analysis (if needed)

2. **Visualization Recommendations**
   - Appropriate plots for each variable type
   - Relationship exploration plots based on the actual data patterns

3. **Statistical Analysis Suggestions**
   - Based on the data types and structure shown
   - Appropriate statistical tests or models for this specific dataset

4. **Step-by-Step R Code**
   - Complete, executable R code for each step
   - Clear explanations for beginners
   - Best practices and tips

5. **Potential Issues to Watch For**
   - Data quality concerns based on the actual data
   - Statistical assumptions to check
   - Common pitfalls to avoid

Format your response as a comprehensive tutorial that builds on the initial exploration results shown above.
"""
        
        try:
            analysis_plan = self.llm_client.generate_response(
                planning_prompt,
                execute_code=False  # Don't execute code in the planning phase
            )
            return analysis_plan
        except Exception as e:
            logger.error(f"Error generating analysis plan: {e}")
            return f"Sorry, I encountered an error generating the analysis plan: {e}"
    
    def _summarize_dataset(self, dataset_info: Dict[str, Any]) -> str:
        """Create a human-readable summary of the dataset."""
        
        if "error" in dataset_info:
            return f"Error: {dataset_info['error']}"
        
        summary_parts = []
        
        # Basic info
        summary_parts.append(f"Dataset: {dataset_info.get('name', 'Unknown')}")
        summary_parts.append(f"Type: {dataset_info.get('type', 'Unknown')}")
        
        if dataset_info.get('type') == 'data.frame':
            summary_parts.append(f"Dimensions: {dataset_info.get('rows', 0)} rows × {dataset_info.get('cols', 0)} columns")
            
            # Column information
            columns = dataset_info.get('columns', {})
            if columns:
                summary_parts.append(f"\\nColumn Details:")
                for col_name, col_info in columns.items():
                    col_type = col_info.get('type', 'unknown')
                    missing_pct = col_info.get('missing_percent', 0)
                    role = col_info.get('suggested_role', 'unknown')
                    
                    summary_parts.append(f"  - {col_name}: {col_type} ({role}, {missing_pct}% missing)")
                    
                    # Add statistical summary for numeric columns
                    if 'numeric_stats' in col_info:
                        stats = col_info['numeric_stats']
                        summary_parts.append(f"    Range: {stats.get('min', 'N/A')} to {stats.get('max', 'N/A')}, Mean: {stats.get('mean', 'N/A'):.2f}")
                    
                    # Add categorical summary
                    elif 'categorical_stats' in col_info:
                        cat_stats = col_info['categorical_stats']
                        summary_parts.append(f"    {cat_stats.get('unique_values', 'N/A')} unique values, Most frequent: {cat_stats.get('most_frequent', 'N/A')}")
            
            # Dataset characteristics
            chars = dataset_info.get('characteristics', {})
            summary_parts.append(f"\\nDataset Characteristics:")
            summary_parts.append(f"  - Numeric columns: {chars.get('numeric_columns', 0)}")
            summary_parts.append(f"  - Categorical columns: {chars.get('categorical_columns', 0)}")
            summary_parts.append(f"  - Has missing values: {chars.get('has_missing_values', False)}")
        
        elif dataset_info.get('type') == 'vector':
            summary_parts.append(f"Length: {dataset_info.get('length', 0)}")
            summary_parts.append(f"Data type: {dataset_info.get('data_type', 'unknown')}")
            summary_parts.append(f"Missing values: {dataset_info.get('missing_values', 0)}")
        
        return "\\n".join(summary_parts)
    
    def suggest_analysis_type(self, dataset_info: Dict[str, Any]) -> List[str]:
        """Suggest appropriate analysis types based on dataset characteristics."""
        
        suggestions = []
        
        if dataset_info.get('type') == 'data.frame':
            chars = dataset_info.get('characteristics', {})
            cols = dataset_info.get('columns', {})
            
            # Basic suggestions
            suggestions.append("Exploratory Data Analysis (EDA)")
            suggestions.append("Summary Statistics")
            suggestions.append("Data Visualization")
            
            # Advanced suggestions based on data structure
            if chars.get('numeric_columns', 0) >= 2:
                suggestions.append("Correlation Analysis")
                suggestions.append("Linear Regression")
            
            if chars.get('categorical_columns', 0) >= 1 and chars.get('numeric_columns', 0) >= 1:
                suggestions.append("Group Comparisons (t-tests, ANOVA)")
                suggestions.append("Categorical Data Analysis")
            
            if chars.get('numeric_columns', 0) >= 1:
                suggestions.append("Distribution Analysis")
                suggestions.append("Outlier Detection")
            
            # Time series analysis if date/time columns detected
            for col_name, col_info in cols.items():
                if 'date' in col_name.lower() or 'time' in col_name.lower():
                    suggestions.append("Time Series Analysis")
                    break
            
            # Machine learning suggestions
            if len(cols) >= 3:  # Multiple predictors available
                suggestions.append("Predictive Modeling")
                suggestions.append("Feature Selection")
        
        return suggestions
    
    def _execute_initial_exploration(self, dataset_name: str) -> str:
        """Execute basic R commands to show actual data exploration results."""
        
        if not self.r_executor:
            return "R executor not available for code execution."
        
        r_code = f'''
# Load the dataset
data({dataset_name})
dataset <- get("{dataset_name}")

cat("=== DATASET PREVIEW ===\\n")
cat("First 10 rows:\\n")
print(head(dataset, 10))

cat("\\n\\n=== DATASET STRUCTURE ===\\n")
str(dataset)

cat("\\n\\n=== SUMMARY STATISTICS ===\\n")
print(summary(dataset))

cat("\\n\\n=== DATASET DIMENSIONS ===\\n")
cat("Rows:", nrow(dataset), "\\n")
cat("Columns:", ncol(dataset), "\\n")
cat("Column names:", paste(colnames(dataset), collapse = ", "), "\\n")

# Show correlation matrix for numeric columns only
numeric_cols <- sapply(dataset, is.numeric)
if (sum(numeric_cols) > 1) {{
    cat("\\n\\n=== CORRELATION MATRIX (Numeric columns only) ===\\n")
    print(round(cor(dataset[, numeric_cols]), 3))
}}

# Show unique values for categorical/factor columns
factor_cols <- sapply(dataset, function(x) is.factor(x) || is.character(x))
if (sum(factor_cols) > 0) {{
    cat("\\n\\n=== CATEGORICAL VARIABLE SUMMARY ===\\n")
    for (col in names(dataset)[factor_cols]) {{
        cat("\\n", col, ":\\n")
        print(table(dataset[[col]]))
    }}
}}
'''
        
        try:
            result = self.r_executor.execute_code(r_code)
            if result.success:
                return f"```\\n{result.stdout}\\n```"
            else:
                return f"Error executing R code: {result.stderr}"
        except Exception as e:
            logger.error(f"Error in _execute_initial_exploration: {e}")
            return f"Error executing initial exploration: {e}"


class SmartDataAnalysisAssistant:
    """Main interface for smart data analysis assistance."""
    
    def __init__(self, r_executor, llm_client):
        self.r_executor = r_executor
        self.data_inspector = DataInspector(r_executor)
        self.plan_generator = AnalysisPlanGenerator(llm_client)
        # Pass the R executor to the plan generator so it can execute code
        self.plan_generator.r_executor = r_executor
    
    def analyze_my_data(self, dataset_name: str = None, user_goal: str = "") -> str:
        """Main function to analyze user's data and provide guidance."""
        
        try:
            if dataset_name:
                # Analyze specific dataset
                dataset_info = self.data_inspector.inspect_dataset(dataset_name)
                
                if "error" in dataset_info:
                    return f"I couldn't access the dataset '{dataset_name}'. Error: {dataset_info['error']}\\n\\nTip: Make sure the dataset is loaded in your R environment. You can check with `ls()` to see available objects."
                
                # Generate analysis plan
                analysis_plan = self.plan_generator.generate_analysis_plan(dataset_info, user_goal)
                
                # Add dataset summary at the beginning
                dataset_summary = self.plan_generator._summarize_dataset(dataset_info)
                analysis_suggestions = self.plan_generator.suggest_analysis_type(dataset_info)
                
                response = f"""# 📊 Smart Analysis Plan for '{dataset_name}'

## Dataset Overview
{dataset_summary}

## Recommended Analysis Types
{', '.join(analysis_suggestions)}

## Complete Analysis Plan
{analysis_plan}

---
**💡 Tip:** You can run each code section step by step in your R console or RStudio. I'll be here to help if you have questions about any step!
"""
                return response
            
            else:
                # List available datasets and provide general guidance
                env_data = self.data_inspector.get_environment_data()
                
                if not env_data:
                    return """# 🔍 No Data Objects Found

I don't see any data objects in your R environment yet. Here's how to get started:

## Option 1: Load Built-in Datasets
```r
# Load a built-in dataset
data(mtcars)    # Car data
data(iris)      # Flower measurements  
data(diamonds)  # Diamond characteristics (if ggplot2 installed)
```

## Option 2: Import Your Own Data
```r
# Read CSV file
my_data <- read.csv("path/to/your/file.csv")

# Read Excel file (requires readxl package)
library(readxl)
my_data <- read_excel("path/to/your/file.xlsx")
```

## Option 3: Create Sample Data
```r
# Create sample data for practice
sample_data <- data.frame(
  age = c(25, 30, 35, 40, 45),
  income = c(30000, 45000, 55000, 65000, 75000),
  education = c("Bachelor", "Master", "PhD", "Bachelor", "Master")
)
```

After loading data, try: `chatr_analyze("your_dataset_name")`
"""
                
                # List available datasets
                dataset_list = []
                for obj_name, obj_info in env_data.items():
                    obj_type = obj_info.get('class', 'unknown')
                    if obj_info.get('dimensions'):
                        if isinstance(obj_info['dimensions'], list):
                            dims = f"{obj_info['dimensions'][0]} × {obj_info['dimensions'][1]}"
                        else:
                            dims = f"length {obj_info['dimensions']}"
                    else:
                        dims = "unknown size"
                    
                    dataset_list.append(f"  - **{obj_name}** ({obj_type}, {dims})")
                
                response = f"""# 📊 Available Data Objects

I found {len(env_data)} data object(s) in your R environment:

{chr(10).join(dataset_list)}

## 🎯 Get Analysis Plan for Specific Dataset
Choose a dataset and run:
```r
chatr_analyze("dataset_name")
# or specify your analysis goal:
chatr_analyze("dataset_name", "I want to predict sales")
```

## 🚀 Quick Start Examples
```r
# For general exploration:
chatr_analyze("mtcars")

# For specific analysis:
chatr_analyze("iris", "classify flower species")
chatr_analyze("sales_data", "find factors affecting revenue")
```

**💡 Tip:** I'll create a complete, step-by-step analysis plan tailored to your data structure and goals!
"""
                return response
                
        except Exception as e:
            logger.error(f"Error in analyze_my_data: {e}")
            return f"Sorry, I encountered an error while analyzing your data: {e}"
    
    def quick_data_summary(self, dataset_name: str) -> str:
        """Provide a quick summary of a dataset."""
        
        dataset_info = self.data_inspector.inspect_dataset(dataset_name)
        
        if "error" in dataset_info:
            return f"Error: {dataset_info['error']}"
        
        summary = self.plan_generator._summarize_dataset(dataset_info)
        suggestions = self.plan_generator.suggest_analysis_type(dataset_info)
        
        return f"""# 📋 Quick Summary: {dataset_name}

{summary}

## 🎯 Suggested Analyses
{', '.join(suggestions)}

Run `chatr_analyze("{dataset_name}")` for a complete analysis plan!
"""