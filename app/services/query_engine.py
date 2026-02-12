"""Query understanding and business intelligence engine."""
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum


class QueryType(Enum):
    """Types of business intelligence queries."""
    PIPELINE_OVERVIEW = "pipeline_overview"
    REVENUE_FORECAST = "revenue_forecast"
    SECTOR_ANALYSIS = "sector_analysis"
    EXECUTION_STATUS = "execution_status"
    LEADERSHIP_UPDATE = "leadership_update"
    CUSTOM_QUERY = "custom_query"
    UNKNOWN = "unknown"


class TimeRange(Enum):
    """Common time range filters."""
    THIS_QUARTER = "this_quarter"
    NEXT_QUARTER = "next_quarter"
    THIS_YEAR = "this_year"
    LAST_QUARTER = "last_quarter"
    LAST_30_DAYS = "last_30_days"
    LAST_90_DAYS = "last_90_days"
    CUSTOM = "custom"
    ALL_TIME = "all_time"


@dataclass
class ParsedQuery:
    """Parsed business query with extracted parameters."""
    original_query: str
    query_type: QueryType
    time_range: TimeRange
    sector: Optional[str]
    stage_filter: Optional[str]
    status_filter: Optional[str]
    metrics_requested: List[str]
    confidence: float
    clarification_needed: Optional[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "original_query": self.original_query,
            "query_type": self.query_type.value,
            "time_range": self.time_range.value,
            "sector": self.sector,
            "stage_filter": self.stage_filter,
            "status_filter": self.status_filter,
            "metrics_requested": self.metrics_requested,
            "confidence": self.confidence,
            "clarification_needed": self.clarification_needed
        }


