"""Business Intelligence analyzer for computing metrics and insights."""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict
import statistics

from app.services.query_engine import TimeRange, TimeRangeCalculator
from app.services.data_resilience import DataQualityReport


@dataclass
class PipelineMetrics:
    """Metrics for sales pipeline analysis."""
    total_deals: int
    total_pipeline_value: float
    weighted_pipeline_value: float
    avg_deal_size: float
    deals_by_stage: Dict[str, int]
    value_by_stage: Dict[str, float]
    conversion_rate: Optional[float]
    win_rate: Optional[float]
    sector_breakdown: Dict[str, Dict[str, Any]]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_deals": self.total_deals,
            "total_pipeline_value": round(self.total_pipeline_value, 2),
            "weighted_pipeline_value": round(self.weighted_pipeline_value, 2),
            "avg_deal_size": round(self.avg_deal_size, 2),
            "deals_by_stage": self.deals_by_stage,
            "value_by_stage": {k: round(v, 2) for k, v in self.value_by_stage.items()},
            "conversion_rate": round(self.conversion_rate, 2) if self.conversion_rate else None,
            "win_rate": round(self.win_rate, 2) if self.win_rate else None,
            "sector_breakdown": self.sector_breakdown
        }


@dataclass
class RevenueMetrics:
    """Metrics for revenue analysis."""
    total_revenue: float
    recognized_revenue: float
    forecasted_revenue: float
    revenue_by_sector: Dict[str, float]
    revenue_by_month: Dict[str, float]
    ytd_revenue: float
    growth_rate: Optional[float]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_revenue": round(self.total_revenue, 2),
            "recognized_revenue": round(self.recognized_revenue, 2),
            "forecasted_revenue": round(self.forecasted_revenue, 2),
            "revenue_by_sector": {k: round(v, 2) for k, v in self.revenue_by_sector.items()},
            "revenue_by_month": {k: round(v, 2) for k, v in self.revenue_by_month.items()},
            "ytd_revenue": round(self.ytd_revenue, 2),
            "growth_rate": round(self.growth_rate, 2) if self.growth_rate else None
        }


@dataclass
class ExecutionMetrics:
    """Metrics for work order execution analysis."""
    total_work_orders: int
    completed_orders: int
    in_progress_orders: int
    on_hold_orders: int
    completion_rate: float
    avg_completion_time_days: Optional[float]
    orders_by_status: Dict[str, int]
    orders_by_sector: Dict[str, int]
    delivered_revenue: float
    backlog_value: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_work_orders": self.total_work_orders,
            "completed_orders": self.completed_orders,
            "in_progress_orders": self.in_progress_orders,
            "on_hold_orders": self.on_hold_orders,
            "completion_rate": round(self.completion_rate, 2),
            "avg_completion_time_days": round(self.avg_completion_time_days, 2) if self.avg_completion_time_days else None,
            "orders_by_status": self.orders_by_status,
            "orders_by_sector": self.orders_by_sector,
            "delivered_revenue": round(self.delivered_revenue, 2),
            "backlog_value": round(self.backlog_value, 2)
        }


@dataclass
class LeadershipSummary:
    """Executive summary for leadership updates."""
    period: str
    pipeline_health: str
    key_highlights: List[str]
    risks: List[str]
    opportunities: List[str]
    pipeline_metrics: PipelineMetrics
    revenue_metrics: RevenueMetrics
    execution_metrics: ExecutionMetrics
    data_quality: DataQualityReport
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "period": self.period,
            "pipeline_health": self.pipeline_health,
            "key_highlights": self.key_highlights,
            "risks": self.risks,
            "opportunities": self.opportunities,
            "pipeline_metrics": self.pipeline_metrics.to_dict(),
            "revenue_metrics": self.revenue_metrics.to_dict(),
            "execution_metrics": self.execution_metrics.to_dict(),
            "data_quality": {
                "total_records": self.data_quality.total_records,
                "valid_records": self.data_quality.valid_records,
                "confidence_score": round(self.data_quality.confidence_score, 1),
                "warnings": self.data_quality.warnings[:5]  # Limit warnings
            }
        }


