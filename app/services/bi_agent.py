"""Main Business Intelligence Agent service."""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import json

from app.services.monday_client import monday_client, MondayClient
from app.services.data_resilience import (
    DataNormalizer, DataValidator, transform_monday_items, 
    DataQualityReport
)
from app.services.query_engine import (
    QueryParser, ParsedQuery, QueryType, TimeRange, TimeRangeCalculator
)
from app.services.bi_analyzer import (
    PipelineAnalyzer, RevenueAnalyzer, ExecutionAnalyzer, LeadershipAnalyzer,
    PipelineMetrics, RevenueMetrics, ExecutionMetrics, LeadershipSummary
)
from app.core.config import settings


@dataclass
class BIResponse:
    """Structured response from the BI Agent."""
    executive_summary: str
    key_metrics: Dict[str, Any]
    data_quality: Dict[str, Any]
    implications: List[str]
    raw_data: Optional[Dict[str, Any]] = None


class MondayBIAgent:
    """Business Intelligence Agent for Monday.com data."""
    
    # Column mappings for Deals board
    DEALS_COLUMN_MAPPING = {
        "amount": "Amount",
        "stage": "Stage",
        "sector": "Sector",
        "close_date": "Close Date",
        "probability": "Probability",
        "owner": "Owner",
        "company": "Company",
    }
    
    # Column mappings for Work Orders board
    WORK_ORDERS_COLUMN_MAPPING = {
        "revenue": "Revenue",
        "status": "Status",
        "sector": "Sector",
        "start_date": "Start Date",
        "end_date": "End Date",
        "project_manager": "Project Manager",
        "client": "Client",
    }
    
    def __init__(self, api_token: Optional[str] = None):
        self.client = MondayClient(api_token)
        self.query_parser = QueryParser()
        self.pipeline_analyzer = PipelineAnalyzer()
        self.revenue_analyzer = RevenueAnalyzer()
        self.execution_analyzer = ExecutionAnalyzer()
        self.leadership_analyzer = LeadershipAnalyzer()
        
        # Cached data
        self._deals_board_id: Optional[str] = None
        self._work_orders_board_id: Optional[str] = None
        self._deals_data: List[Dict[str, Any]] = []
        self._work_orders_data: List[Dict[str, Any]] = []
    
    async def _get_board_id(self, board_name: str, board_id: Optional[str] = None) -> Optional[str]:
        """Get board ID - use provided ID first, then try to find by name."""
        # If board ID is provided via config, use it directly
        if board_id:
            return board_id
        
        # Otherwise, look up by name
        board = await self.client.get_board_by_name(board_name)
        return board.get("id") if board else None
    
    async def _load_deals_data(self) -> List[Dict[str, Any]]:
        """Load and normalize deals data from Monday.com."""

        # 1️⃣ If ID already cached, use it
        if not self._deals_board_id:

            # 2️⃣ Try config ID
            if settings.DEALS_BOARD_ID:
                self._deals_board_id = settings.DEALS_BOARD_ID

            # 3️⃣ Try config name
            elif settings.DEALS_BOARD_NAME:
                board = await self.client.get_board_by_name(settings.DEALS_BOARD_NAME)
                if board:
                    self._deals_board_id = board.get("id")

            # 4️⃣ Auto detect
            if not self._deals_board_id:
                boards = await self.client.get_boards()
                for board in boards:
                    name = board.get("name", "").lower()
                    if any(k in name for k in ["deal", "pipeline", "sales"]):
                        self._deals_board_id = board.get("id")
                        break

            print("DEALS BOARD ID:", self._deals_board_id)
            items = await self.client.get_board_items(self._deals_board_id)
            print("DEALS ITEMS COUNT:", len(items))



        if not self._deals_board_id:
            return []

        items = await self.client.get_board_items(self._deals_board_id)
        normalized = transform_monday_items(items, self.DEALS_COLUMN_MAPPING)
        print("SAMPLE DEAL RECORD:", normalized[0] if normalized else "EMPTY")


        return normalized
  

    
    async def _load_work_orders_data(self) -> List[Dict[str, Any]]:
        """Load and normalize work orders data from Monday.com."""

        if not self._work_orders_board_id:

            # 1️⃣ Try config ID
            if settings.WORK_ORDERS_BOARD_ID:
                self._work_orders_board_id = settings.WORK_ORDERS_BOARD_ID

            # 2️⃣ Try config name
            elif settings.WORK_ORDERS_BOARD_NAME:
                board = await self.client.get_board_by_name(settings.WORK_ORDERS_BOARD_NAME)
                if board:
                    self._work_orders_board_id = board.get("id")

            # 3️⃣ Auto detect
            if not self._work_orders_board_id:
                boards = await self.client.get_boards()
                for board in boards:
                    name = board.get("name", "").lower()
                    if any(k in name for k in ["work", "order", "project", "execution"]):
                        self._work_orders_board_id = board.get("id")
                        break

        if not self._work_orders_board_id:
            return []

        items = await self.client.get_board_items(self._work_orders_board_id)
        normalized = transform_monday_items(items, self.WORK_ORDERS_COLUMN_MAPPING)
        print("WORK BOARD ID:", self._work_orders_board_id)
        items = await self.client.get_board_items(self._work_orders_board_id)
        print("WORK ITEMS COUNT:", len(items))


        return normalized

    
    async def answer_query(self, query: str) -> BIResponse:
        """Answer a business intelligence query."""
        # Parse the query
        parsed = self.query_parser.parse(query)
        
        # Check if clarification is needed
        if parsed.clarification_needed:
            return BIResponse(
                executive_summary=parsed.clarification_needed,
                key_metrics={},
                data_quality={"clarification_needed": True},
                implications=["Please provide more details to get accurate insights"]
            )
        
        # Load data based on query type
        deals = []
        work_orders = []
        
        if parsed.query_type in [QueryType.PIPELINE_OVERVIEW, QueryType.REVENUE_FORECAST, QueryType.LEADERSHIP_UPDATE]:
            deals = await self._load_deals_data()
        
        if parsed.query_type in [QueryType.EXECUTION_STATUS, QueryType.REVENUE_FORECAST, QueryType.LEADERSHIP_UPDATE]:
            work_orders = await self._load_work_orders_data()
        
        # Validate data quality
        validator = DataValidator()
        
        if deals:
            deals, deals_quality = validator.validate_records(deals, required_fields=["name"])
        else:
            deals_quality = DataQualityReport(0, 0, {}, {}, 0, ["No deals data available"])
        
        if work_orders:
            work_orders, wo_quality = validator.validate_records(work_orders, required_fields=["name"])
        else:
            wo_quality = DataQualityReport(0, 0, {}, {}, 0, ["No work orders data available"])
        
        # Combine quality reports
        combined_quality = DataQualityReport(
            total_records=deals_quality.total_records + wo_quality.total_records,
            valid_records=deals_quality.valid_records + wo_quality.valid_records,
            missing_values={**deals_quality.missing_values, **wo_quality.missing_values},
            invalid_formats={**deals_quality.invalid_formats, **wo_quality.invalid_formats},
            excluded_records=deals_quality.excluded_records + wo_quality.excluded_records,
            warnings=deals_quality.warnings + wo_quality.warnings
        )
        
        # Generate response based on query type
        if parsed.query_type == QueryType.PIPELINE_OVERVIEW:
            return self._generate_pipeline_response(parsed, deals, combined_quality)
        
        elif parsed.query_type == QueryType.REVENUE_FORECAST:
            return self._generate_revenue_response(parsed, deals, work_orders, combined_quality)
        
        elif parsed.query_type == QueryType.EXECUTION_STATUS:
            return self._generate_execution_response(parsed, work_orders, combined_quality)
        
        elif parsed.query_type == QueryType.LEADERSHIP_UPDATE:
            return self._generate_leadership_response(parsed, deals, work_orders, combined_quality)
        
        else:
            # Custom query - try to provide helpful information
            return self._generate_custom_response(parsed, deals, work_orders, combined_quality)
    
    def _generate_pipeline_response(
        self, 
        parsed: ParsedQuery, 
        deals: List[Dict[str, Any]],
        quality: DataQualityReport
    ) -> BIResponse:
        """Generate response for pipeline overview queries."""
        metrics = self.pipeline_analyzer.analyze(deals, parsed.sector)
        
        # Build executive summary
        if parsed.sector:
            summary = f"The {parsed.sector} sector pipeline contains {metrics.total_deals} deals worth ${metrics.total_pipeline_value:,.0f}."
        else:
            summary = f"Overall pipeline contains {metrics.total_deals} deals worth ${metrics.total_pipeline_value:,.0f}."
        
        if metrics.win_rate:
            summary += f" Current win rate is {metrics.win_rate:.1f}%."
        
        # Key implications
        implications = []
        if metrics.win_rate and metrics.win_rate < 20:
            implications.append("Low win rate suggests need for better qualification")
        if metrics.weighted_pipeline_value < metrics.total_pipeline_value * 0.3:
            implications.append("Many deals in early stages - focus on advancing opportunities")
        if not implications:
            implications.append("Pipeline is progressing well - maintain current sales activities")
        print("DEALS PASSED TO ANALYZER:", len(deals))

        return BIResponse(
            executive_summary=summary,
            key_metrics=metrics.to_dict(),
            data_quality={
                "confidence_score": round(quality.confidence_score, 1),
                "total_records": quality.total_records,
                "valid_records": quality.valid_records,
                "warnings": quality.warnings[:3]
            },
            implications=implications
        )
    
    def _generate_revenue_response(
        self,
        parsed: ParsedQuery,
        deals: List[Dict[str, Any]],
        work_orders: List[Dict[str, Any]],
        quality: DataQualityReport
    ) -> BIResponse:
        """Generate response for revenue forecast queries."""
        # Get pipeline value
        pipeline_metrics = self.pipeline_analyzer.analyze(deals, parsed.sector)
        revenue_metrics = self.revenue_analyzer.analyze(work_orders, parsed.sector)
        
        # Combine for total forecast
        total_forecast = pipeline_metrics.weighted_pipeline_value + revenue_metrics.forecasted_revenue
        
        if parsed.sector:
            summary = f"{parsed.sector} sector revenue forecast: ${total_forecast:,.0f} "
            summary += f"(${revenue_metrics.recognized_revenue:,.0f} recognized, ${total_forecast:,.0f} forecasted)."
        else:
            summary = f"Total revenue forecast: ${total_forecast:,.0f} "
            summary += f"(${revenue_metrics.recognized_revenue:,.0f} recognized, ${total_forecast:,.0f} forecasted)."
        
        implications = [
            f"Weighted pipeline of ${pipeline_metrics.weighted_pipeline_value:,.0f} provides revenue visibility",
            f"Backlog of ${revenue_metrics.forecasted_revenue:,.0f} represents committed work"
        ]
        
        key_metrics = {
            "pipeline_value": pipeline_metrics.total_pipeline_value,
            "weighted_pipeline": pipeline_metrics.weighted_pipeline_value,
            "recognized_revenue": revenue_metrics.recognized_revenue,
            "forecasted_revenue": revenue_metrics.forecasted_revenue,
            "total_forecast": total_forecast,
            "revenue_by_sector": revenue_metrics.revenue_by_sector
        }
        
        return BIResponse(
            executive_summary=summary,
            key_metrics=key_metrics,
            data_quality={
                "confidence_score": round(quality.confidence_score, 1),
                "total_records": quality.total_records,
                "valid_records": quality.valid_records,
                "warnings": quality.warnings[:3]
            },
            implications=implications
        )
    
    def _generate_execution_response(
        self,
        parsed: ParsedQuery,
        work_orders: List[Dict[str, Any]],
        quality: DataQualityReport
    ) -> BIResponse:
        """Generate response for execution status queries."""
        metrics = self.execution_analyzer.analyze(work_orders, parsed.sector)
        
        if parsed.sector:
            summary = f"{parsed.sector} sector execution: {metrics.total_work_orders} work orders, "
        else:
            summary = f"Overall execution: {metrics.total_work_orders} work orders, "
        
        summary += f"{metrics.completed_orders} completed ({metrics.completion_rate:.1f}%), "
        summary += f"{metrics.in_progress_orders} in progress."
        
        implications = []
        if metrics.completion_rate > 80:
            implications.append("Excellent execution efficiency - team is performing well")
        elif metrics.completion_rate > 50:
            implications.append("Good progress - monitor in-progress items for timely delivery")
        else:
            implications.append("Execution needs attention - review resource allocation")
        
        if metrics.backlog_value > 0:
            implications.append(f"${metrics.backlog_value:,.0f} backlog represents delivery commitment")
        
        return BIResponse(
            executive_summary=summary,
            key_metrics=metrics.to_dict(),
            data_quality={
                "confidence_score": round(quality.confidence_score, 1),
                "total_records": quality.total_records,
                "valid_records": quality.valid_records,
                "warnings": quality.warnings[:3]
            },
            implications=implications
        )
    
    def _generate_leadership_response(
        self,
        parsed: ParsedQuery,
        deals: List[Dict[str, Any]],
        work_orders: List[Dict[str, Any]],
        quality: DataQualityReport
    ) -> BIResponse:
        """Generate leadership update response."""
        pipeline_metrics = self.pipeline_analyzer.analyze(deals, parsed.sector)
        revenue_metrics = self.revenue_analyzer.analyze(work_orders, parsed.sector)
        execution_metrics = self.execution_analyzer.analyze(work_orders, parsed.sector)
        
        summary = self.leadership_analyzer.generate_summary(
            pipeline_metrics, revenue_metrics, execution_metrics, quality, parsed.time_range
        )
        
        # Build executive summary
        exec_summary = f"Pipeline health: {summary.pipeline_health}. "
        exec_summary += f"Total pipeline: ${pipeline_metrics.total_pipeline_value:,.0f} across {pipeline_metrics.total_deals} deals. "
        exec_summary += f"Execution: {execution_metrics.completion_rate:.1f}% completion rate."
        
        return BIResponse(
            executive_summary=exec_summary,
            key_metrics=summary.to_dict(),
            data_quality={
                "confidence_score": round(quality.confidence_score, 1),
                "total_records": quality.total_records,
                "valid_records": quality.valid_records,
                "warnings": quality.warnings[:5]
            },
            implications=summary.risks + summary.opportunities
        )
    
    def _generate_custom_response(
        self,
        parsed: ParsedQuery,
        deals: List[Dict[str, Any]],
        work_orders: List[Dict[str, Any]],
        quality: DataQualityReport
    ) -> BIResponse:
        """Generate response for custom queries."""
        # Try to provide helpful information based on available data
        pipeline_metrics = self.pipeline_analyzer.analyze(deals, parsed.sector)
        execution_metrics = self.execution_analyzer.analyze(work_orders, parsed.sector)
        
        summary = "Based on available data: "
        
        if pipeline_metrics.total_deals > 0:
            summary += f"Pipeline has {pipeline_metrics.total_deals} deals worth ${pipeline_metrics.total_pipeline_value:,.0f}. "
        
        if execution_metrics.total_work_orders > 0:
            summary += f"Execution has {execution_metrics.total_work_orders} work orders with {execution_metrics.completion_rate:.1f}% completion."
        
        if not deals and not work_orders:
            summary = "No data available. Please check your Monday.com connection and board configuration."
        
        return BIResponse(
            executive_summary=summary,
            key_metrics={
                "pipeline": pipeline_metrics.to_dict() if deals else None,
                "execution": execution_metrics.to_dict() if work_orders else None
            },
            data_quality={
                "confidence_score": round(quality.confidence_score, 1),
                "total_records": quality.total_records,
                "valid_records": quality.valid_records,
                "warnings": quality.warnings[:3]
            },
            implications=["For more specific insights, try asking about pipeline, revenue, or execution specifically"]
        )


# Singleton instance
bi_agent = MondayBIAgent()