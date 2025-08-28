# Overview

This is a Telegram Mini-App for creating and managing auction-style listings with multiple sale modes. The application allows users to list items for sale using different pricing strategies including fixed price, free giveaways, name-your-price, and traditional auctions. Users authenticate through Telegram's WebApp API and can manage their listings through a mobile-optimized interface that follows Telegram's design guidelines.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Frontend Architecture
- **Framework**: Vanilla JavaScript with Bootstrap 5 for responsive UI components
- **Theme System**: CSS custom properties that adapt to Telegram's theme parameters (light/dark mode)
- **Mobile-First Design**: Touch-optimized interface following Telegram Mini-App guidelines
- **Component Structure**: Modular HTML templates with shared CSS and JavaScript utilities
- **State Management**: Client-side JavaScript manages form state and user interactions

## Backend Architecture
- **Framework**: Flask web application with SQLAlchemy ORM
- **Database**: SQLite for development with PostgreSQL support via environment configuration
- **Authentication**: Telegram WebApp data verification using HMAC-SHA256
- **File Handling**: Local file storage for uploaded images with PIL for image processing
- **API Design**: RESTful endpoints for CRUD operations on listings and user management

## Data Model
- **Users**: Telegram user data (telegram_id, username, names) with creation timestamps
- **Listings**: Items with flexible pricing models, status tracking, and seller relationships
- **Photos**: File references linked to listings with metadata
- **Bids**: Auction functionality with bidder tracking and price history
- **Enums**: Sale modes (fixed_price, free, name_your_price, auction) and listing statuses

## Security & Configuration
- **Environment Variables**: Database URL, Telegram bot token, and session secrets
- **CORS**: Cross-origin resource sharing enabled for WebApp integration
- **File Upload**: Size limits (16MB) with secure filename handling
- **Proxy Support**: Production-ready with ProxyFix middleware for proper headers

# External Dependencies

## Telegram Integration
- **Telegram WebApp API**: User authentication, theme adaptation, haptic feedback
- **Bot Token**: Required for validating WebApp authentication data

## Frontend Libraries
- **Bootstrap 5**: UI components and responsive grid system
- **Feather Icons**: Consistent iconography throughout the interface
- **PIL (Pillow)**: Server-side image processing and optimization

## Database
- **SQLAlchemy**: ORM for database operations with PostgreSQL/SQLite support
- **Flask-SQLAlchemy**: Flask integration for database management

## Development Tools
- **Flask-CORS**: Cross-origin request handling for development
- **Werkzeug**: WSGI utilities and secure file handling