class PipelineAnalyzer:
    """Analyze sales pipeline data."""
    
    # Stage weights for pipeline forecasting (simplified)
    STAGE_WEIGHTS = {
        'Lead': 0.1,
        'Qualified': 0.25,
        'Proposal': 0.5,
        'Negotiation': 0.75,
        'Closed Won': 1.0,
        'Closed Lost': 0.0,
    }
    
    def analyze(self, deals: List[Dict[str, Any]], sector_filter: Optional[str] = None) -> PipelineMetrics:
        """Analyze pipeline data and compute metrics."""
        # Filter by sector if specified
        if sector_filter:
            deals = [d for d in deals if d.get('sector', '').lower() == sector_filter.lower()]
        
        total_deals = len(deals)
        
        if total_deals == 0:
            return PipelineMetrics(
                total_deals=0,
                total_pipeline_value=0.0,
                weighted_pipeline_value=0.0,
                avg_deal_size=0.0,
                deals_by_stage={},
                value_by_stage={},
                conversion_rate=None,
                win_rate=None,
                sector_breakdown={}
            )
        
        # Calculate total pipeline value
        total_value = sum(d.get('amount', 0) or 0 for d in deals)
        
        # Calculate weighted pipeline value
        weighted_value = 0.0
        for deal in deals:
            amount = deal.get('amount', 0) or 0
            stage = deal.get('stage', 'Lead')
            weight = self.STAGE_WEIGHTS.get(stage, 0.1)
            weighted_value += amount * weight
        
        # Average deal size
        avg_deal_size = total_value / total_deals if total_deals > 0 else 0
        
        # Deals and value by stage
        deals_by_stage = defaultdict(int)
        value_by_stage = defaultdict(float)
        
        for deal in deals:
            stage = deal.get('stage', 'Unknown')
            deals_by_stage[stage] += 1
            value_by_stage[stage] += deal.get('amount', 0) or 0
        
        # Conversion rate (Qualified to Closed Won)
        qualified_count = sum(1 for d in deals if d.get('stage') in ['Qualified', 'Proposal', 'Negotiation', 'Closed Won'])
        won_count = sum(1 for d in deals if d.get('stage') == 'Closed Won')
        conversion_rate = (won_count / qualified_count * 100) if qualified_count > 0 else None
        
        # Win rate (Closed Won / (Closed Won + Closed Lost))
        lost_count = sum(1 for d in deals if d.get('stage') == 'Closed Lost')
        total_closed = won_count + lost_count
        win_rate = (won_count / total_closed * 100) if total_closed > 0 else None
        
        # Sector breakdown
        sector_data = defaultdict(lambda: {'count': 0, 'value': 0.0})
        for deal in deals:
            sector = deal.get('sector', 'Unknown') or 'Unknown'
            sector_data[sector]['count'] += 1
            sector_data[sector]['value'] += deal.get('amount', 0) or 0
        
        return PipelineMetrics(
            total_deals=total_deals,
            total_pipeline_value=total_value,
            weighted_pipeline_value=weighted_value,
            avg_deal_size=avg_deal_size,
            deals_by_stage=dict(deals_by_stage),
            value_by_stage=dict(value_by_stage),
            conversion_rate=conversion_rate,
            win_rate=win_rate,
            sector_breakdown=dict(sector_data)
        )


class RevenueAnalyzer:
    """Analyze revenue data from work orders."""
    
    def analyze(self, work_orders: List[Dict[str, Any]], sector_filter: Optional[str] = None) -> RevenueMetrics:
        """Analyze revenue data and compute metrics."""
        # Filter by sector if specified
        if sector_filter:
            work_orders = [w for w in work_orders if w.get('sector', '').lower() == sector_filter.lower()]
        
        # Calculate metrics
        total_revenue = sum(w.get('revenue', 0) or 0 for w in work_orders)
        
        # Recognized revenue (from completed orders)
        recognized = sum(
            w.get('revenue', 0) or 0 
            for w in work_orders 
            if w.get('status') == 'Completed'
        )
        
        # Forecasted revenue (in progress + planning)
        forecasted = sum(
            w.get('revenue', 0) or 0 
            for w in work_orders 
            if w.get('status') in ['In Progress', 'Planning']
        )
        
        # Revenue by sector
        revenue_by_sector = defaultdict(float)
        for wo in work_orders:
            sector = wo.get('sector', 'Unknown') or 'Unknown'
            revenue_by_sector[sector] += wo.get('revenue', 0) or 0
        
        # Revenue by month (simplified)
        revenue_by_month = defaultdict(float)
        for wo in work_orders:
            date = wo.get('date')
            if date and isinstance(date, datetime):
                month_key = date.strftime('%Y-%m')
                revenue_by_month[month_key] += wo.get('revenue', 0) or 0
        
        # YTD revenue
        current_year = datetime.now().year
        ytd = sum(
            w.get('revenue', 0) or 0 
            for w in work_orders 
            if w.get('date') and isinstance(w.get('date'), datetime) and w.get('date').year == current_year
        )
        
        return RevenueMetrics(
            total_revenue=total_revenue,
            recognized_revenue=recognized,
            forecasted_revenue=forecasted,
            revenue_by_sector=dict(revenue_by_sector),
            revenue_by_month=dict(revenue_by_month),
            ytd_revenue=ytd,
            growth_rate=None  # Would need historical data
        )


