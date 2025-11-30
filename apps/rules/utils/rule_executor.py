import pandas as pd
import os
import hashlib
from datetime import datetime
from django.conf import settings
from django.utils import timezone
from django.db.models import Q, Count
from django.db.models.functions import TruncDate
from .dsl_parser import DSLParser, compile_to_sql, execute_custom_python_rule, compute_run_id
from apps.rules.models import Rule, RuleRun
from apps.incidents.models import Incident

class RuleExecutor:
    """
    Execute rules and create incidents with evidence
    """
    
    def __init__(self, rule, dataset):
        self.rule = rule
        self.dataset = dataset
        self.parser = DSLParser()
    
    def execute(self, run_timestamp=None):
        """
        Execute a rule and return results
        """
        if run_timestamp is None:
            run_timestamp = timezone.now()
        
        # Compute deterministic run_id
        run_id = compute_run_id(self.dataset.id, self.rule.id, run_timestamp)
        
        # Check if this run already exists (idempotency)
        existing_run = RuleRun.objects.filter(run_id=run_id).first()
        if existing_run:
            return existing_run
        
        # Create RuleRun record
        rule_run = RuleRun.objects.create(
            rule=self.rule,
            dataset=self.dataset,
            run_id=run_id,
            started_at=run_timestamp,
            status='RUNNING'
        )
        
        try:
            # Load dataset
            df = self._load_dataset()
            if df is None:
                rule_run.status = 'FAILED'
                rule_run.finished_at = timezone.now()
                rule_run.save()
                return rule_run
            
            total_rows = len(df)
            
            # Parse DSL expression
            try:
                func_name, args = self.parser.parse(self.rule.dsl_expression)
                # Convert tuple to dictionary for compatibility
                parsed_rule = {'type': func_name}
                if func_name == 'NOT_NULL':
                    parsed_rule['column'] = args[0]
                elif func_name == 'UNIQUE':
                    parsed_rule['column'] = args[0]
                elif func_name == 'IN_RANGE':
                    parsed_rule['column'] = args[0]
                    parsed_rule['min'] = args[1]
                    parsed_rule['max'] = args[2]
                elif func_name == 'FOREIGN_KEY':
                    parsed_rule['column'] = args[0]
                    parsed_rule['ref_table'] = args[1]
                    parsed_rule['ref_column'] = args[2]
                elif func_name == 'REGEX':
                    parsed_rule['column'] = args[0]
                    parsed_rule['pattern'] = args[1]
                elif func_name == 'LENGTH_RANGE':
                    parsed_rule['column'] = args[0]
                    parsed_rule['min_length'] = args[1]
                    parsed_rule['max_length'] = args[2]
            except Exception as e:
                rule_run.status = 'FAILED'
                rule_run.finished_at = timezone.now()
                rule_run.save()
                raise ValueError(f"Failed to parse DSL expression: {str(e)}")
            
            # Apply rule
            failed_mask, failed_rows, passed_rows = self._apply_rule(df, parsed_rule)
            
            # Update RuleRun
            rule_run.total_rows = total_rows
            rule_run.passed_count = passed_rows
            rule_run.failed_count = failed_rows
            rule_run.finished_at = timezone.now()
            rule_run.status = 'COMPLETED'
            
            print(f"Updating rule run {rule_run.id}: passed={passed_rows}, failed={failed_rows}, total={total_rows}")  # Debug log
            
            # Save evidence if there are failures
            if failed_rows > 0:
                evidence_data = self._generate_evidence(df, failed_mask, parsed_rule)
                rule_run.sample_evidence = evidence_data
                
                # Save evidence to file if needed
                if len(str(evidence_data)) > 10000:  # If evidence is large, save to file
                    evidence_filename = f'evidence_{run_id}.csv'
                    evidence_path = os.path.join(settings.MEDIA_ROOT, 'evidences', evidence_filename)
                    
                    # Ensure evidences directory exists
                    os.makedirs(os.path.dirname(evidence_path), exist_ok=True)
                    
                    # Save evidence
                    evidence_df = df[failed_mask].head(50)  # Limit to 50 rows
                    evidence_df.to_csv(evidence_path, index=False)
                    rule_run.evidence_file = f'evidences/{evidence_filename}'
            
            rule_run.save()
            
            # Update dataset quality trend data
            self._update_dataset_quality_trend()
            
            # Create or update incidents
            if failed_rows > 0:
                self._create_or_update_incident(rule_run, failed_rows, total_rows, evidence_data)
            
            return rule_run
            
        except Exception as e:
            # Update RuleRun with failure
            rule_run.status = 'FAILED'
            rule_run.finished_at = timezone.now()
            rule_run.save()
            raise e
    
    def _load_dataset(self):
        """
        Load dataset into pandas DataFrame
        """
        if self.dataset.source_type == 'CSV' and self.dataset.file:
            file_path = self.dataset.file.path
            if os.path.exists(file_path):
                try:
                    # Try to read CSV with different encodings
                    try:
                        return pd.read_csv(file_path, encoding='utf-8')
                    except UnicodeDecodeError:
                        try:
                            return pd.read_csv(file_path, encoding='latin1')
                        except UnicodeDecodeError:
                            return pd.read_csv(file_path, encoding='cp1252')
                except Exception as e:
                    print(f"Error reading CSV file: {e}")
                    raise FileNotFoundError(f"Could not read CSV file: {file_path}")
            else:
                raise FileNotFoundError(f"Dataset file not found: {file_path}")
        elif self.dataset.source_type == 'DB':
            # For database datasets, we would need to implement database connection
            # This is a simplified implementation
            raise NotImplementedError("Database datasets not implemented yet")
        else:
            raise ValueError(f"Unsupported dataset source type: {self.dataset.source_type}")
    
    def _apply_rule(self, df, parsed_rule):
        """
        Apply rule to DataFrame and return results
        """
        rule_type = parsed_rule['type']
        column = parsed_rule.get('column')
        
        # Check if column exists in DataFrame
        if column and column not in df.columns:
            raise ValueError(f"Column '{column}' not found in dataset")
        
        if rule_type == 'NOT_NULL':
            # Find rows where column is null
            failed_mask = df[column].isnull()
        elif rule_type == 'UNIQUE':
            # Find rows where column values are not unique
            duplicated_mask = df[column].duplicated(keep=False)
            failed_mask = duplicated_mask
        elif rule_type == 'IN_RANGE':
            # Find rows where column values are outside range
            range_min = parsed_rule.get('min')
            range_max = parsed_rule.get('max')
            failed_mask = pd.Series([False] * len(df))
            
            if range_min is not None:
                failed_mask |= (df[column] < range_min)
            if range_max is not None:
                failed_mask |= (df[column] > range_max)
        elif rule_type == 'LENGTH_RANGE':
            # Find rows where column values are outside length range
            min_length = parsed_rule.get('min_length', 0)
            max_length = parsed_rule.get('max_length', 1000)
            
            # Check if column contains string data
            if not df[column].dtype == 'object':
                # Convert to string for length calculation
                column_data = df[column].astype(str)
            else:
                column_data = df[column]
            
            # Calculate string lengths
            lengths = column_data.str.len()
            
            # Create mask for values outside length range
            failed_mask = (lengths < min_length) | (lengths > max_length)
        elif rule_type == 'MATCHES' or rule_type == 'REGEX':
            # Find rows where column values don't match pattern
            pattern = parsed_rule.get('pattern')
            try:
                failed_mask = ~df[column].str.match(pattern, na=False)
            except Exception:
                failed_mask = pd.Series([True] * len(df))  # If pattern is invalid, mark all as failed
        elif rule_type == 'FK':
            # Foreign key validation would require checking against another dataset
            # This is a simplified implementation
            failed_mask = pd.Series([False] * len(df))
        elif rule_type == 'CUSTOM_PYTHON':
            # Execute custom Python rule
            lambda_expr = parsed_rule.get('lambda_expr')
            try:
                result = execute_custom_python_rule(lambda_expr, df)
                if isinstance(result, pd.Series):
                    failed_mask = result
                else:
                    failed_mask = pd.Series([bool(result)] * len(df))
            except Exception:
                failed_mask = pd.Series([True] * len(df))  # If execution fails, mark all as failed
        else:
            raise ValueError(f"Unsupported rule type: {rule_type}")
        
        failed_rows = failed_mask.sum()
        passed_rows = len(df) - failed_rows
        
        return failed_mask, failed_rows, passed_rows
    
    def _generate_evidence(self, df, failed_mask, parsed_rule):
        """
        Generate evidence data for failed rows
        """
        failed_df = df[failed_mask]
        total_failed = len(failed_df)
        
        # Limit evidence to first 50 rows to avoid oversized data
        evidence_df = failed_df.head(50)
        
        evidence = {
            'total_failed': total_failed,
            'sample_rows': evidence_df.to_dict('records') if not evidence_df.empty else [],
            'columns': list(df.columns),
            'rule_type': parsed_rule['type'],
            'timestamp': timezone.now().isoformat()
        }
        
        return evidence
    
    def _update_dataset_quality_trend(self):
        """
        Update the dataset's quality trend data with rule-level pass/fail rates
        """
        try:
            from django.utils import timezone
            from datetime import timedelta
            
            # Get executions for last 7 days for this dataset
            week_ago = timezone.now() - timedelta(days=7)
            
            # Get daily aggregations (existing functionality)
            daily_executions = RuleRun.objects.filter(
                dataset=self.dataset,
                started_at__gte=week_ago
            ).annotate(
                date=TruncDate('started_at')
            ).values(
                'date'
            ).annotate(
                passed=Count('id', filter=Q(failed_count=0)),
                failed=Count('id', filter=~Q(failed_count=0))
            ).order_by('date')
            
            # Get rule-level pass/fail rates for the latest execution of each rule
            rule_rates = []
            # Get latest run for each rule
            from django.db.models import Max
            latest_runs = RuleRun.objects.filter(
                dataset=self.dataset
            ).values('rule').annotate(
                latest_run=Max('started_at')
            )
            
            for item in latest_runs:
                latest_run = RuleRun.objects.filter(
                    rule=item['rule'],
                    started_at=item['latest_run']
                ).first()
                
                if latest_run:
                    total = latest_run.passed_count + latest_run.failed_count
                    pass_rate = (latest_run.passed_count / total * 100) if total > 0 else 0
                    rule_rates.append({
                        'rule_name': latest_run.rule.name,
                        'pass_rate': round(pass_rate, 2),
                        'total_executions': RuleRun.objects.filter(rule=latest_run.rule).count()
                    })
            
            # Format data for storage
            trend_data = [
                {
                    'date': execution['date'].strftime('%Y-%m-%d'),
                    'passed': execution['passed'],
                    'failed': execution['failed']
                }
                for execution in daily_executions
            ]
            
            # Update dataset with trend data and rule rates
            self.dataset.quality_trend_data = trend_data
            self.dataset.rule_pass_rates = rule_rates
            self.dataset.save(update_fields=['quality_trend_data', 'rule_pass_rates'])
            
        except Exception as e:
            print(f"Error updating dataset quality trend: {e}")

    def _create_or_update_incident(self, rule_run, failed_rows, total_rows, evidence_data):
        """
        Create or update an incident based on rule run results
        """
        # Check if an incident already exists for this rule and dataset
        existing_incident = Incident.objects.filter(
            rule=self.rule,
            dataset=self.dataset,
            status__in=['OPEN', 'ACKNOWLEDGED', 'MUTED']  # Not resolved
        ).order_by('-created_at').first()
        
        if existing_incident:
            # Update existing incident
            existing_incident.updated_at = timezone.now()
            existing_incident.save()
        else:
            # Create new incident
            Incident.objects.create(
                rule=self.rule,
                rule_run=rule_run,
                dataset=self.dataset,
                severity=self.rule.severity,
                title=f'Rule failed: {self.rule.name}',
                description=f'Rule {self.rule.name} failed on {failed_rows} out of {total_rows} rows',
                evidence=str(evidence_data),
                status='OPEN'
            )