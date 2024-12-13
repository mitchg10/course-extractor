import React, { useState, useEffect } from 'react';
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
  Snackbar,
  LinearProgress
} from '@mui/material';
import {
  Upload,
  FileText,
  Database,
  CheckCircle,
  Trash2,
  XCircle,
  RefreshCcw
} from 'lucide-react';

const CourseExtractor = () => {
  const [files, setFiles] = useState([]);
  const [processing, setProcessing] = useState(false);
  const [taskId, setTaskId] = useState(null);
  const [processingStatus, setProcessingStatus] = useState(null);
  const [errorMessage, setErrorMessage] = useState('');

  // Status polling
  useEffect(() => {
    let pollInterval;

    const pollStatus = async () => {
      if (!taskId) return;

      try {
        const response = await fetch(`http://localhost:8000/status/${taskId}`);
        if (!response.ok) throw new Error('Failed to fetch status');

        const statusData = await response.json();
        setProcessingStatus(statusData);

        // Stop polling if processing is complete
        if (statusData.status === 'completed') {
          setProcessing(false);
          clearInterval(pollInterval);
        }
      } catch (error) {
        console.error('Status polling failed:', error);
        setErrorMessage('Failed to get processing status');
        setProcessing(false);
        clearInterval(pollInterval);
      }
    };

    if (processing && taskId) {
      pollInterval = setInterval(pollStatus, 2000); // Poll every 2 seconds
    }

    return () => {
      if (pollInterval) clearInterval(pollInterval);
    };
  }, [taskId, processing]);

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
    const droppedFiles = Array.from(e.dataTransfer.files);
    const validFiles = validateFiles(droppedFiles);
    if (validFiles.length > 0) {
      setFiles(prevFiles => [...prevFiles, ...validFiles]);
    }
  };

  const handleFileSelect = (e) => {
    const selectedFiles = Array.from(e.target.files);
    const validFiles = validateFiles(selectedFiles);
    if (validFiles.length > 0) {
      setFiles(prevFiles => [...prevFiles, ...validFiles]);
    }
  };

  const handleDeleteFile = (indexToDelete) => {
    setFiles(prevFiles => prevFiles.filter((_, index) => index !== indexToDelete));
    if (processingStatus) {
      setProcessingStatus(null);
      setTaskId(null);
    }
  };

  const handleSubmit = async () => {
    setProcessing(true);
    setProcessingStatus(null);
    setTaskId(null);

    const formData = new FormData();
    files.forEach(file => formData.append('files', file));

    try {
      const response = await fetch('http://localhost:8000/process', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) throw new Error('Processing failed');

      const result = await response.json();
      setTaskId(result.task_id);
    } catch (error) {
      setErrorMessage('Failed to start processing');
      setProcessing(false);
    }
  };

  const getProgressPercentage = () => {
    if (!processingStatus) return 0;
    const { total, processed, failed } = processingStatus;
    return ((processed + failed) / total) * 100;
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
        <Upload className="w-16 h-16 mb-2 text-gray-500" />
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
                  <FileText className="text-blue-500" />
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
                    className="text-red-500 hover:text-red-700"
                  >
                    <Trash2 />
                  </IconButton>
                </ListItemSecondaryAction>
              </ListItem>
            ))}
          </List>
        </Box>
      )}

      {/* Progress indicator */}
      {processing && processingStatus && (
        <Box sx={{ mb: 3 }}>
          <LinearProgress
            variant="determinate"
            value={getProgressPercentage()}
            sx={{ mb: 1 }}
          />
          <Typography variant="body2" color="text.secondary" align="center">
            Processed: {processingStatus.processed} / {processingStatus.total} files
            {processingStatus.failed > 0 && ` (${processingStatus.failed} failed)`}
          </Typography>
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
            startIcon={processing ? <CircularProgress size={20} /> : <Database />}
            sx={{ px: 4, py: 1.5 }}
          >
            {processing ? 'Processing...' : 'Extract Course Data'}
          </Button>
        </Box>
      )}

      {/* Status messages */}
      {processingStatus?.status === 'processing' && (
        <Alert
          severity="info"
          icon={<RefreshCcw className="animate-spin" />}
          sx={{ mt: 3 }}
        >
          Processing your files. This may take a few minutes...
        </Alert>
      )}

      {processingStatus?.status === 'completed' && (
        <Alert
          severity="success"
          icon={<CheckCircle />}
          sx={{ mt: 3 }}
        >
          {processingStatus.failed === 0 ? (
            'Processing complete! You can find your CSV files in the data folder.'
          ) : (
            `Processing complete with ${processingStatus.failed} errors. Check the logs for details.`
          )}
          {processingStatus.combined_output && (
            <Typography variant="body2" sx={{ mt: 1 }}>
              Combined CSV: {processingStatus.combined_output}
            </Typography>
          )}
        </Alert>
      )}

      {/* Error messages */}
      <Snackbar
        open={!!errorMessage}
        autoHideDuration={6000}
        onClose={handleCloseError}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert
          onClose={handleCloseError}
          severity="error"
          icon={<XCircle />}
          sx={{ width: '100%' }}
        >
          {errorMessage}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default CourseExtractor;