class ExecutionAnalyzer:
    """Analyze work order execution data."""
    
    def analyze(self, work_orders: List[Dict[str, Any]], sector_filter: Optional[str] = None) -> ExecutionMetrics:
        """Analyze execution data and compute metrics."""
        # Filter by sector if specified
        if sector_filter:
            work_orders = [w for w in work_orders if w.get('sector', '').lower() == sector_filter.lower()]
        
        total = len(work_orders)
        
        if total == 0:
            return ExecutionMetrics(
                total_work_orders=0,
                completed_orders=0,
                in_progress_orders=0,
                on_hold_orders=0,
                completion_rate=0.0,
                avg_completion_time_days=None,
                orders_by_status={},
                orders_by_sector={},
                delivered_revenue=0.0,
                backlog_value=0.0
            )
        
        # Count by status
        completed = sum(1 for w in work_orders if w.get('status') == 'Completed')
        in_progress = sum(1 for w in work_orders if w.get('status') == 'In Progress')
        on_hold = sum(1 for w in work_orders if w.get('status') == 'On Hold')
        planning = sum(1 for w in work_orders if w.get('status') == 'Planning')
        
        # Completion rate
        completion_rate = (completed / total * 100) if total > 0 else 0.0
        
        # Orders by status
        orders_by_status = {
            'Planning': planning,
            'In Progress': in_progress,
            'Completed': completed,
            'On Hold': on_hold
        }
        
        # Orders by sector
        orders_by_sector = defaultdict(int)
        for wo in work_orders:
            sector = wo.get('sector', 'Unknown') or 'Unknown'
            orders_by_sector[sector] += 1
        
        # Delivered revenue (completed orders)
        delivered = sum(
            w.get('revenue', 0) or 0 
            for w in work_orders 
            if w.get('status') == 'Completed'
        )
        
        # Backlog value (in progress + planning)
        backlog = sum(
            w.get('revenue', 0) or 0 
            for w in work_orders 
            if w.get('status') in ['In Progress', 'Planning']
        )
        
        return ExecutionMetrics(
            total_work_orders=total,
            completed_orders=completed,
            in_progress_orders=in_progress,
            on_hold_orders=on_hold,
            completion_rate=completion_rate,
            avg_completion_time_days=None,  # Would need start/end dates
            orders_by_status=orders_by_status,
            orders_by_sector=dict(orders_by_sector),
            delivered_revenue=delivered,
            backlog_value=backlog
        )


