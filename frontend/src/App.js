import React, { useState, useEffect, useRef } from 'react';
import { 
  Container, 
  Paper, 
  TextField, 
  Button, 
  Typography, 
  Box,
  CircularProgress,
  List,
  ListItem,
  ListItemText,
  Divider,
  Alert,
  Snackbar
} from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import axios from 'axios';

const API_URL = (process.env.REACT_APP_API_URL || 'http://localhost:8000').replace(/\/$/, '');
console.log('API URL:', API_URL);

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [error, setError] = useState(null);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage = input;
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setLoading(true);
    setError(null);

    try {
      console.log('Making request to:', `${API_URL}/ask`);
      const response = await axios.post(`${API_URL}/ask`, {
        query: userMessage,
        session_id: sessionId
      }, {
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        }
      });

      console.log('Response received:', response.data);

      if (response.data.session_id) {
        setSessionId(response.data.session_id);
      }

      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: response.data.answer,
        agent: response.data.agent_used
      }]);
    } catch (error) {
      console.error('Full error object:', error);
      let errorMessage = 'Sorry, there was an error processing your request.';
      
      if (error.response) {
        console.error('Error response:', error.response);
        errorMessage = error.response.data.error || errorMessage;
        if (error.response.data.details) {
          errorMessage += ` Details: ${JSON.stringify(error.response.data.details)}`;
        }
      } else if (error.request) {
        console.error('No response received:', error.request);
        errorMessage = 'Unable to connect to the server. Please check if the backend is running.';
      } else {
        console.error('Error setting up request:', error.message);
      }
      
      setError(errorMessage);
      setMessages(prev => [...prev, { 
        role: 'error', 
        content: errorMessage
      }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="md" sx={{ height: '100vh', py: 4 }}>
      <Paper elevation={3} sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
        <Box sx={{ p: 2, bgcolor: 'primary.main', color: 'white' }}>
          <Typography variant="h5" component="h1">
            AI Tutor
          </Typography>
        </Box>
        
        <List sx={{ 
          flex: 1, 
          overflow: 'auto', 
          p: 2,
          bgcolor: 'background.default'
        }}>
          {messages.map((message, index) => (
            <React.Fragment key={index}>
              <ListItem 
                sx={{ 
                  justifyContent: message.role === 'user' ? 'flex-end' : 'flex-start',
                  mb: 1
                }}
              >
                <Paper 
                  elevation={1} 
                  sx={{ 
                    p: 2, 
                    maxWidth: '70%',
                    bgcolor: message.role === 'user' ? 'primary.light' : 
                             message.role === 'error' ? 'error.light' : 
                             'secondary.light',
                    color: message.role === 'user' ? 'white' : 'text.primary'
                  }}
                >
                  <ListItemText 
                    primary={message.content}
                    secondary={message.agent && `Answered by: ${message.agent}`}
                  />
                </Paper>
              </ListItem>
              {index < messages.length - 1 && <Divider />}
            </React.Fragment>
          ))}
          <div ref={messagesEndRef} />
        </List>

        <Box sx={{ p: 2, bgcolor: 'background.paper' }}>
          <form onSubmit={(e) => { e.preventDefault(); handleSend(); }}>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <TextField
                fullWidth
                variant="outlined"
                placeholder="Ask a question..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                disabled={loading}
              />
              <Button 
                variant="contained" 
                color="primary" 
                onClick={handleSend}
                disabled={loading || !input.trim()}
                sx={{ minWidth: '100px' }}
              >
                {loading ? <CircularProgress size={24} /> : <SendIcon />}
              </Button>
            </Box>
          </form>
        </Box>
      </Paper>
      
      <Snackbar 
        open={!!error} 
        autoHideDuration={6000} 
        onClose={() => setError(null)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert onClose={() => setError(null)} severity="error" sx={{ width: '100%' }}>
          {error}
        </Alert>
      </Snackbar>
    </Container>
  );
}

export default App; 
