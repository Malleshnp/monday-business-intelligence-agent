# Monday.com Business Intelligence Agent

An AI-powered Business Intelligence agent that answers founder-level queries by integrating with Monday.com boards. Get instant insights on your sales pipeline, revenue forecast, and project execution.



## Features

- **Natural Language Queries**: Ask questions like "How's our pipeline looking?" or "Give me a leadership update"
- **Live Data Integration**: Fetches real-time data from Monday.com GraphQL API
- **Data Resilience**: Handles messy real-world data with missing values and inconsistent formats
- **Business Intelligence**: Computes pipeline metrics, revenue forecasts, and execution status
- **Leadership Updates**: Generates board-ready executive summaries with risks and opportunities
- **Data Quality Transparency**: Reports confidence scores and data quality issues
```
## Architecture

                ┌─────────────────────────┐
                │        Frontend         │
                │  (React + Vite build)   │
                └────────────┬────────────┘
                             │
                             ▼
                ┌─────────────────────────┐
                │        FastAPI API      │
                │      app.main:app       │
                └────────────┬────────────┘
                             │
         ┌───────────────────┼───────────────────┐
         ▼                   ▼                   ▼
  Query Engine         Monday Client       Data Resilience
 (Intent Parsing)     (Board + Items API)   (Normalization)
         │                   │                   │
         ▼                   ▼                   ▼
                 Business Intelligence Analyzers
           (Pipeline | Revenue | Execution | Leadership)
                             │
                             ▼
                     Structured BI Response
```

### Backend Components

- **MondayClient**: GraphQL API integration
- **DataNormalizer**: Handles date, numeric, text, sector, and status normalization
- **QueryParser**: Interprets natural language business queries
- **BI Analyzers**: Pipeline, Revenue, Execution, and Leadership analysis engines
- **BI Agent**: Orchestrates query processing and response generation

## Quick Start

### Prerequisites

- Python 3.9+
- Node.js 18+
- Monday.com API token

### 1. Clone and Setup

```bash
git clone <repository-url>
cd monday-bi-agent
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export MONDAY_API_TOKEN="your_monday_api_token"
export OPENAI_API_KEY="your_openai_key"  # Optional

# Run the server
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend Setup

```bash
cd app

# Install dependencies
npm install

# Set API URL (optional, defaults to localhost:8000)
echo "VITE_API_URL=http://localhost:8000" > .env