class LeadershipAnalyzer:
    """Generate leadership summaries and insights."""
    
    def generate_summary(
        self,
        pipeline_metrics: PipelineMetrics,
        revenue_metrics: RevenueMetrics,
        execution_metrics: ExecutionMetrics,
        data_quality: DataQualityReport,
        time_range: TimeRange
    ) -> LeadershipSummary:
        """Generate executive summary for leadership."""
        
        # Determine pipeline health
        pipeline_health = self._assess_pipeline_health(pipeline_metrics)
        
        # Generate key highlights
        highlights = self._generate_highlights(
            pipeline_metrics, revenue_metrics, execution_metrics
        )
        
        # Identify risks
        risks = self._identify_risks(
            pipeline_metrics, revenue_metrics, execution_metrics
        )
        
        # Identify opportunities
        opportunities = self._identify_opportunities(
            pipeline_metrics, revenue_metrics, execution_metrics
        )
        
        period_str = self._get_period_string(time_range)
        
        return LeadershipSummary(
            period=period_str,
            pipeline_health=pipeline_health,
            key_highlights=highlights,
            risks=risks,
            opportunities=opportunities,
            pipeline_metrics=pipeline_metrics,
            revenue_metrics=revenue_metrics,
            execution_metrics=execution_metrics,
            data_quality=data_quality
        )
    
    def _assess_pipeline_health(self, metrics: PipelineMetrics) -> str:
        """Assess overall pipeline health."""
        if metrics.total_deals == 0:
            return "No Data"
        
        score = 0
        
        # Check win rate
        if metrics.win_rate and metrics.win_rate > 30:
            score += 2
        elif metrics.win_rate and metrics.win_rate > 15:
            score += 1
        
        # Check pipeline value
        if metrics.total_pipeline_value > 1000000:
            score += 2
        elif metrics.total_pipeline_value > 500000:
            score += 1
        
        # Check avg deal size
        if metrics.avg_deal_size > 50000:
            score += 1
        
        if score >= 4:
            return "Strong"
        elif score >= 2:
            return "Healthy"
        else:
            return "Needs Attention"
    
    def _generate_highlights(
        self,
        pipeline: PipelineMetrics,
        revenue: RevenueMetrics,
        execution: ExecutionMetrics
    ) -> List[str]:
        """Generate key highlights from the data."""
        highlights = []
        
        if pipeline.total_deals > 0:
            highlights.append(
                f"Pipeline contains {pipeline.total_deals} deals worth ${pipeline.total_pipeline_value:,.0f}"
            )
        
        if pipeline.win_rate:
            highlights.append(f"Win rate of {pipeline.win_rate:.1f}% indicates {'strong' if pipeline.win_rate > 30 else 'moderate' if pipeline.win_rate > 15 else 'challenging'} sales performance")
        
        if execution.completion_rate > 70:
            highlights.append(f"High execution efficiency with {execution.completion_rate:.1f}% of work orders completed")
        
        if revenue.ytd_revenue > 0:
            highlights.append(f"YTD revenue of ${revenue.ytd_revenue:,.0f}")
        
        return highlights[:4]  # Limit to top 4
    
    def _identify_risks(
        self,
        pipeline: PipelineMetrics,
        revenue: RevenueMetrics,
        execution: ExecutionMetrics
    ) -> List[str]:
        """Identify potential risks from the data."""
        risks = []
        
        if pipeline.win_rate and pipeline.win_rate < 20:
            risks.append("Low win rate may indicate issues with deal qualification or competitive positioning")
        
        if execution.on_hold_orders > execution.total_work_orders * 0.2:
            risks.append(f"High number of on-hold orders ({execution.on_hold_orders}) may indicate delivery challenges")
        
        if pipeline.total_pipeline_value < 500000:
            risks.append("Pipeline value is below typical targets")
        
        return risks if risks else ["No significant risks identified"]
    
    def _identify_opportunities(
        self,
        pipeline: PipelineMetrics,
        revenue: RevenueMetrics,
        execution: ExecutionMetrics
    ) -> List[str]:
        """Identify opportunities from the data."""
        opportunities = []
        
        # Find top sector
        if pipeline.sector_breakdown:
            top_sector = max(pipeline.sector_breakdown.items(), key=lambda x: x[1]['value'])
            opportunities.append(f"{top_sector[0]} sector shows strongest pipeline at ${top_sector[1]['value']:,.0f}")
        
        if execution.backlog_value > 0:
            opportunities.append(f"${execution.backlog_value:,.0f} in backlog represents near-term revenue opportunity")
        
        # Check for deals in late stages
        late_stage_value = sum(
            v for k, v in pipeline.value_by_stage.items() 
            if k in ['Negotiation', 'Proposal']
        )
        if late_stage_value > 0:
            opportunities.append(f"${late_stage_value:,.0f} in late-stage deals close to closing")
        
        return opportunities if opportunities else ["Continue current growth trajectory"]
    
    def _get_period_string(self, time_range: TimeRange) -> str:
        """Convert time range to readable string."""
        period_map = {
            TimeRange.THIS_QUARTER: "This Quarter",
            TimeRange.NEXT_QUARTER: "Next Quarter",
            TimeRange.THIS_YEAR: "Year to Date",
            TimeRange.LAST_QUARTER: "Last Quarter",
            TimeRange.LAST_30_DAYS: "Last 30 Days",
            TimeRange.LAST_90_DAYS: "Last 90 Days",
            TimeRange.ALL_TIME: "All Time",
        }
        return period_map.get(time_range, "Custom Period")