class QueryParser:
    """Parse natural language business queries into structured parameters."""
    
    # Keywords for query type detection
    PIPELINE_KEYWORDS = [
        'pipeline', 'deals', 'sales', 'opportunities', 'forecast',
        'funnel', 'prospects', 'leads', 'closed won', 'closed lost'
    ]
    
    REVENUE_KEYWORDS = [
        'revenue', 'income', 'earnings', 'money', 'financial',
        'value', 'worth', 'amount', 'booking'
    ]
    
    EXECUTION_KEYWORDS = [
        'work order', 'project', 'delivery', 'execution', 'operational',
        'work orders', 'projects', 'delivered', 'completion'
    ]
    
    LEADERSHIP_KEYWORDS = [
        'update', 'summary', 'report', 'overview', 'status',
        'leadership', 'board', 'executive', 'kpi', 'metrics'
    ]
    
    # Sector keywords
    SECTOR_KEYWORDS = {
        'energy': ['energy', 'power', 'utilities', 'oil', 'gas', 'renewable'],
        'technology': ['technology', 'tech', 'software', 'it', 'digital'],
        'healthcare': ['healthcare', 'health', 'medical', 'pharma'],
        'finance': ['finance', 'financial', 'banking', 'fintech'],
        'manufacturing': ['manufacturing', 'industrial', 'production'],
        'retail': ['retail', 'ecommerce', 'consumer'],
        'education': ['education', 'edtech', 'learning'],
        'government': ['government', 'public sector', 'govt'],
    }
    
    # Time range keywords
    TIME_KEYWORDS = {
        TimeRange.THIS_QUARTER: ['this quarter', 'current quarter', 'q1', 'q2', 'q3', 'q4'],
        TimeRange.NEXT_QUARTER: ['next quarter', 'upcoming quarter'],
        TimeRange.THIS_YEAR: ['this year', 'current year', 'ytd', 'year to date'],
        TimeRange.LAST_QUARTER: ['last quarter', 'previous quarter', 'past quarter'],
        TimeRange.LAST_30_DAYS: ['last 30 days', 'past 30 days', 'last month', 'past month'],
        TimeRange.LAST_90_DAYS: ['last 90 days', 'past 90 days', 'last quarter'],
    }
    
    def parse(self, query: str) -> ParsedQuery:
        """Parse a natural language query into structured parameters."""
        query_lower = query.lower()
        
        # Determine query type
        query_type = self._detect_query_type(query_lower)
        
        # Extract time range
        time_range = self._detect_time_range(query_lower)
        
        # Extract sector
        sector = self._detect_sector(query_lower)
        
        # Extract stage/status filters
        stage_filter = self._detect_stage_filter(query_lower)
        status_filter = self._detect_status_filter(query_lower)
        
        # Determine metrics requested
        metrics = self._detect_metrics(query_lower)
        
        # Calculate confidence
        confidence = self._calculate_confidence(
            query_type, time_range, sector, metrics
        )
        
        # Check if clarification is needed
        clarification = self._check_clarification_needed(
            query_type, sector, time_range, confidence
        )
        
        return ParsedQuery(
            original_query=query,
            query_type=query_type,
            time_range=time_range,
            sector=sector,
            stage_filter=stage_filter,
            status_filter=status_filter,
            metrics_requested=metrics,
            confidence=confidence,
            clarification_needed=clarification
        )
    
    def _detect_query_type(self, query: str) -> QueryType:
        """Detect the type of business query."""
        scores = {
            QueryType.PIPELINE_OVERVIEW: 0,
            QueryType.REVENUE_FORECAST: 0,
            QueryType.EXECUTION_STATUS: 0,
            QueryType.LEADERSHIP_UPDATE: 0,
        }
        
        for keyword in self.PIPELINE_KEYWORDS:
            if keyword in query:
                scores[QueryType.PIPELINE_OVERVIEW] += 1
        
        for keyword in self.REVENUE_KEYWORDS:
            if keyword in query:
                scores[QueryType.REVENUE_FORECAST] += 1
        
        for keyword in self.EXECUTION_KEYWORDS:
            if keyword in query:
                scores[QueryType.EXECUTION_STATUS] += 1
        
        for keyword in self.LEADERSHIP_KEYWORDS:
            if keyword in query:
                scores[QueryType.LEADERSHIP_UPDATE] += 1
        
        # Return the highest scoring type
        if max(scores.values()) > 0:
            return max(scores, key=scores.get)
        
        return QueryType.CUSTOM_QUERY
    
    def _detect_time_range(self, query: str) -> TimeRange:
        """Detect the time range filter from the query."""
        for time_range, keywords in self.TIME_KEYWORDS.items():
            for keyword in keywords:
                if keyword in query:
                    return time_range
        
        # Check for specific quarter mentions
        quarter_match = re.search(r'q([1-4])\s*(\d{4})?', query)
        if quarter_match:
            return TimeRange.CUSTOM
        
        return TimeRange.ALL_TIME
    
    def _detect_sector(self, query: str) -> Optional[str]:
        """Detect sector filter from the query."""
        for sector, keywords in self.SECTOR_KEYWORDS.items():
            for keyword in keywords:
                if keyword in query:
                    return sector.title()
        
        return None
    
    def _detect_stage_filter(self, query: str) -> Optional[str]:
        """Detect pipeline stage filter from the query."""
        stage_keywords = {
            'Lead': ['lead', 'prospect', 'new'],
            'Qualified': ['qualified', 'qualification'],
            'Proposal': ['proposal', 'quoted'],
            'Negotiation': ['negotiation', 'negotiating'],
            'Closed Won': ['won', 'closed won'],
            'Closed Lost': ['lost', 'closed lost'],
        }
        
        for stage, keywords in stage_keywords.items():
            for keyword in keywords:
                if keyword in query:
                    return stage
        
        return None
    
    def _detect_status_filter(self, query: str) -> Optional[str]:
        """Detect work order status filter from the query."""
        status_keywords = {
            'Planning': ['planning', 'planned'],
            'In Progress': ['in progress', 'active', 'ongoing'],
            'Completed': ['completed', 'done', 'finished'],
            'On Hold': ['on hold', 'hold', 'paused'],
        }
        
        for status, keywords in status_keywords.items():
            for keyword in keywords:
                if keyword in query:
                    return status
        
        return None
    
    def _detect_metrics(self, query: str) -> List[str]:
        """Detect which metrics are being requested."""
        metrics = []
        
        metric_keywords = {
            'revenue': ['revenue', 'income', 'earnings', 'value', 'amount'],
            'count': ['count', 'number', 'how many', 'total'],
            'conversion': ['conversion', 'win rate', 'close rate'],
            'avg_deal_size': ['average', 'avg', 'deal size'],
            'pipeline_value': ['pipeline', 'forecast'],
            'sector_breakdown': ['sector', 'industry', 'breakdown', 'by sector'],
            'trends': ['trend', 'growth', 'change', 'over time'],
        }
        
        for metric, keywords in metric_keywords.items():
            for keyword in keywords:
                if keyword in query:
                    metrics.append(metric)
                    break
        
        # Default metrics if none explicitly requested
        if not metrics:
            metrics = ['count', 'revenue']
        
        return metrics
    
    def _calculate_confidence(
        self, 
        query_type: QueryType, 
        time_range: TimeRange,
        sector: Optional[str],
        metrics: List[str]
    ) -> float:
        """Calculate confidence score for the parsed query."""
        confidence = 0.5  # Base confidence
        
        # Higher confidence if we detected query type
        if query_type != QueryType.UNKNOWN:
            confidence += 0.2
        
        # Higher confidence if time range was specified
        if time_range != TimeRange.ALL_TIME:
            confidence += 0.15
        
        # Higher confidence if sector was detected
        if sector:
            confidence += 0.15
        
        return min(confidence, 1.0)
    
    def _check_clarification_needed(
        self,
        query_type: QueryType,
        sector: Optional[str],
        time_range: TimeRange,
        confidence: float
    ) -> Optional[str]:
        """Check if we need to ask the user for clarification."""
        if confidence < 0.4:
            return "I'm not sure what you're asking. Could you clarify if you're asking about pipeline, revenue, or project execution?"
        
        if query_type == QueryType.UNKNOWN:
            return "Could you specify if you're asking about sales pipeline, revenue forecast, or work order execution?"
        
        return None


