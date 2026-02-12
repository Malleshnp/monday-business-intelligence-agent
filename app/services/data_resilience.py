"""Data resilience layer for handling messy real-world data."""
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
import json


@dataclass
class DataQualityReport:
    """Report on data quality issues found during processing."""
    total_records: int
    valid_records: int
    missing_values: Dict[str, int]
    invalid_formats: Dict[str, int]
    excluded_records: int
    warnings: List[str]
    
    @property
    def confidence_score(self) -> float:
        """Calculate confidence score based on data quality."""
        if self.total_records == 0:
            return 0.0
        return (self.valid_records / self.total_records) * 100


class DataNormalizer:
    """Normalizes and validates data from Monday.com boards."""
    
    # Common date formats to try
    DATE_FORMATS = [
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%d/%m/%Y",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S",
        "%B %d, %Y",
        "%b %d, %Y",
        "%d-%b-%Y",
        "%m-%d-%Y",
    ]
    
    # Currency patterns
    CURRENCY_PATTERN = re.compile(r'[^\d.\-]')
    
    @staticmethod
    def parse_date(value: Any) -> Optional[datetime]:
        """Safely parse a date from various formats."""
        if value is None or value == "":
            return None
        
        if isinstance(value, datetime):
            return value
        
        value_str = str(value).strip()
        
        # Try each date format
        for fmt in DataNormalizer.DATE_FORMATS:
            try:
                return datetime.strptime(value_str, fmt)
            except ValueError:
                continue
        
        # Try ISO format with timezone
        try:
            return datetime.fromisoformat(value_str.replace('Z', '+00:00'))
        except ValueError:
            pass
        
        return None
    
    @staticmethod
    def parse_numeric(value: Any) -> Optional[float]:
        """Safely parse a numeric value, handling currency formats."""
        if value is None or value == "":
            return None
        
        if isinstance(value, (int, float)):
            return float(value)
        
        value_str = str(value).strip()
        
        # Remove currency symbols and other non-numeric characters
        cleaned = DataNormalizer.CURRENCY_PATTERN.sub('', value_str)
        
        try:
            return float(cleaned)
        except ValueError:
            return None
    
    @staticmethod
    def normalize_text(value: Any) -> Optional[str]:
        """Normalize text fields (strip, lowercase, handle nulls)."""
        if value is None:
            return None
        
        value_str = str(value).strip()
        if value_str == "" or value_str.lower() in ['null', 'none', 'n/a', 'na', '-']:
            return None
        
        return value_str
    
    @staticmethod
    def normalize_sector(value: Any) -> Optional[str]:
        """Normalize sector names to consistent categories."""
        text = DataNormalizer.normalize_text(value)
        if not text:
            return None
        
        text_lower = text.lower()
        
        # Map common variations to standard sectors
        sector_mapping = {
            'energy': ['energy', 'power', 'utilities', 'oil', 'gas', 'renewable'],
            'technology': ['tech', 'technology', 'software', 'it', 'digital', 'saas'],
            'healthcare': ['health', 'healthcare', 'medical', 'pharma', 'biotech'],
            'finance': ['finance', 'financial', 'banking', 'fintech', 'insurance'],
            'manufacturing': ['manufacturing', 'industrial', 'production', 'factory'],
            'retail': ['retail', 'ecommerce', 'e-commerce', 'consumer'],
            'education': ['education', 'edtech', 'learning', 'training'],
            'government': ['government', 'public sector', 'govt', 'municipal'],
        }
        
        for standard, variations in sector_mapping.items():
            if any(var in text_lower for var in variations):
                return standard.title()
        
        return text.title()
    
    @staticmethod
    def normalize_status(value: Any) -> Optional[str]:
        """Normalize status/stage values to consistent categories."""
        text = DataNormalizer.normalize_text(value)
        if not text:
            return None
        
        text_lower = text.lower()
        
        # Pipeline stages
        if any(word in text_lower for word in ['lead', 'prospect', 'new']):
            return 'Lead'
        elif any(word in text_lower for word in ['qualified', 'qualification']):
            return 'Qualified'
        elif any(word in text_lower for word in ['proposal', 'quoted', 'quote']):
            return 'Proposal'
        elif any(word in text_lower for word in ['negotiation', 'negotiating']):
            return 'Negotiation'
        elif any(word in text_lower for word in ['won', 'closed won', 'closed-won', 'deal won']):
            return 'Closed Won'
        elif any(word in text_lower for word in ['lost', 'closed lost', 'closed-lost', 'deal lost']):
            return 'Closed Lost'
        
        # Work order statuses
        if any(word in text_lower for word in ['planning', 'planned']):
            return 'Planning'
        elif any(word in text_lower for word in ['in progress', 'active', 'ongoing', 'started']):
            return 'In Progress'
        elif any(word in text_lower for word in ['completed', 'done', 'finished']):
            return 'Completed'
        elif any(word in text_lower for word in ['on hold', 'hold', 'paused']):
            return 'On Hold'
        elif any(word in text_lower for word in ['cancelled', 'canceled']):
            return 'Cancelled'
        
        return text.title()


