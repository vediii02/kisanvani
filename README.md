# Kisan Vani AI - Agricultural Voice Advisory System

An intelligent voice-based agricultural advisory platform designed to help Indian farmers get real-time advice about crops, pests, diseases, and farming practices.

## 🌾 Features

### Core Functionality
- **Voice-based Advisory**: Farmers can call and get agricultural advice in Hindi
- **Multi-tenant Architecture**: Organisation → Company → User hierarchy
- **Role-based Access**: Super Admin, Organisation Admin, Company Admin roles
- **Knowledge Base**: Agricultural information management system
- **Real-time Processing**: Speech-to-text and text-to-speech capabilities

### Frontend Features
- **Modern React UI**: Built with React, TailwindCSS, and shadcn/ui
- **Role-based Dashboards**: Different interfaces for each user type
- **Company Profile Management**: Editable company information and legal details
- **Pending Approvals**: Workflow for user registration approvals
- **Responsive Design**: Works on desktop and mobile devices

### Backend Features
- **FastAPI**: Modern async Python web framework
- **MySQL Database**: Reliable data storage with SQLAlchemy ORM
- **Authentication**: JWT-based secure authentication
- **API Documentation**: Auto-generated OpenAPI/Swagger docs
- **Real-time Pipeline**: Event-driven streaming voice pipeline consisting of independent nodes (STT, LLM, TTS, Voice Processing)
- **External Integration**: Exotel integration for multi-tenant phone handling

## 🏗️ Architecture

### Multi-Tenant System
```
Super Admin
├── Organisations
    ├── Organisation Admin
    ├── Companies
        ├── Company Admin
        └── Operators/Products
```

### Technology Stack

#### Frontend
- **React 19** - Modern UI framework
- **TailwindCSS** - Utility-first CSS framework
- **shadcn/ui** - Pre-built React components
- **React Router** - Client-side routing
- **Axios** - HTTP client for API calls

#### Backend
- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - Python ORM for database operations
- **MySQL 8.0** - Primary database
- **Redis** - Caching and session management
- **Qdrant** - Vector database for future RAG implementation
- **JWT** - Authentication tokens
- **Alembic** - Database migrations

- **LLMs & GenAI**: Sarvam AI tools and Groq used for low-latency streaming TTS, LLM responses
- **Docker & Docker Compose** - Container orchestration alongside PGVector for vector embeddings

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Git

### Installation
```bash
# Clone the repository
git clone <repository-url>
cd voice-advisory

# Start all services
docker-compose up -d --build

# Access the application
# Frontend: http://localhost:3001
# Backend API: http://localhost:8001
# PostgreSQL: Exposed on port 5434
# PGAdmin: http://localhost:8081
```

### Environment Variables
Create a `.env` file in the root directory:
```env
# Database
MYSQL_ROOT_PASSWORD=rootpassword
MYSQL_DATABASE=kisanvani_db
MYSQL_USER=kisanvani
MYSQL_PASSWORD=kisanvani_password

# API Keys (Optional)
GOOGLE_TTS_API_KEY=your_google_tts_key
GEMINI_API_KEY=your_gemini_key
EMERGENT_LLM_KEY=your_openai_key
GROQ_API_KEY=your_groq_key

# JWT
SECRET_KEY=your_jwt_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## 📱 User Roles & Permissions

### Super Admin
- Manage all organisations
- View system statistics
- Manage platform settings
- Access all user data

### Organisation Admin
- Manage companies under their organisation
- Approve/reject company user registrations
- View organisation-specific analytics
- Manage phone numbers and settings

### Company Admin
- Manage company profile and legal information
- Manage products and brands
- View company-specific analytics
- Manage operators (if implemented)

## 🔗 API Endpoints

### Authentication
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `GET /api/auth/me` - Get current user info

### Organisation Management
- `GET /api/organisations` - List organisations (Super Admin)
- `POST /api/organisations` - Create organisation
- `GET /api/organisations/{id}` - Get organisation details
- `PUT /api/organisations/{id}` - Update organisation
- `DELETE /api/organisations/{id}` - Delete organisation

### Company Management
- `GET /api/company/profile` - Get company profile
- `PUT /api/company/profile` - Update company profile
- `GET /api/admin/companies` - List companies (Admin/Org)

### User Management
- `GET /api/superadmin/pending-approvals` - Pending org approvals
- `GET /api/organisation/pending-approvals` - Pending company approvals
- `POST /api/superadmin/approve-user/{id}` - Approve user
- `POST /api/superadmin/reject-user/{id}` - Reject user

### Voice & Advisory
- `POST /api/call-flow/incoming` - Handle incoming calls
- `POST /api/kb/query` - Query knowledge base
- `GET /api/call-flow/audio/{filename}` - Get generated audio

## 🗄️ Database Schema

### Key Tables
- **users** - User accounts and authentication
- **organisations** - Organisation details (email, name, status)
- **companies** - Company profiles with legal information
- **call_sessions** - Call tracking and analytics
- **kb_entries** - Knowledge base articles
- **advisories** - Generated agricultural advice
- **products** - Product catalog
- **brands** - Brand management

## 🎯 Key Features Implementation

### Company Profile Management
- Editable company information
- Legal details (GST, Registration numbers)
- Address and contact information
- Real-time updates with validation

### Pending Approvals Workflow
- Organisation registration requires Super Admin approval
- Company user registration requires Organisation Admin approval
- Email notifications and status tracking

### Voice Call Processing
- Speech-to-text conversion
- Agricultural query analysis
- AI-powered advisory generation
- Text-to-speech response
- Call session logging

### Streaming AI Architecture (Active)
- 6-Node deterministic state machine pipeline for rapid speech turn-taking
- Configured dynamic models dynamically driven by organisation profile
- Real-time chunking mapping text streams to LLM content
- Sarvam AI and Groq optimized node instances

### Provider Integration (Exotel)
- Robust mapping for inbound/outbound IVR processes
- Connect numbers directly to corresponding brands/orgs

## 🔧 Development

### Running Tests
```bash
# Backend tests
docker-compose exec backend python -m pytest