class TimeRangeCalculator:
    """Calculate date ranges from TimeRange enum."""
    
    @staticmethod
    def get_date_range(time_range: TimeRange) -> Tuple[Optional[datetime], Optional[datetime]]:
        """Get start and end dates for a time range."""
        now = datetime.now()
        
        if time_range == TimeRange.THIS_QUARTER:
            quarter = (now.month - 1) // 3
            start = datetime(now.year, quarter * 3 + 1, 1)
            if quarter == 3:
                end = datetime(now.year + 1, 1, 1)
            else:
                end = datetime(now.year, quarter * 3 + 4, 1)
            return start, end
        
        elif time_range == TimeRange.NEXT_QUARTER:
            quarter = (now.month - 1) // 3
            next_quarter = (quarter + 1) % 4
            year = now.year + (1 if next_quarter < quarter else 0)
            start = datetime(year, next_quarter * 3 + 1, 1)
            if next_quarter == 3:
                end = datetime(year + 1, 1, 1)
            else:
                end = datetime(year, next_quarter * 3 + 4, 1)
            return start, end
        
        elif time_range == TimeRange.THIS_YEAR:
            start = datetime(now.year, 1, 1)
            end = datetime(now.year + 1, 1, 1)
            return start, end
        
        elif time_range == TimeRange.LAST_QUARTER:
            quarter = (now.month - 1) // 3
            last_quarter = (quarter - 1) % 4
            year = now.year - (1 if last_quarter > quarter else 0)
            start = datetime(year, last_quarter * 3 + 1, 1)
            if last_quarter == 3:
                end = datetime(year + 1, 1, 1)
            else:
                end = datetime(year, last_quarter * 3 + 4, 1)
            return start, end
        
        elif time_range == TimeRange.LAST_30_DAYS:
            start = now - timedelta(days=30)
            return start, now
        
        elif time_range == TimeRange.LAST_90_DAYS:
            start = now - timedelta(days=90)
            return start, now
        
        return None, None