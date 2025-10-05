# News Crawler MVP

A Python-based news aggregator that fetches articles from RSS feeds based on keywords and outputs them in JSONL and CSV formats.

## Features

- **RSS Feed Aggregation**: Fetches news from multiple RSS sources
- **Keyword Filtering**: Filters articles based on search queries
- **Content Extraction**: Extracts full article text using trafilatura and readability
- **Date Filtering**: Optional date range filtering
- **Rate Limiting**: Respects robots.txt and implements rate limiting
- **Multiple Output Formats**: JSONL and CSV output
- **Async Processing**: Concurrent fetching for better performance

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage
```bash
python main.py --q "Nasdaq AI chips" --since 2025-01-01 --limit 50
```

### With Custom RSS Feeds
```bash
python main.py --q "NVIDIA earnings" --feeds "https://www.bing.com/news/search?q={query}&format=rss,https://www.reuters.com/markets/rss"
```

### Command Line Arguments

- `--q, --query` (required): Search query/keywords
- `--since` (optional): Start date in ISO format (YYYY-MM-DD)
- `--limit` (optional): Maximum number of articles (default: 50)
- `--feeds` (optional): Custom RSS feeds, comma-separated

## Output

The crawler generates two output files in the `output/` directory:

- `news.jsonl`: One JSON object per line, suitable for further processing
- `news.csv`: CSV format for easy viewing in spreadsheet applications

## RSS Sources

Default RSS sources are configured in `config/feeds.default.txt`:

- Bing News (query-specific)
- Google News (query-specific)
- Wall Street Journal Markets
- Reuters Markets
- Nasdaq Markets



