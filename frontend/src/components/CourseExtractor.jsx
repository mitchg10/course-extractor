import React, { useState, useEffect } from 'react';
import { logger } from '@/lib/utils/logger';
import { api } from '@/lib/utils/api';
import { cn } from '@/lib/utils/cn';
import StatusDisplay from '@/components/StatusDisplay';
// import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Box, Paper, Button, CircularProgress, FormControl, Grid, IconButton, InputLabel, List, ListItem, ListItemIcon, ListItemText, MenuItem, Select, Typography, Alert } from '@mui/material';
import {
    Upload,
    FileText,
    Database,
    Trash2,
    XCircle
} from 'lucide-react';

// TODO:
// 1. Ensure you can't upload a duplicate file
// 2. Constants file
// 3. Add a loading spinner when processing

const ENGINEERING_PROGRAMS = [
    ["AOE", "Aerospace and Ocean Engineering"],
    ["BC", "Building Construction"],
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
    { value: "01", label: "Spring" },
    { value: "06", label: "Summer I" },
    { value: "07", label: "Summer II" },
    { value: "09", label: "Fall" },
    { value: "12", label: "Winter" }
];

const YEARS = Array.from({ length: 5 }, (_, i) => new Date().getFullYear() + i);

// At the top of CourseExtractor.jsx, after imports
console.log('Testing logger availability:', logger);
logger.info('CourseExtractor component loaded');

const CourseExtractor = () => {
    const [filesData, setFilesData] = useState([]);
    const [processing, setProcessing] = useState(false);
    const [taskId, setTaskId] = useState(null);
    const [processingStatus, setProcessingStatus] = useState(null);
    const [errorMessage, setErrorMessage] = useState('');
    const [progress, setProgress] = useState(0);

    useEffect(() => {
        let interval;
        if (taskId && processing) {
            logger.info(`Starting status polling for task: ${taskId}`);
            interval = setInterval(checkTaskStatus, 2000);
        }
        return () => {
            if (interval) {
                clearInterval(interval);
                logger.info('Cleared status polling interval');
            }
        };
    }, [taskId, processing]);

    const checkTaskStatus = async () => {
        try {
            const status = await api.checkStatus(taskId);
            logger.info(`Task status update: ${status.status}`);
            setProcessingStatus(status.status);
            setProgress(status.progress || 0);

            if (['completed', 'failed'].includes(status.status.toLowerCase())) {
                setProcessing(false);
                clearInterval(interval);
                logger.info(`Processing ${status.status}`);
            }
        } catch (error) {
            logger.error('Status check failed:', error);
            setErrorMessage('Failed to check processing status');
            setProcessing(false);
        }
    };

    const validateFiles = (newFiles) => {
        logger.info(`Validating ${newFiles.length} files`);
        const invalidFiles = newFiles.filter(file =>
            file.type !== 'application/pdf' &&
            !file.name.toLowerCase().endsWith('.pdf')
        );

        if (invalidFiles.length > 0) {
            const fileNames = invalidFiles.map(f => f.name).join(', ');
            logger.warn(`Invalid file types detected: ${fileNames}`);
            setErrorMessage(`Invalid file type(s): ${fileNames}. Only PDF files are allowed.`);
            return [];
        }

        const validFiles = newFiles.map(file => ({
            file,
            program: '',
            semester: '',
            year: new Date().getFullYear(),
            id: crypto.randomUUID()
        }));

        logger.info(`Successfully validated ${validFiles.length} files`);
        return validFiles;
    };

    const handleDrop = (e) => {
        e.preventDefault();
        logger.info('File drop event detected');
        const droppedFiles = Array.from(e.dataTransfer.files);
        const validFileData = validateFiles(droppedFiles);
        if (validFileData.length > 0) {
            logger.fileOperation('drop', droppedFiles);
            setFilesData(prevFiles => [...prevFiles, ...validFileData]);
        }
    };

    const handleFileSelect = (e) => {
        logger.info('File select event detected');
        const selectedFiles = Array.from(e.target.files);
        const validFileData = validateFiles(selectedFiles);
        if (validFileData.length > 0) {
            logger.fileOperation('select', selectedFiles);
            setFilesData(prevFiles => [...prevFiles, ...validFileData]);
        }
    };

    const handleDeleteFile = (idToDelete) => {
        logger.info(`Deleting file with ID: ${idToDelete}`);
        setFilesData(prevFiles => prevFiles.filter(fileData => fileData.id !== idToDelete));
        if (processingStatus) {
            setProcessingStatus(null);
            setTaskId(null);
        }
    };

    const handleMetadataChange = (id, field, value) => {
        logger.info(`Updating metadata - ID: ${id}, Field: ${field}, Value: ${value}`);
        setFilesData(prevFiles =>
            prevFiles.map(fileData =>
                fileData.id === id
                    ? { ...fileData, [field]: value }
                    : fileData
            )
        );
    };

    const handleSubmit = async () => {
        const incompleteFiles = filesData.filter(
            fileData => !fileData.program || !fileData.semester || !fileData.year
        );

        if (incompleteFiles.length > 0) {
            logger.warn('Incomplete metadata detected');
            setErrorMessage('Please fill in all required fields for each file');
            return;
        }

        setProcessing(true);
        setProcessingStatus('processing');
        setTaskId(null);
        logger.info('Starting file processing');

        try {
            const formData = new FormData();
            // Add files to form data
            filesData.forEach((fileData, index) => {
                formData.append('files', fileData.file);
            });
            // Add metadata to form data
            const metadata = filesData.map(fileData => ({
                subject_code: fileData.program,
                term_year: `${fileData.year}${fileData.semester}`,
                file_path: fileData.file.name
            }));
            // Add metadata as a JSON string
            formData.append('metadata', JSON.stringify(metadata));

            // ! Remove
            // Add this before the fetch call
            logger.info('Metadata being sent:', JSON.stringify(metadata, null, 2));
            logger.info('Files being sent:', Array.from(formData.getAll('files')).map(f => f.name));

            // Send request to backend
            const response = await fetch('http://localhost:8000/process', {
                method: 'POST',
                body: formData
            });
            // Check if request was successful
            if (!response.ok) {
                throw new Error('Failed to process files');
            }
            // Parse response
            const result = await response.json();
            setTaskId(result.task_id);
            logger.info(`Task created with ID: ${result.task_id}`);
        } catch (error) {
            logger.error('Processing submission failed:', error);
            setErrorMessage('Failed to start processing');
            setProcessing(false);
            setProcessingStatus('failed');
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

            {/* Status display */}
            <StatusDisplay status={processingStatus} progress={progress} />

            {/* Error messages */}
            {errorMessage && (
                // <Alert variant="destructive" className="mt-4">
                //     <AlertTitle className="flex items-center gap-2">
                //         <XCircle className="h-4 w-4" />
                //         Error
                //     </AlertTitle>
                //     <AlertDescription>{errorMessage}</AlertDescription>
                // </Alert>
                <Alert
                    onClose={() => setErrorMessage('')}
                    severity="error"
                    icon={<XCircle />}
                    sx={{ width: '100%' }}
                >
                    {errorMessage}
                </Alert>
            )}
        </Box>
    );
};

export default CourseExtractor;