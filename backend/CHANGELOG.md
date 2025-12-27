# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-12-28

### Added
- Async/await architecture with httpx for concurrent scraping
- Retry logic with exponential backoff using tenacity
- Pydantic models for type safety and validation
- Comprehensive test suite with pytest (>80% coverage)
- Environment-based configuration with pydantic-settings
- Centralized logging with configurable levels
- Multi-stage Docker builds for smaller images
- GitHub Actions CI/CD pipeline
- Health check endpoint
- Download endpoint for JSON file export
- Comprehensive documentation and README
- Code quality tools (black, ruff) configuration

### Changed
- Migrated from Python 3.9 to Python 3.12
- Replaced synchronous requests with async httpx
- Refactored monolithic scripts into modular architecture
- Upgraded Flask from 2.3.2 to 3.1.0
- Improved HTML parsing with better error handling
- Enhanced data transformation pipeline
- Switched from subprocess to async execution in Flask routes
- Updated Docker configuration with production-ready setup

### Removed
- Old monolithic scripts (scrape3.py, test3.py)
- Hardcoded German comments and variable names
- Unused Node.js dependencies (pandas, puppeteer, xlsx)
- Direct file writing in favor of in-memory processing
- Blocking subprocess calls

### Fixed
- Missing requests dependency in requirements.txt
- Security vulnerabilities in Flask 2.3.2
- Blocking I/O in Flask routes
- Lack of error handling in scraping logic
- No rate limiting causing potential server issues
- Mixed Python/Node.js dependency confusion

### Security
- Updated all dependencies to latest versions
- Fixed Flask security vulnerabilities
- Added proper error handling to prevent information leakage
- Implemented rate limiting and request timeouts

## [1.0.0] - 2023-06-03

### Added
- Initial release
- Basic web scraping for Dominion ships
- Flask API with CORS support
- Docker containerization
- JSON output files