# DeepResearch UI - Streamlit Application

A comprehensive Streamlit-based user interface for the DeepResearch document search platform with Google OAuth authentication, topic management, and intelligent search capabilities.

## 🏗️ Architecture

The application is structured as a multi-page Streamlit app with the following components:

```
UIV2/
├── app.py                          # Main entry point with authentication
├── pages/
│   ├── 1_🔍_Search.py             # Document search interface
│   ├── 2_📁_Topics.py             # Topic & document management
│   └── 3_💬_Chat.py               # Chat placeholder (coming soon)
├── utils/
│   ├── api_client.py              # API communication layer
│   ├── auth.py                    # OAuth & session management
│   └── validators.py              # Input validation utilities
├── components/
│   └── (UI components - extensible)
├── requirements.txt                # Python dependencies
├── Dockerfile                      # Docker container definition
├── docker-compose.yml              # Docker Compose configuration
└── .env                           # Environment variables (create from .env.example)
```

## 🚀 Features

### Authentication
- **Google OAuth 2.0** with PKCE flow for secure authentication
- Automatic user onboarding with username selection
- JWT token management with secure cookie storage
- Session persistence across page reloads

### Search Page
- **Advanced search** across multiple topics/indices
- **Topic selection** (system topics and user topics)
- **Optional filters**: minimum score, max results
- **Search result display** with relevance scores and snippets
- **Document download** directly from search results
- Query expansion display

### Topics Management Page
- **Create/Delete topics** (user topics only)
- **View topic details** with dedicated interface
- **Document management**:
  - Upload documents (PDF, PPTX, DOCX)
  - View document status (pending/success)
  - Download documents
  - Delete documents
  - Real-time status refresh
- **User access control**:
  - View users with access to topics
  - Add users by username (reader/owner roles)
  - Remove users from topics
  - Role-based permissions

### Chat Page
- Placeholder for future AI agent integration
- Preview of upcoming chat interface

## 📋 Prerequisites

- Docker and Docker Compose
- Google Cloud Console project with OAuth 2.0 credentials
- Access to Kong gateway (running on test_network)
- Backend services (auth, load, search) running

## ⚙️ Configuration

### 1. Create Environment File

Copy the example environment file and configure it:

```bash
cp .env.example .env
```

### 2. Configure Environment Variables

Edit `.env` file with your configuration:

```env
# Kong Gateway Configuration
GATEWAY_URL=http://kong:8015

# Google OAuth Configuration (from Google Cloud Console)
GOOGLE_CLIENT_ID=your_actual_client_id
GOOGLE_CLIENT_SECRET=your_actual_client_secret
REDIRECT_URI=http://localhost:8501

# Logging Configuration
LOG_LEVEL=INFO

# Cookie Encryption (Generate a secure random key!)
COOKIE_PASSWORD=your_secure_random_key_here

# Streamlit Configuration
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
```

### 3. Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable **Google+ API**
4. Create OAuth 2.0 credentials:
   - Application type: Web application
   - Authorized redirect URIs: `http://localhost:8501` (or your production URL)
5. Copy Client ID and Client Secret to `.env` file

### 4. Generate Cookie Password

Generate a secure random key for cookie encryption:

```python
import secrets
print(secrets.token_urlsafe(32))
```

Use the output as your `COOKIE_PASSWORD`.

## 🐳 Docker Deployment

### Build and Run

```bash
# Build the Docker image
docker-compose build

# Start the service
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the service
docker-compose down
```

The UI will be available at `http://localhost:8501`

### Network Requirements

The service connects to the `test_network` Docker network where Kong gateway and backend services are running.

## 🔧 Development Setup

### Local Development (without Docker)

1. Install Python 3.11+
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create and configure `.env` file
4. Run the application:

```bash
streamlit run app.py
```

## 📚 API Integration

The UI communicates with backend services through Kong gateway:

### Endpoints Used

**Auth Service** (`/auth/*`):
- `POST /auth/oauth/google` - OAuth callback
- `POST /auth/onboarding/username` - Set username

**Load Service** (`/topics/*`, `/documents/*`):
- `GET /topics/editable` - Get user's topics
- `GET /topics/readable` - Get searchable topics
- `POST /topics` - Create topic
- `DELETE /topics/{id}` - Delete topic
- `GET /topics/{id}/documents` - List documents
- `GET /topics/{id}/users` - List users with access
- `POST /topics/{id}/users` - Add user to topic
- `DELETE /topics/{id}/users/{user_id}` - Remove user
- `POST /documents/upload` - Upload document
- `DELETE /documents/{id}` - Delete document
- `GET /documents/{id}/status` - Get document status
- `GET /documents/{id}/download` - Download document

**Search Service** (`/search`):
- `POST /search` - Perform search

## 🔒 Security Features

- **PKCE OAuth Flow**: Enhanced security for OAuth
- **JWT Authentication**: Secure token-based auth
- **Encrypted Cookies**: Session data protection
- **CSRF Protection**: State parameter validation
- **Input Validation**: Comprehensive validation for all inputs
- **Secure File Handling**: File type and size validation
- **Role-Based Access**: Topic-level permissions

## 📝 Logging

Application logs include:
- Authentication events
- API requests and responses
- Error tracking
- User actions

Log level can be configured via `LOG_LEVEL` environment variable:
- `DEBUG` - Detailed debugging information
- `INFO` - General informational messages (default)
- `WARNING` - Warning messages
- `ERROR` - Error messages only

## 🐛 Troubleshooting

### Common Issues

**OAuth Redirect Error**:
- Ensure `REDIRECT_URI` in `.env` matches Google Cloud Console configuration
- Check that redirect URI includes the correct protocol (http/https)

**Cannot Connect to Gateway**:
- Verify Kong gateway is running: `docker ps | grep kong`
- Check that UI container is on `test_network`: `docker network inspect test_network`
- Verify `GATEWAY_URL` is correct

**Cookie Manager Not Ready**:
- This is normal on first page load
- Wait for cookie manager initialization
- Refresh if issue persists

**Session Expired Errors**:
- JWT token may have expired
- Click logout and login again
- Check backend JWT configuration

## 🎨 UI Customization

The application uses Streamlit's built-in theming. You can customize by creating `.streamlit/config.toml`:

```toml
[theme]
primaryColor = "#1f77b4"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
font = "sans serif"
```

## 📈 Future Enhancements

- ✅ Google OAuth authentication
- ✅ Topic management
- ✅ Document upload/download
- ✅ User access control
- ✅ Advanced search
- 🔄 Chat with AI agent (in progress)
- 🔜 Document preview
- 🔜 Batch operations
- 🔜 Advanced analytics
- 🔜 Export functionality

## 📄 License

This project is part of the DeepResearch platform.

## 👥 Support

For issues and questions:
1. Check the troubleshooting section
2. Review application logs: `docker-compose logs -f`
3. Contact the development team

---

**Built with ❤️ using Streamlit**
