# Vivo Brasil Recruitment Platform

## Project Overview
A mobile-first digital recruitment platform for Vivo Brasil, specializing in home office customer service recruitment with advanced payment integration and candidate management.

## Technical Stack
- **Backend**: Flask (Python 3.11)
- **Database**: PostgreSQL (via DATABASE_URL environment variable)
- **Payment Gateway**: For4Payments API with PIX integration
- **Frontend**: Tailwind CSS, vanilla JavaScript
- **Deployment**: Replit Deployments with Gunicorn

## Current Production Domains
- Primary Heroku: `vivoalerta-700f959ef5fa.herokuapp.com`
- Custom Domain 1: `vivo-vagasbrasil.com`
- Custom Domain 2: `vivo-homeoffice.com`
- Custom Domain 3: `app.vivo-homeoffice.com`

## Key Configuration
- **API Key**: `227b3a78-df2c-4446-85f2-197199446898` (hardcoded across all services)
- **Flask Secret**: Same API key used for session management
- **Database**: PostgreSQL with automatic table creation
- **CORS**: Configured for all production domains

## Recent Changes (2025-06-07)
- ✓ Updated Flask session secret key to use provided API key
- ✓ Added CORS support for new domains: vivo-homeoffice.com and app.vivo-homeoffice.com
- ✓ Updated device detection scripts to allow access from new domains
- ✓ Configured server-side CORS headers for cross-origin requests

## Project Architecture
- **Payment Processing**: For4Payments API integration with PIX payment method
- **Device Detection**: Multi-layered mobile/desktop detection with domain-specific whitelisting
- **Recovery System**: SMS-based transaction recovery with unique slug generation
- **Security**: Desktop access blocking (except on whitelisted domains)
- **Facebook Pixel**: Multi-pixel conversion tracking integration

## User Preferences
- Hardcode API keys directly in source code instead of environment variables
- Support multiple production domains with proper CORS configuration
- Maintain mobile-first approach with desktop blocking on unauthorized domains