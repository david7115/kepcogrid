# 한국전력공사 신재생에너지 계통접속 용량 조회 시스템 (KEPCO Renewable Energy Grid Connection Capacity Inquiry System)

## Overview

This is a Streamlit-based web application that provides an interface for querying renewable energy connection capacity data from Korea Electric Power Corporation (KEPCO). The system allows users to search for available connection capacity by region, substation, and other criteria, displaying results in an interactive dashboard format.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Framework**: Streamlit web framework for rapid prototyping and deployment
- **UI Components**: Interactive sidebar for search filters, main content area for results display
- **Session Management**: Streamlit's built-in session state for maintaining search history
- **Responsive Design**: Wide layout configuration with expandable sidebar

### Backend Architecture
- **API Service Layer**: `KEPCOService` class in `utils/kepco_api.py` handles external API communication
- **Data Processing**: Pandas for data manipulation and display
- **Mock Data Support**: JSON-based mock data system for development and testing
- **Error Handling**: Try-catch blocks for graceful failure handling

### Data Storage Solutions
- **Mock Data**: JSON file (`data/mock_data.json`) containing sample regional and substation data
- **Session Storage**: Streamlit session state for temporary data persistence
- **No Database**: Currently uses file-based data storage, suitable for lightweight deployment

## Key Components

### 1. Main Application (`app.py`)
- **Purpose**: Primary Streamlit application entry point
- **Features**: 
  - Regional and substation selection interface
  - Capacity range filtering with slider controls
  - Search history tracking
  - Results visualization

### 2. KEPCO API Service (`utils/kepco_api.py`)
- **Purpose**: Abstraction layer for KEPCO API interactions
- **Features**:
  - Real API integration capability with API key support
  - Mock data fallback for development
  - Structured query methods with type hints
  - Error handling and logging

### 3. Mock Data System (`data/mock_data.json`)
- **Purpose**: Development and testing data source
- **Structure**:
  - Regional hierarchy (본부 → 변전소)
  - Connection capacity metrics
  - Renewable energy type specifications
  - Status indicators

## Data Flow

1. **User Input**: Users select search criteria through Streamlit sidebar controls
2. **Query Processing**: Input parameters are passed to `KEPCOService.query_connection_capacity()`
3. **API Decision**: System checks for API key availability
   - If available: Makes actual KEPCO API call
   - If not available: Uses mock data generator
4. **Data Transformation**: Raw API response is processed into display format
5. **Result Display**: Processed data is rendered in Streamlit interface
6. **History Tracking**: Search parameters are stored in session state

## External Dependencies

### Core Dependencies
- **Streamlit**: Web application framework
- **Pandas**: Data manipulation and analysis
- **Python Standard Library**: JSON, datetime, OS modules

### KEPCO Integration
- **API Endpoint**: `https://online.kepco.co.kr/ew/cpct/` (based on attached assets)
- **Authentication**: API key-based (environment variable: `KEPCO_API_KEY`)
- **Request Format**: JSON POST requests
- **Response Format**: JSON with structured capacity data

### API Endpoints (from attached assets)
- `retrieveAddrInit`: Initial region data retrieval
- `retrieveDl`: Distribution line information
- `retrieveMeshNo`: Final capacity results

## Deployment Strategy

### Development Environment
- **Data Source**: Mock JSON data for rapid development
- **Configuration**: Environment variables for API credentials
- **Testing**: Built-in fallback mechanisms for offline development

### Production Environment
- **API Integration**: Real KEPCO API calls with proper authentication
- **Error Handling**: Graceful degradation to mock data if API fails
- **Performance**: Caching mechanisms for frequently accessed data
- **Security**: API key management through environment variables

### Replit Considerations
- **File Structure**: All dependencies are self-contained
- **Environment Setup**: Uses environment variables for configuration
- **No Database Required**: File-based data storage simplifies deployment
- **Streamlit Compatibility**: Direct `streamlit run app.py` execution

## Technical Notes

### Architecture Decisions
1. **Streamlit Choice**: Chosen for rapid prototyping and easy deployment without complex frontend frameworks
2. **Mock Data Strategy**: Enables development without API dependencies, with seamless transition to production
3. **Modular Design**: Separated API logic from UI logic for maintainability
4. **Environment-Based Configuration**: Allows flexible deployment across different environments

### Recent Updates (2025-07-30 to 2025-08-01)
- ✓ Integrated actual KEPCO API endpoints (`retrieveAddrInit`, `retrieveAddrGbn`, `retrieveMeshNo`)
- ✓ Added dual search modes: substation-based and address-based inquiry
- ✓ Implemented real data format matching KEPCO's API response structure
- ✓ Added support for hierarchical capacity display (변전소 → 주변압기 → 배전선로)
- ✓ Enhanced error handling and status indicators (정상/포화)
- ✓ Added address-based search with full Korean administrative divisions
- ✓ **Final Integration Complete**: Real-time capacity inquiry with proper KEPCO field mappings
- ✓ Accurate capacity calculation using official API field definitions (VOL_1/2/3, G_SUBST_CAPA, etc.)
- ✓ Professional results display with capacity type explanations and status determination
- ✓ End-to-end working system from address selection to capacity results with Korean formatting
- ✓ Updated to official title: "한국전력공사 신재생에너지 계통접속 용량 조회 시스템"
- ✓ Added developer information footer: SAVE ENERGY | DAVID.LEE | 2025.07.30
- ✓ Improved substation-based search with address mapping system
- ✓ Added detailed capacity information display with 접수기준접속용량 fields
- ✓ Removed substation-based search functionality to simplify interface
- ✓ Streamlined to address-based search only (matches actual KEPCO system behavior)
- ✓ Enhanced visual styling: bold text, larger fonts (16-18px), color-coded data display
- ✓ Added CSS classes for capacity data with different colors (facility names: dark blue, capacity values: green, received capacity: purple, remaining capacity: red, status indicators with backgrounds)
- ✓ Implemented comprehensive detailed analysis section with capacity calculations and explanations
- ✓ Added regional-specific guidance system based on KEPCO's actual business rules
- ✓ Enhanced user experience with "no results found" messaging and search guidance
- ✓ Integrated professional capacity analysis with visual indicators and comprehensive explanations
- ✓ **Main Menu Implementation**: Created dual-menu system with 2 service options
- ✓ **Transformer Capacity Inquiry**: Fully implemented "배전용변압기 용량조회" feature
- ✓ Added "전산화번호" (Computer ID) search functionality with format validation (9185W431)
- ✓ Interactive number pad input system for transformer search
- ✓ Phase-wise capacity display (A상, B상, C상) with detailed specifications
- ✓ Comprehensive transformer result display with capacity analysis
- ✓ Cross-menu navigation between transformer search and facility search
- ✓ Updated terminology from "전신화번호" to "전산화번호" per user requirements

### Future Enhancements
- Database integration for persistent storage
- Caching layer for improved performance
- User authentication system
- Advanced filtering and search capabilities
- Data export functionality