# Frontend tests
cd frontend && npm test
```

### Database Migrations
```bash
# Create new migration
docker-compose exec backend alembic revision --autogenerate -m "description"

# Apply migrations
docker-compose exec backend alembic upgrade head
```

### Adding New Advisory Responses
Edit `backend/services/mock_advisory_service.py`:
```python
# Add new entries to wheat_kb dictionary
"new_problem_keyword": {
    "advisory": "Your agricultural advice here",
    "keywords": ["keyword1", "keyword2"],
    "confidence": 0.85
}
```

## 📊 Monitoring & Analytics

### Available Metrics
- Call volume and duration
- User registration and approval rates
- Advisory confidence scores
- Geographic distribution (if implemented)
- Query pattern analysis

### Logs
- Application logs: `docker-compose logs backend`
- Database logs: `docker-compose logs mysql`
- Frontend logs: Browser console

## 🔒 Security

### Authentication
- JWT-based authentication
- Role-based access control
- Password hashing with bcrypt
- Session management

### Data Protection
- Input validation and sanitization
- SQL injection prevention
- CORS configuration
- Environment variable management

## 🚀 Deployment

### Production Considerations
- Use HTTPS/SSL certificates
- Configure proper domain names
- Set up reverse proxy (Nginx)
- Configure backup strategies
- Monitor resource usage

### Environment Configuration
- Development: `docker-compose.yml`
- Production: Modify with production values
- Database: Use managed MySQL service
- API Keys: Store in secure environment

## 🤝 Contributing

### Code Structure
```
voice-advisory/
├── backend/
│   ├── api/routes/          # API endpoints
│   ├── core/               # Core functionality
│   ├── db/models/          # Database models
│   ├── services/            # Business logic
│   └── alembic/            # Database migrations
├── frontend/
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── pages/          # Page components
│   │   ├── contexts/       # React contexts
│   │   └── api/            # API client
│   └── public/             # Static assets
└── docker-compose.yml          # Service orchestration
```

### Development Workflow
1. Fork the repository
2. Create feature branch
3. Make changes
4. Test thoroughly
5. Submit pull request

## 📞 Support

### Common Issues
- **Backend not starting**: Check environment variables and database connection
- **Frontend errors**: Verify API endpoints and CORS settings
- **Audio issues**: Check TTS service configuration
- **Database errors**: Run migrations and verify schema

### Getting Help
- Check API documentation at `/docs`
- Review application logs
- Verify database connectivity
- Test with sample data

## 📈 Future Enhancements

### Planned Features
- [ ] Real RAG implementation with vector database
- [ ] Multi-language support (English, regional languages)
- [ ] Mobile app development
- [ ] Advanced analytics dashboard
- [ ] Integration with agricultural sensors
- [ ] WhatsApp and SMS integration
- [ ] Weather API integration
- [ ] Crop price information

### Technical Improvements
- [ ] Load testing and optimization
- [ ] Caching strategy implementation
- [ ] API rate limiting
- [ ] Automated testing pipeline
- [ ] Container security scanning

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👥 Team

Agricultural technology platform built for Indian farmers with modern AI and voice technology capabilities.

---

**Last Updated**: February 2026
**Version**: 1.0.0
