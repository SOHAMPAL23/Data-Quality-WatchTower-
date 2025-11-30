import re
import pandas as pd
from typing import Tuple, Any, List, Dict


class DSLParser:
    """
    A simple DSL parser for data quality rules.
    Supports: NOT_NULL, UNIQUE, IN_RANGE, FOREIGN_KEY, REGEX, LENGTH_RANGE
    """
    
    def __init__(self):
        self.functions = {
            'NOT_NULL': self._parse_not_null,
            'UNIQUE': self._parse_unique,
            'IN_RANGE': self._parse_in_range,
            'FOREIGN_KEY': self._parse_foreign_key,
            'REGEX': self._parse_regex,
            'LENGTH_RANGE': self._parse_length_range,
        }
    
    def parse(self, dsl_expression: str) -> Tuple[str, List[Any]]:
        """
        Parse a DSL expression and return the function name and arguments.
        
        Args:
            dsl_expression (str): The DSL expression to parse
            
        Returns:
            Tuple[str, List[Any]]: Function name and list of arguments
        """
        # Remove whitespace
        dsl_expression = dsl_expression.strip()
        
        # Match function name and arguments
        pattern = r'^([A-Z_]+)\((.*)\)$'
        match = re.match(pattern, dsl_expression)
        
        if not match:
            raise ValueError(f"Invalid DSL expression format: {dsl_expression}")
        
        func_name = match.group(1)
        args_str = match.group(2)
        
        if func_name not in self.functions:
            raise ValueError(f"Unsupported function: {func_name}")
        
        # Parse arguments
        args = self._parse_arguments(args_str)
        
        return func_name, args
    
    def _parse_arguments(self, args_str: str) -> List[Any]:
        """Parse arguments string into a list of arguments."""
        args = []
        current_arg = ""
        in_quotes = False
        quote_char = None
        
        i = 0
        while i < len(args_str):
            char = args_str[i]
            
            if char in ['"', "'"] and (i == 0 or args_str[i-1] != '\\'):
                if not in_quotes:
                    in_quotes = True
                    quote_char = char
                elif char == quote_char:
                    in_quotes = False
                    quote_char = None
                    args.append(current_arg)
                    current_arg = ""
                    # Skip comma after closing quote
                    if i + 1 < len(args_str) and args_str[i+1] == ',':
                        i += 1
                    # Skip whitespace after comma
                    while i + 1 < len(args_str) and args_str[i+1].isspace():
                        i += 1
                else:
                    current_arg += char
            elif char == ',' and not in_quotes:
                if current_arg.strip():
                    args.append(self._convert_arg(current_arg.strip()))
                current_arg = ""
                # Skip whitespace after comma
                while i + 1 < len(args_str) and args_str[i+1].isspace():
                    i += 1
            else:
                current_arg += char
            
            i += 1
        
        # Add last argument
        if current_arg.strip():
            args.append(self._convert_arg(current_arg.strip()))
        
        return args
    
    def _convert_arg(self, arg: str) -> Any:
        """Convert string argument to appropriate type."""
        arg = arg.strip()
        
        # Handle null values
        if arg.lower() == 'null':
            return None
            
        # Handle numeric values
        try:
            if '.' in arg:
                return float(arg)
            else:
                return int(arg)
        except ValueError:
            pass
        
        # Handle quoted strings (remove quotes)
        if (arg.startswith('"') and arg.endswith('"')) or (arg.startswith("'") and arg.endswith("'")):
            return arg[1:-1]
        
        # Return as string
        return arg
    
    def _parse_not_null(self, column: str) -> Dict:
        """Parse NOT_NULL function arguments."""
        return {'column': column}
    
    def _parse_unique(self, column: str) -> Dict:
        """Parse UNIQUE function arguments."""
        return {'column': column}
    
    def _parse_in_range(self, column: str, min_val: Any, max_val: Any) -> Dict:
        """Parse IN_RANGE function arguments."""
        return {'column': column, 'min': min_val, 'max': max_val}
    
    def _parse_foreign_key(self, column: str, ref_table: str, ref_column: str) -> Dict:
        """Parse FOREIGN_KEY function arguments."""
        return {'column': column, 'ref_table': ref_table, 'ref_column': ref_column}
    
    def _parse_regex(self, column: str, pattern: str) -> Dict:
        """Parse REGEX function arguments."""
        return {'column': column, 'pattern': pattern}
    
    def _parse_length_range(self, column: str, min_length: int, max_length: int) -> Dict:
        """Parse LENGTH_RANGE function arguments."""
        return {'column': column, 'min_length': min_length, 'max_length': max_length}


