# Multi-Agent AI Tutor

An intelligent tutoring system that uses multiple specialized AI agents to provide personalized learning experiences in various subjects.

## Features

- Multi-agent architecture with specialized tutors for different subjects
- Real-time chat interface
- Session management and context preservation
- Powered by Google's Gemini AI
- Modern React frontend
- FastAPI backend

## Tech Stack

- **Frontend**: React, Material-UI
- **Backend**: FastAPI, Python
- **AI**: Google Gemini
- **Session Management**: Redis
- **Deployment**: Vercel

## Setup Instructions

### Prerequisites

- Python 3.8+
- Node.js 14+
- Redis
- Google Gemini API Key

### Backend Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the root directory:
```
GEMINI_API_KEY=your_api_key_here
ENVIRONMENT=development
```

4. Start the backend server:
```bash
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Create a `.env` file in the frontend directory:
```
REACT_APP_API_URL=http://localhost:8000
```

4. Start the development server:
```bash
npm start
```

## Project Structure

```
MultiAgentTutor/
├── app/                    # Backend application
│   ├── agents/            # AI agent implementations
│   ├── utils/             # Utility functions
│   └── main.py            # FastAPI application
├── frontend/              # React frontend
│   ├── src/              # Source files
│   └── public/           # Static files
├── tests/                # Test files
├── requirements.txt      # Python dependencies
└── README.md            # Project documentation
```

## API Documentation

Once the backend is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License

## Contact

Your Name - your.email@example.com