class DataValidator:
    """Validates and reports on data quality."""
    
    def __init__(self):
        self.quality_report = DataQualityReport(
            total_records=0,
            valid_records=0,
            missing_values={},
            invalid_formats={},
            excluded_records=0,
            warnings=[]
        )
    
    def validate_records(self, records: List[Dict[str, Any]], required_fields: List[str] = None) -> Tuple[List[Dict[str, Any]], DataQualityReport]:
        """Validate a list of records and return clean data with quality report."""
        self.quality_report.total_records = len(records)
        valid_records = []
        
        for record in records:
            is_valid, issues = self._validate_single_record(record, required_fields)
            
            if is_valid:
                valid_records.append(record)
                self.quality_report.valid_records += 1
            else:
                self.quality_report.excluded_records += 1
                for issue in issues:
                    self.quality_report.warnings.append(issue)
        
        return valid_records, self.quality_report
    
    def _validate_single_record(self, record: Dict[str, Any], required_fields: List[str] = None) -> Tuple[bool, List[str]]:
        """Validate a single record and return validation status with issues."""
        issues = []
        is_valid = True
        
        if required_fields:
            for field in required_fields:
                if field not in record or record[field] is None:
                    self._track_missing_value(field)
                    issues.append(f"Missing required field: {field}")
                    is_valid = False
        
        return is_valid, issues
    
    def _track_missing_value(self, field: str):
        """Track missing values by field name."""
        if field not in self.quality_report.missing_values:
            self.quality_report.missing_values[field] = 0
        self.quality_report.missing_values[field] += 1
    
    def _track_invalid_format(self, field: str):
        """Track invalid format issues by field name."""
        if field not in self.quality_report.invalid_formats:
            self.quality_report.invalid_formats[field] = 0
        self.quality_report.invalid_formats[field] += 1


def extract_column_value(item: Dict[str, Any], column_title: str, normalizer_func = None) -> Any:
    """Extract a column value from a Monday.com item by column title."""
    column_values = item.get("column_values", [])
    
    for col in column_values:
        if col.get("column", {}).get("title", "").lower() == column_title.lower():
            value = col.get("text") or col.get("value")
            
            # Try to parse JSON values
            if value and isinstance(value, str) and value.startswith('{'):
                try:
                    parsed = json.loads(value)
                    if 'text' in parsed:
                        value = parsed['text']
                    elif 'label' in parsed:
                        value = parsed['label']
                except json.JSONDecodeError:
                    pass
            
            if normalizer_func and value is not None:
                return normalizer_func(value)
            return value
    
    return None


def transform_monday_items(items: List[Dict[str, Any]], column_mapping: Dict[str, str]) -> List[Dict[str, Any]]:
    """Transform Monday.com items into clean, normalized records."""
    normalized_records = []
    
    for item in items:
        record = {
            "id": item.get("id"),
            "name": item.get("name"),
            "created_at": item.get("created_at"),
            "updated_at": item.get("updated_at"),
        }
        
        for target_field, column_title in column_mapping.items():
            normalizer = None
            
            # Determine appropriate normalizer based on field name
            if 'date' in target_field.lower():
                normalizer = DataNormalizer.parse_date
            elif any(word in target_field.lower() for word in ['amount', 'value', 'revenue', 'cost', 'price']):
                normalizer = DataNormalizer.parse_numeric
            elif 'sector' in target_field.lower() or 'industry' in target_field.lower():
                normalizer = DataNormalizer.normalize_sector
            elif any(word in target_field.lower() for word in ['status', 'stage', 'state']):
                normalizer = DataNormalizer.normalize_status
            else:
                normalizer = DataNormalizer.normalize_text
            
            record[target_field] = extract_column_value(item, column_title, normalizer)
        
        normalized_records.append(record)
    
    return normalized_records