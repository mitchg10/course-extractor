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
  Snackbar,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid
} from '@mui/material';
import {
  Upload,
  FileText,
  Database,
  Trash2,
  XCircle
} from 'lucide-react';

// Engineering programs filtered from the constants
const ENGINEERING_PROGRAMS = [
  ["AOE", "Aerospace and Ocean Engineering"],
  ["BSE", "Biological Systems Engineering"],
  ["CEE", "Civil and Environmental Engineering"],
  ["CHE", "Chemical Engineering"],
  ["CS", "Computer Science"],
  ["ECE", "Electrical and Computer Engineering"],
  ["ENGE", "Engineering Education"],
  ["ENGR", "Engineering"],
  ["ESM", "Engineering Science and Mechanics"],
  ["ISE", "Industrial and Systems Engineering"],
  ["ME", "Mechanical Engineering"],
  ["MINE", "Mining Engineering"],
  ["MSE", "Materials Science and Engineering"],
  ["NSEG", "Nuclear Science and Engineering"]
];

const SEMESTERS = [
  { value: "1", label: "Spring" },
  { value: "6", label: "Summer I" },
  { value: "7", label: "Summer II" },
  { value: "9", label: "Fall" },
  { value: "12", label: "Winter" }
];

const YEARS = Array.from({ length: 5 }, (_, i) => new Date().getFullYear() + i);

const CourseExtractor = () => {
  // Modified to store files with their metadata
  const [filesData, setFilesData] = useState([]);
  const [processing, setProcessing] = useState(false);
  const [taskId, setTaskId] = useState(null);
  const [processingStatus, setProcessingStatus] = useState(null);
  const [errorMessage, setErrorMessage] = useState('');

  const validateFiles = (newFiles) => {
    const invalidFiles = newFiles.filter(file =>
      file.type !== 'application/pdf' &&
      !file.name.toLowerCase().endsWith('.pdf')
    );

    if (invalidFiles.length > 0) {
      const fileNames = invalidFiles.map(f => f.name).join(', ');
      setErrorMessage(`Invalid file type(s): ${fileNames}. Only PDF files are allowed.`);
      return [];
    }

    return newFiles.map(file => ({
      file,
      program: '',
      semester: '',
      year: new Date().getFullYear(),
      id: crypto.randomUUID() // Unique identifier for each file entry
    }));
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const droppedFiles = Array.from(e.dataTransfer.files);
    const validFileData = validateFiles(droppedFiles);
    if (validFileData.length > 0) {
      setFilesData(prevFiles => [...prevFiles, ...validFileData]);
    }
  };

  const handleFileSelect = (e) => {
    const selectedFiles = Array.from(e.target.files);
    const validFileData = validateFiles(selectedFiles);
    if (validFileData.length > 0) {
      setFilesData(prevFiles => [...prevFiles, ...validFileData]);
    }
  };

  const handleDeleteFile = (idToDelete) => {
    setFilesData(prevFiles => prevFiles.filter(fileData => fileData.id !== idToDelete));
    if (processingStatus) {
      setProcessingStatus(null);
      setTaskId(null);
    }
  };

  const handleMetadataChange = (id, field, value) => {
    setFilesData(prevFiles =>
      prevFiles.map(fileData =>
        fileData.id === id
          ? { ...fileData, [field]: value }
          : fileData
      )
    );
  };

  const handleSubmit = async () => {
    // Validate that all files have complete metadata
    const incompleteFiles = filesData.filter(
      fileData => !fileData.program || !fileData.semester || !fileData.year
    );

    if (incompleteFiles.length > 0) {
      setErrorMessage('Please fill in all required fields for each file');
      return;
    }

    setProcessing(true);
    setProcessingStatus(null);
    setTaskId(null);

    const formData = new FormData();

    // Add each file with its metadata
    filesData.forEach((fileData, index) => {
      formData.append('files', fileData.file);
      formData.append(`metadata_${index}`, JSON.stringify({
        subject_code: fileData.program,
        term_year: `${fileData.year}${fileData.semester}`
      }));
    });

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
          borderColor: filesData.length === 0 ? 'grey.300' : 'primary.main',
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

      {/* File list with metadata selectors */}
      {filesData.length > 0 && (
        <Box sx={{ mb: 3 }}>
          <Typography variant="h5" gutterBottom>
            Selected Files ({filesData.length})
          </Typography>
          <List>
            {filesData.map((fileData) => (
              <ListItem
                key={fileData.id}
                sx={{
                  bgcolor: 'grey.50',
                  borderRadius: 1,
                  mb: 1,
                  flexDirection: 'column',
                  alignItems: 'stretch'
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', width: '100%', mb: 2 }}>
                  <ListItemIcon>
                    <FileText className="text-blue-500" />
                  </ListItemIcon>
                  <ListItemText
                    primary={fileData.file.name}
                    secondary={`${(fileData.file.size / (1024 * 1024)).toFixed(2)} MB`}
                  />
                  <Box sx={{ display: 'flex', alignItems: 'center', ml: 'auto' }}>
                    <IconButton
                      edge="end"
                      onClick={() => handleDeleteFile(fileData.id)}
                      disabled={processing}
                      className="text-red-500 hover:text-red-700"
                    >
                      <Trash2 />
                    </IconButton>
                  </Box>
                </Box>

                <Grid container spacing={2} sx={{ px: 2, pb: 2 }}>
                  <Grid item xs={12} md={4}>
                    <FormControl fullWidth size="small">
                      <InputLabel>Engineering Program</InputLabel>
                      <Select
                        value={fileData.program}
                        label="Engineering Program"
                        onChange={(e) => handleMetadataChange(fileData.id, 'program', e.target.value)}
                        disabled={processing}
                      >
                        {ENGINEERING_PROGRAMS.map(([code, name]) => (
                          <MenuItem key={code} value={code}>
                            {name}
                          </MenuItem>
                        ))}
                      </Select>
                    </FormControl>
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <FormControl fullWidth size="small">
                      <InputLabel>Semester</InputLabel>
                      <Select
                        value={fileData.semester}
                        label="Semester"
                        onChange={(e) => handleMetadataChange(fileData.id, 'semester', e.target.value)}
                        disabled={processing}
                      >
                        {SEMESTERS.map((semester) => (
                          <MenuItem key={semester.value} value={semester.value}>
                            {semester.label}
                          </MenuItem>
                        ))}
                      </Select>
                    </FormControl>
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <FormControl fullWidth size="small">
                      <InputLabel>Year</InputLabel>
                      <Select
                        value={fileData.year}
                        label="Year"
                        onChange={(e) => handleMetadataChange(fileData.id, 'year', e.target.value)}
                        disabled={processing}
                      >
                        {YEARS.map((year) => (
                          <MenuItem key={year} value={year}>
                            {year}
                          </MenuItem>
                        ))}
                      </Select>
                    </FormControl>
                  </Grid>
                </Grid>
              </ListItem>
            ))}
          </List>
        </Box>
      )}

      {/* Process button */}
      {filesData.length > 0 && (
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

      {/* Status messages and error handling components... */}
      <Snackbar
        open={!!errorMessage}
        autoHideDuration={6000}
        onClose={() => setErrorMessage('')}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert
          onClose={() => setErrorMessage('')}
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