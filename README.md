# Intelligent Study Content Recommendation System

A Python-based system that analyzes user browsing behavior from a PostgreSQL database and recommends high-quality educational content. The system processes browsing session data captured by a Chrome extension, identifies study patterns and frequently searched topics, then uses web scraping to discover relevant blogs and research papers from professional sources.

## Features

- **Pattern Analysis**: Identifies study patterns from browsing sessions
- **Topic Extraction**: Extracts and ranks frequently searched study topics
- **Content Discovery**: Scrapes blogs and research papers using ZenRows API
- **Quality Filtering**: Filters content by engagement metrics and source trustworthiness
- **Professional Source Prioritization**: Prioritizes content from industry professionals

## Project Structure

```
study-content-recommender/
├── src/
│   ├── data/           # Database connector, simulator, and data models
│   ├── analysis/       # Pattern analyzer and topic extractor
│   ├── scraping/       # Content scraper and ZenRows client
│   ├── filtering/      # Quality filter and professional evaluator
│   ├── output/         # Recommendation generator and formatter
│   └── utils/          # Logger and configuration
├── tests/              # Test suite
├── requirements.txt    # Python dependencies
├── .env.example        # Example environment configuration
└── README.md          # This file
```

## Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and configure your environment variables:
   ```bash
   cp .env.example .env
   ```
4. Update `.env` with your PostgreSQL and ZenRows API credentials

## Configuration

See `.env.example` for all available configuration options.

## Usage

(To be implemented in subsequent tasks)

## Testing

Run tests with pytest:
```bash
pytest tests/
```

Run property-based tests:
```bash
pytest tests/property/
```

## License

(To be determined)