class RuleExecutor:
    """
    Execute rules on pandas DataFrames.
    """
    
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.parser = DSLParser()
    
    def execute_rule(self, dsl_expression: str) -> Dict:
        """
        Execute a rule on the DataFrame.
        
        Args:
            dsl_expression (str): The DSL expression to execute
            
        Returns:
            Dict: Results including passed/failed counts and sample evidence
        """
        try:
            func_name, args = self.parser.parse(dsl_expression)
            
            if func_name == 'NOT_NULL':
                return self._execute_not_null(args[0])
            elif func_name == 'UNIQUE':
                return self._execute_unique(args[0])
            elif func_name == 'IN_RANGE':
                return self._execute_in_range(args[0], args[1], args[2])
            elif func_name == 'FOREIGN_KEY':
                return self._execute_foreign_key(args[0], args[1], args[2])
            elif func_name == 'REGEX':
                return self._execute_regex(args[0], args[1])
            elif func_name == 'LENGTH_RANGE':
                return self._execute_length_range(args[0], args[1], args[2])
            else:
                raise ValueError(f"Unsupported function: {func_name}")
        except Exception as e:
            return {
                'passed': 0,
                'failed': len(self.df),
                'error': str(e),
                'sample_evidence': []
            }
    
    def _execute_not_null(self, column: str) -> Dict:
        """Execute NOT_NULL rule."""
        if column not in self.df.columns:
            return {
                'passed': 0,
                'failed': len(self.df),
                'error': f"Column '{column}' not found",
                'sample_evidence': []
            }
        
        null_mask = self.df[column].isnull()
        failed_count = null_mask.sum()
        passed_count = len(self.df) - failed_count
        
        # Get sample evidence (first 5 null rows)
        sample_evidence = []
        if failed_count > 0:
            sample_evidence = self.df[null_mask].head(5).to_dict('records')
        
        return {
            'passed': passed_count,
            'failed': failed_count,
            'sample_evidence': sample_evidence
        }
    
    def _execute_unique(self, column: str) -> Dict:
        """Execute UNIQUE rule."""
        if column not in self.df.columns:
            return {
                'passed': 0,
                'failed': len(self.df),
                'error': f"Column '{column}' not found",
                'sample_evidence': []
            }
        
        # Count duplicates
        duplicated_mask = self.df[column].duplicated(keep=False)
        failed_count = duplicated_mask.sum()
        passed_count = len(self.df) - failed_count
        
        # Get sample evidence (first 5 duplicate rows)
        sample_evidence = []
        if failed_count > 0:
            sample_evidence = self.df[duplicated_mask].head(5).to_dict('records')
        
        return {
            'passed': passed_count,
            'failed': failed_count,
            'sample_evidence': sample_evidence
        }
    
    def _execute_in_range(self, column: str, min_val: Any, max_val: Any) -> Dict:
        """Execute IN_RANGE rule."""
        if column not in self.df.columns:
            return {
                'passed': 0,
                'failed': len(self.df),
                'error': f"Column '{column}' not found",
                'sample_evidence': []
            }
        
        # Handle None values for min/max
        if min_val is None and max_val is None:
            return {
                'passed': len(self.df),
                'failed': 0,
                'sample_evidence': []
            }
        
        # Create mask for values within range
        range_mask = pd.Series([True] * len(self.df))
        
        if min_val is not None:
            range_mask &= (self.df[column] >= min_val)
        if max_val is not None:
            range_mask &= (self.df[column] <= max_val)
        
        failed_count = (~range_mask).sum()
        passed_count = len(self.df) - failed_count
        
        # Get sample evidence (first 5 out-of-range rows)
        sample_evidence = []
        if failed_count > 0:
            sample_evidence = self.df[~range_mask].head(5).to_dict('records')
        
        return {
            'passed': passed_count,
            'failed': failed_count,
            'sample_evidence': sample_evidence
        }
    
    def _execute_foreign_key(self, column: str, ref_table: str, ref_column: str) -> Dict:
        """Execute FOREIGN_KEY rule."""
        # This is a simplified implementation
        # In a real system, you would check against the actual reference table
        return {
            'passed': len(self.df),
            'failed': 0,
            'sample_evidence': [],
            'message': "FOREIGN_KEY rule execution not fully implemented in this demo"
        }
    
    def _execute_regex(self, column: str, pattern: str) -> Dict:
        """Execute REGEX rule."""
        if column not in self.df.columns:
            return {
                'passed': 0,
                'failed': len(self.df),
                'error': f"Column '{column}' not found",
                'sample_evidence': []
            }
        
        # Check if column contains string data
        if not self.df[column].dtype == 'object':
            return {
                'passed': 0,
                'failed': len(self.df),
                'error': f"Column '{column}' is not of string type",
                'sample_evidence': []
            }
        
        # Create mask for values matching the regex pattern
        try:
            regex_mask = self.df[column].str.match(pattern, na=False)
        except re.error as e:
            return {
                'passed': 0,
                'failed': len(self.df),
                'error': f"Invalid regex pattern '{pattern}': {str(e)}",
                'sample_evidence': []
            }
        
        failed_count = (~regex_mask).sum()
        passed_count = len(self.df) - failed_count
        
        # Get sample evidence (first 5 non-matching rows)
        sample_evidence = []
        if failed_count > 0:
            sample_evidence = self.df[~regex_mask].head(5).to_dict('records')
        
        return {
            'passed': passed_count,
            'failed': failed_count,
            'sample_evidence': sample_evidence
        }
    
    def _execute_length_range(self, column: str, min_length: int, max_length: int) -> Dict:
        """Execute LENGTH_RANGE rule."""
        if column not in self.df.columns:
            return {
                'passed': 0,
                'failed': len(self.df),
                'error': f"Column '{column}' not found",
                'sample_evidence': []
            }
        
        # Check if column contains string data
        if not self.df[column].dtype == 'object':
            # Convert to string for length calculation
            column_data = self.df[column].astype(str)
        else:
            column_data = self.df[column]
        
        # Calculate string lengths
        lengths = column_data.str.len()
        
        # Create mask for values within length range
        length_mask = (lengths >= min_length) & (lengths <= max_length)
        
        failed_count = (~length_mask).sum()
        passed_count = len(self.df) - failed_count
        
        # Get sample evidence (first 5 out-of-length-range rows)
        sample_evidence = []
        if failed_count > 0:
            sample_evidence = self.df[~length_mask].head(5).to_dict('records')
        
        return {
            'passed': passed_count,
            'failed': failed_count,
            'sample_evidence': sample_evidence
        }


def compute_run_id(dataset_id, rule_id, timestamp):
    """Compute a deterministic run ID based on inputs."""
    import hashlib
    input_str = f"{dataset_id}:{rule_id}:{timestamp.isoformat()}"
    return hashlib.md5(input_str.encode()).hexdigest()


def compile_to_sql(dsl_expression):
    """Compile DSL expression to SQL (simplified implementation)."""
    # This is a placeholder implementation
    # In a real system, you would parse the DSL and generate proper SQL
    return f"-- SQL for {dsl_expression}"


def execute_custom_python_rule(lambda_expr, df):
    """Execute a custom Python rule (simplified implementation)."""
    # This is a placeholder implementation
    # In a real system, you would safely evaluate the lambda expression
    return pd.Series([True] * len(df))