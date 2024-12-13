import React, { useState } from 'react';
import {
  Box,
  Typography,
  Button,
  Paper,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Alert,
  CircularProgress
} from '@mui/material';
import {
  Upload as UploadIcon,
  FileText as FileTextIcon,
  Database as DatabaseIcon,
  AlertCircle as AlertCircleIcon,
  CheckCircle as CheckCircleIcon
} from 'lucide-react';

const CourseExtractor = () => {
  const [files, setFiles] = useState([]);
  const [processing, setProcessing] = useState(false);
  const [status, setStatus] = useState(null);

  const handleDrop = (e) => {
    e.preventDefault();
    const droppedFiles = Array.from(e.dataTransfer.files).filter(
      file => file.type === 'application/pdf'
    );
    setFiles(prevFiles => [...prevFiles, ...droppedFiles]);
  };

  const handleFileSelect = (e) => {
    const selectedFiles = Array.from(e.target.files);
    setFiles(prevFiles => [...prevFiles, ...selectedFiles]);
  };

  const handleSubmit = async () => {
    setProcessing(true);
    setStatus('processing');

    const formData = new FormData();
    files.forEach(file => formData.append('files', file));

    try {
      const response = await fetch('http://localhost:8000/process', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) throw new Error('Processing failed');

      const result = await response.json();
      setStatus('complete');
    } catch (error) {
      setStatus('error');
    } finally {
      setProcessing(false);
    }
  };

  return (
    <Box sx={{ maxWidth: 'lg', mx: 'auto' }}>
      <Typography variant="h3" component="h1" align="center" gutterBottom>
        Course Data Extractor
      </Typography>

      {/* Upload area */}
      <Paper
        variant="outlined"
        sx={{
          border: 3,
          borderStyle: 'dashed',
          borderColor: files.length === 0 ? 'grey.300' : 'primary.main',
          borderRadius: 2,
          p: 4,
          mb: 3,
          textAlign: 'center'
        }}
        onDragOver={(e) => e.preventDefault()}
        onDrop={handleDrop}
      >
        <UploadIcon style={{ width: 64, height: 64, margin: '0 auto 16px', color: '#9e9e9e' }} />
        <Typography variant="h6" gutterBottom>
          Drag and drop your PDF files here
        </Typography>
        <Typography variant="body2" color="text.secondary" gutterBottom>
          or
        </Typography>
        <input
          type="file"
          accept=".pdf"
          multiple
          onChange={handleFileSelect}
          style={{ display: 'none' }}
          id="file-upload"
        />
        <label htmlFor="file-upload">
          <Button
            variant="contained"
            component="span"
            sx={{ mt: 2 }}
          >
            Choose Files
          </Button>
        </label>
      </Paper>

      {/* File list */}
      {files.length > 0 && (
        <Box sx={{ mb: 3 }}>
          <Typography variant="h5" gutterBottom>
            Selected Files
          </Typography>
          <List>
            {files.map((file, index) => (
              <ListItem key={index} sx={{ bgcolor: 'grey.50', borderRadius: 1, mb: 1 }}>
                <ListItemIcon>
                  <FileTextIcon style={{ color: '#1976d2' }} />
                </ListItemIcon>
                <ListItemText primary={file.name} />
              </ListItem>
            ))}
          </List>
        </Box>
      )}

      {/* Process button */}
      {files.length > 0 && (
        <Box sx={{ textAlign: 'center' }}>
          <Button
            variant="contained"
            color="success"
            disabled={processing}
            onClick={handleSubmit}
            startIcon={processing ? <CircularProgress size={20} /> : <DatabaseIcon />}
            sx={{ px: 4, py: 1.5 }}
          >
            {processing ? 'Processing...' : 'Extract Course Data'}
          </Button>
        </Box>
      )}

      {/* Status messages */}
      {status === 'processing' && (
        <Alert
          severity="info"
          icon={<AlertCircleIcon />}
          sx={{ mt: 3 }}
        >
          Processing your files. This may take a few minutes...
        </Alert>
      )}

      {status === 'complete' && (
        <Alert
          severity="success"
          icon={<CheckCircleIcon />}
          sx={{ mt: 3 }}
        >
          Processing complete! You can find your CSV files in the data folder.
        </Alert>
      )}

      {status === 'error' && (
        <Alert
          severity="error"
          icon={<AlertCircleIcon />}
          sx={{ mt: 3 }}
        >
          An error occurred while processing your files. Please try again.
        </Alert>
      )}
    </Box>
  );
};

export default CourseExtractor;