# Run development server
npm run dev
```

### 4. Access the Application

Open http://localhost:5173 in your browser

## Monday.com Configuration

### 1. Get Your API Token

1. Log in to Monday.com
2. Go to your profile (avatar) → Admin
3. Click "API" in the left sidebar
4. Copy your API token

### 2. Board Structure

The agent expects two boards:

#### Deals Board (Sales Pipeline)

| Column | Type | Description |
|--------|------|-------------|
| Item Name | Text | Deal/Company name |
| Amount | Numbers | Deal value |
| Stage | Status | Lead, Qualified, Proposal, Negotiation, Closed Won, Closed Lost |
| Sector | Dropdown | Energy, Technology, Healthcare, Finance, etc. |
| Close Date | Date | Expected close date |
| Owner | People | Sales owner |

#### Work Orders Board (Project Execution)

| Column | Type | Description |
|--------|------|-------------|
| Item Name | Text | Project name |
| Revenue | Numbers | Project revenue |
| Status | Status | Planning, In Progress, Completed, On Hold |
| Sector | Dropdown | Energy, Technology, Healthcare, Finance, etc. |
| Start Date | Date | Project start |
| End Date | Date | Project end |
| Project Manager | People | Project owner |

### 3. Configure Board Names

Set environment variables if your boards have different names:

```bash
export DEALS_BOARD_NAME="Your Deals Board Name"
export WORK_ORDERS_BOARD_NAME="Your Work Orders Board Name"
```

## Usage Examples

### Pipeline Queries

```
"How's our pipeline looking?"
"What's the pipeline for energy sector?"
"Show me deals in negotiation"
"What's our win rate?"
```

### Revenue Queries

```
"What's our revenue forecast?"
"Show me recognized revenue by sector"
"What's our YTD revenue?"
```

### Execution Queries

```
"Show me execution status"
"How many work orders are in progress?"
"What's our completion rate?"
```

### Leadership Updates

```
"Give me a leadership update"
"Board report for this quarter"
"Executive summary"
```

## API Endpoints

### POST /api/query

Process a business intelligence query.

**Request:**
```json
{
  "query": "How's our pipeline looking?",
  "api_token": "optional_override_token"
}
```

**Response:**
```json
{
  "executive_summary": "Pipeline contains 25 deals worth $2.5M...",
  "key_metrics": {
    "total_deals": 25,
    "total_pipeline_value": 2500000,
    "win_rate": 35.5,
    ...
  },
  "data_quality": {
    "confidence_score": 85.5,
    "total_records": 30,
    "valid_records": 25,
    "warnings": []
  },
  "implications": [
    "Pipeline is progressing well...",
    "Focus on advancing opportunities..."
  ]
}
```

### GET /api/boards

List all accessible Monday.com boards.

### GET /api/config

Get current configuration (without sensitive data).

### POST /api/leadership-update

Generate a comprehensive leadership update.

## Data Quality

The agent handles common data quality issues:

- **Missing values**: Tracked and reported, never silently filled
- **Date formats**: Handles 10+ formats (ISO, US, EU, text-based)
- **Currency values**: Strips symbols, extracts numeric values
- **Sector names**: Normalizes variations to standard categories
- **Status/Stage**: Maps variations to consistent pipeline stages

Every response includes a confidence score and data quality warnings.

## Development

### Project Structure

skylark-monday-bi-agent/
│
├── app/
│   ├── main.py
│   ├── core/
│   │   └── config.py
│   ├── services/
│   │   ├── bi_agent.py
│   │   ├── monday_client.py
│   │   ├── data_resilience.py
│   │   ├── query_engine.py
│   │   └── bi_analyzer.py
│   └── __init__.py
│
├── static/                 # Built frontend (Vite dist)
│   ├── index.html
│   └── assets/
│       ├── index-xxxx.js
│       └── index-xxxx.css
│
├── requirements.txt
├── README.md
├── .gitignore
└── LICENSE (optional)


### Running Tests

```bash
cd backend
pytest
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MONDAY_API_TOKEN` | Monday.com API token | Required |
| `MONDAY_API_URL` | Monday.com GraphQL endpoint | `https://api.monday.com/v2` |
| `DEALS_BOARD_NAME` | Name of deals board | `Deals` |
| `WORK_ORDERS_BOARD_NAME` | Name of work orders board | `Work Orders` |
| `OPENAI_API_KEY` | OpenAI API key (optional) | None |
| `DEBUG` | Enable debug mode | `False` |

## Deployment

### Backend (Railway/Render/Heroku)

1. Create a new project
2. Connect your repository
3. Set environment variables
4. Deploy

### Frontend (Vercel/Netlify)

1. Connect your repository
2. Set build command: `npm run build`
3. Set output directory: `dist`
4. Set environment variable: `VITE_API_URL=<your_backend_url>`
5. Deploy

## Troubleshooting

### "Monday.com API token required"

- Set your API token in the Settings dialog (gear icon)
- Or set the `MONDAY_API_TOKEN` environment variable

### "No data available"

- Verify board names match your Monday.com boards
- Check that boards have the expected column structure
- Ensure API token has access to the boards

### "Data quality issues"

- Review warnings in the response
- Check for missing values in required columns
- Verify date and numeric formats

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For issues and questions:
- Open a GitHub issue
- Contact: support@example.com

---

Built with ❤️ for founders who need quick, accurate business insights.
