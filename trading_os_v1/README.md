# My Trading OS v1

## Project Overview
A comprehensive trading system combining risk management, technical analysis, and fundamental principles. This version includes:

## Core Components
- **Risk Engine**: 52 principles (42 direct implementations, 10 configurable)
- **Technical Engine**: 18 principles (15 direct, 3 visual/numeric conversion)
- **Fundamental Engine**: 4 principles (all direct)

## Documentation
- [Engine Mapping](docs/engine-mapping/principles.csv): Detailed principle categorization
- [Architecture Overview](docs/architecture-overview.md): System design summary

## Development
- **Backend**: Python-based with REST API endpoints
- **Frontend**: Node.js server with HTML interface
- **Testing**: Comprehensive unit and integration tests in `tests/` directory

## Setup
1. Install dependencies: `pip install -r requirements.txt`
2. Configure risk parameters in `config/rule_mapping.json`
3. Run backend: `python trading_os_v1/backend/main.py`
4. Access UI: `http://localhost:5000`

## Contributions
- Update principles.csv with new module extractions
- Enhance technical engine numeric rule conversions
- Expand fundamental analysis modules