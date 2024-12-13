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
  CircularProgress,
  IconButton,
  ListItemSecondaryAction,
  Snackbar
} from '@mui/material';
import {
  Upload as UploadIcon,
  FileText as FileTextIcon,
  Database as DatabaseIcon,
  AlertCircle as AlertCircleIcon,
  CheckCircle as CheckCircleIcon,
  Trash2 as TrashIcon,
  XCircle as XCircleIcon
} from 'lucide-react';

const CourseExtractor = () => {
  const [files, setFiles] = useState([]);
  const [processing, setProcessing] = useState(false);
  const [status, setStatus] = useState(null);
  const [errorMessage, setErrorMessage] = useState('');

  const validateFiles = (newFiles) => {
    const invalidFiles = newFiles.filter(file =>
      file.type !== 'application/pdf' &&
      !file.name.toLowerCase().endsWith('.pdf')
    );

    if (invalidFiles.length > 0) {
      const fileNames = invalidFiles.map(f => f.name).join(', ');
      setErrorMessage(`Invalid file type(s): ${fileNames}. Only PDF files are allowed.`);
      return newFiles.filter(file =>
        file.type === 'application/pdf' ||
        file.name.toLowerCase().endsWith('.pdf')
      );
    }
    return newFiles;
  };

  const handleCloseError = () => {
    setErrorMessage('');
  };

  const handleDrop = (e) => {
    e.preventDefault();
    // const droppedFiles = Array.from(e.dataTransfer.files).filter(
    //   file => file.type === 'application/pdf'
    // );
    // setFiles(prevFiles => [...prevFiles, ...droppedFiles]);
    const droppedFiles = Array.from(e.dataTransfer.files);
    const validFiles = validateFiles(droppedFiles);
    if (validFiles.length > 0) {
      setFiles(prevFiles => [...prevFiles, ...validFiles]);
    }
  };

  const handleFileSelect = (e) => {
    // const selectedFiles = Array.from(e.target.files);
    // setFiles(prevFiles => [...prevFiles, ...selectedFiles]);
    const selectedFiles = Array.from(e.target.files);
    const validFiles = validateFiles(selectedFiles);
    if (validFiles.length > 0) {
      setFiles(prevFiles => [...prevFiles, ...validFiles]);
    }
  };

  const handleDeleteFile = (indexToDelete) => {
    setFiles(prevFiles => prevFiles.filter((_, index) => index !== indexToDelete));
    if (status === 'error' || status === 'complete') {
      setStatus(null);
    }
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
    <Box sx={{ maxWidth: 'lg', mx: 'auto', p: 3 }}>
      <Typography variant="h3" component="h1" sx={{ textAlign: 'center', mb: 3 }}>
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
          textAlign: 'center',
          bgcolor: 'background.paper'
        }}
        onDragOver={(e) => e.preventDefault()}
        onDrop={handleDrop}
      >
        <UploadIcon sx={{ width: 64, height: 64, mb: 2, color: 'text.secondary' }} />
        <Typography variant="h6" gutterBottom>
          Drag and drop PDF files here
        </Typography>
        <Typography variant="body2" color="text.secondary" gutterBottom>
          or
        </Typography>
        <input
          type="file"
          accept=".pdf,application/pdf"
          multiple
          onChange={handleFileSelect}
          style={{ display: 'none' }}
          id="file-upload"
        />
        <Button
          variant="contained"
          component="label"
          htmlFor="file-upload"
          sx={{ mt: 2 }}
        >
          Choose Files
        </Button>
      </Paper>

      {/* File list */}
      {files.length > 0 && (
        <Box sx={{ mb: 3 }}>
          <Typography variant="h5" gutterBottom>
            Selected Files ({files.length})
          </Typography>
          <List>
            {files.map((file, index) => (
              <ListItem
                key={index}
                sx={{
                  bgcolor: 'grey.50',
                  borderRadius: 1,
                  mb: 1
                }}
              >
                <ListItemIcon>
                  <FileTextIcon sx={{ color: 'primary.main' }} />
                </ListItemIcon>
                <ListItemText
                  primary={file.name}
                  secondary={`${(file.size / (1024 * 1024)).toFixed(2)} MB`}
                />
                <ListItemSecondaryAction>
                  <IconButton
                    edge="end"
                    onClick={() => handleDeleteFile(index)}
                    disabled={processing}
                    sx={{
                      color: 'error.main',
                      '&:hover': {
                        color: 'error.dark'
                      }
                    }}
                  >
                    <TrashIcon />
                  </IconButton>
                </ListItemSecondaryAction>
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

      <Snackbar
        open={!!errorMessage}
        autoHideDuration={6000}
        onClose={handleCloseError}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert
          onClose={handleCloseError}
          severity="error"
          icon={<XCircleIcon />}
          sx={{ width: '100%' }}
        >
          {errorMessage}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default CourseExtractor;