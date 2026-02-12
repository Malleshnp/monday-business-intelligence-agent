# Decision Log: Monday.com Business Intelligence Agent

## Project Overview

Built an AI-powered Business Intelligence agent that answers founder-level queries by integrating with Monday.com boards (Deals and Work Orders). The agent handles messy real-world data, interprets natural language questions, and provides actionable insights.

---

## Key Architectural Decisions

### 1. Technology Stack Selection

**Decision:** Python FastAPI backend + React TypeScript frontend

**Rationale:**
- FastAPI provides async/await support critical for GraphQL API calls to Monday.com
- Python's data processing ecosystem (pandas) ideal for BI calculations
- React with TypeScript ensures type safety for complex data structures
- Tailwind CSS + shadcn/ui provides rapid, consistent UI development

**Trade-offs:**
- Two separate services to deploy vs. a monolithic approach
- Benefits: Scalability, separation of concerns, team independence

### 2. Monday.com Integration Approach

**Decision:** Direct GraphQL API integration (not MCP)

**Rationale:**
- GraphQL provides precise data fetching - request only needed fields
- No additional abstraction layer reduces complexity
- Full control over query construction and error handling
- Monday.com's GraphQL API is mature and well-documented

**Trade-offs:**
- Must handle pagination and rate limiting manually
- Benefits: Predictable behavior, easier debugging

### 3. Data Resilience Strategy

**Decision:** Multi-layer normalization with explicit quality tracking

**Implementation:**
- `DataNormalizer` class handles date, numeric, text, sector, and status normalization
- `DataValidator` tracks missing values, invalid formats, excluded records
- Every query returns a `DataQualityReport` with confidence score

**Rationale:**
- Real-world data is messy - dates in multiple formats, inconsistent sector names
- Explicit quality tracking builds user trust
- Never silently drop data - always report issues

**Example Normalizations:**
- Dates: Handles 10+ formats (ISO, US, EU, text-based)
- Currency: Strips symbols, extracts numeric values
- Sectors: Maps variations ("tech", "software", "IT") to standard categories
- Status: Normalizes stage names to consistent pipeline stages

### 4. Query Understanding Engine

**Decision:** Rule-based parser with confidence scoring (not LLM-based)

**Rationale:**
- Deterministic behavior for business-critical queries
- Faster execution (no external API call for parsing)
- Easier to debug and extend
- Confidence scoring identifies when clarification is needed

**Query Types Detected:**
- Pipeline Overview (keywords: pipeline, deals, sales, forecast)
- Revenue Forecast (keywords: revenue, income, earnings, value)
- Execution Status (keywords: work order, project, delivery)
- Leadership Update (keywords: update, summary, report, KPI)

**Time Range Detection:**
- this quarter, next quarter, this year, last 30/90 days
- Falls back to "all time" if not specified

### 5. Business Intelligence Calculations

**Decision:** Implement domain-specific analyzers

**Components:**
- `PipelineAnalyzer`: Stage distribution, conversion rates, win rates, weighted pipeline
- `RevenueAnalyzer`: Recognized vs forecasted revenue, sector breakdown
- `ExecutionAnalyzer`: Completion rates, backlog value, status distribution
- `LeadershipAnalyzer`: Generates executive summaries with risks/opportunities

**Pipeline Weighting:**
- Lead: 10%, Qualified: 25%, Proposal: 50%, Negotiation: 75%, Closed Won: 100%
- Provides realistic forecast vs. raw pipeline value

### 6. Leadership Updates Interpretation

**Interpretation:** Board-ready executive summaries that tell a story, not just raw numbers

**Implementation:**
- Pipeline health assessment (Strong/Healthy/Needs Attention)
- Key highlights (top metrics in narrative form)
- Risk identification (low win rate, high on-hold orders)
- Opportunity highlighting (strong sectors, late-stage deals)

**Rationale:**
- Founders need actionable insights, not data dumps
- Risks and opportunities frame the narrative for decision-making

---

## Data Quality Handling

### Approach to Missing/Inconsistent Data

1. **Never fabricate data** - If a deal has no amount, it's excluded from value calculations
2. **Track everything** - Every missing value is counted and reported
3. **Graceful degradation** - Partial metrics computed from available data
4. **User transparency** - Confidence score and warnings in every response

### Example Data Quality Report:
```json
{
  "confidence_score": 78.5,
  "total_records": 100,
  "valid_records": 78,
  "warnings": [
    "22 records missing 'amount' field",
    "5 records with invalid date format"
  ]
}
```

---

## Error Handling Strategy

### API Failures
- Monday.com API errors return meaningful messages to user
- Connection issues trigger retry logic with exponential backoff
- Token validation on startup

### Data Processing Errors
- Individual record failures don't crash batch processing
- Invalid values logged but don't stop analysis
- Empty results handled gracefully with informative messages

---

## Security Considerations

1. **API Token Handling**
   - Token stored in localStorage (frontend) for user convenience
   - Can be overridden via environment variable (backend)
   - Never logged or exposed in error messages

2. **CORS Configuration**
   - Configurable allowed origins
   - Defaults to permissive for development

---

## What I'd Do Differently with More Time

### 1. Enhanced Query Understanding
- Implement LLM-based parsing as fallback for complex queries
- Add query history and learning from corrections
- Support for comparative queries ("vs last quarter")

### 2. Advanced Analytics
- Trend analysis with time-series data
- Predictive forecasting using historical patterns
- Anomaly detection for unusual pipeline changes

### 3. Caching Layer
- Redis cache for frequently accessed board data
- Cache invalidation on Monday.com webhooks
- Reduced API calls and faster response times

### 4. Visualization
- Embedded charts (Recharts or Chart.js)
- Pipeline funnel visualization
- Revenue trend graphs

### 5. User Experience
- Natural language clarifications when query is ambiguous
- Suggested follow-up questions
- Export capabilities (PDF reports, CSV downloads)

### 6. Testing
- Comprehensive unit tests for data normalizers
- Integration tests with Monday.com sandbox
- Load testing for concurrent users

---

## Deployment Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   React Frontend │────▶│  FastAPI Backend │────▶│  Monday.com    │
│   (Vercel)       │     │  (Railway/Render)│     │  GraphQL API   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌─────────────────┐
                        │  Data Processing │
                        │  - Normalization │
                        │  - Validation    │
                        │  - Analysis      │
                        └─────────────────┘
```

---

## Performance Considerations

1. **API Pagination**: Monday.com returns max 500 items per call - implement pagination for large boards
2. **Async Processing**: All API calls are async to prevent blocking
3. **Selective Loading**: Only fetch boards needed for query type
4. **Response Time Target**: < 3 seconds for typical queries

---

## Lessons Learned

1. **Data quality is the hardest problem** - Real-world data requires extensive normalization
2. **Explicit > Implicit** - Users prefer knowing about data issues over silent fixes
3. **Confidence scoring builds trust** - Users appreciate knowing reliability of insights
4. **Founders want narratives** - Numbers without context are less valuable than stories with numbers

---

## Conclusion

The Monday.com BI Agent successfully translates vague founder questions into accurate, trustworthy business insights while maintaining strict adherence to Monday.com as the single source of truth. The architecture prioritizes data quality transparency, graceful handling of messy data, and actionable insights over raw metrics.