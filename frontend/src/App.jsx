import React from 'react';
import { Container, Box } from '@mui/material';
import CourseExtractor from './components/CourseExtractor';

function App() {
  return (
    <Box sx={{ minHeight: '100vh', bgcolor: 'grey.50' }}>
      <Container sx={{ py: 4 }}>
        <CourseExtractor />
      </Container>
    </Box>
  );
}

export default App;