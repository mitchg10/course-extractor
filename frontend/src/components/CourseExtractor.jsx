import React, { useState, useEffect } from 'react';
import { logger } from '@/utils/logger';
import ProcessingButton from '@/components/ProcessingButton';
import { endpoints } from '@/config/api';
import { Box, Paper, Button, FormControl, Grid, IconButton, InputLabel, List, ListItem, ListItemIcon, ListItemText, MenuItem, Select, Typography, Alert, Slide } from '@mui/material';
import {
    Upload,
    FileText,
    Trash2,
    XCircle
} from 'lucide-react';

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

const getNextSemester = () => {
    const currentDate = new Date();
    const currentMonth = currentDate.getMonth() + 1;

    if (currentMonth >= 1 && currentMonth <= 4) {
        return SEMESTERS.find(semester => semester.label === 'Summer I').value;
    } else if (currentMonth >= 5 && currentMonth <= 6) {
        return SEMESTERS.find(semester => semester.label === 'Summer II').value;
    } else if (currentMonth >= 7 && currentMonth <= 8) {
        return SEMESTERS.find(semester => semester.label === 'Fall').value;
    } else {
        return SEMESTERS.find(semester => semester.label === 'Spring').value;
    }
};

console.log('Testing logger availability:', logger);
logger.info('CourseExtractor component loaded');

const CourseExtractor = () => {
    const [filesData, setFilesData] = useState([]);
    const [processing, setProcessing] = useState(false);
    const [taskId, setTaskId] = useState(null);
    const [errorMessage, setErrorMessage] = useState('');

    const validateFiles = (newFiles) => {
        // Validating file types
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

        // Check for duplicates
        const duplicateFiles = newFiles.filter(file =>
            filesData.some(fileData => fileData.file.name === file.name)
        );

        if (duplicateFiles.length > 0) {
            const fileNames = duplicateFiles.map(f => f.name).join(', ');
            logger.warn(`Duplicate files detected: ${fileNames}`);
            setErrorMessage(`Duplicate file(s) detected: ${fileNames}`);
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
        setTaskId(null);
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
        setErrorMessage('');

        try {
            const formData = new FormData();
            filesData.forEach(fileData => {
                formData.append('files', fileData.file);
            });

            const metadata = filesData.map(fileData => ({
                subject_code: fileData.program,
                term_year: `${fileData.year}${fileData.semester}`,
                file_path: fileData.file.name
            }));

            formData.append('metadata', JSON.stringify(metadata));

            const response = await fetch(endpoints.process, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error('Failed to process files');
            }

            const result = await response.json();
            setTaskId(result.task_id);
            logger.info(`Task created with ID: ${result.task_id}`);
        } catch (error) {
            logger.error('Processing submission failed:', error);
            setErrorMessage('Failed to start processing');
            setProcessing(false);
        }
    };

    useEffect(() => {
        if (filesData.length > 0) {
            const updatedFilesData = filesData.map(fileData => {
                if (!fileData.semester) {
                    return { ...fileData, semester: getNextSemester() };
                }
                return fileData;
            });
            setFilesData(updatedFilesData);
        }
    }, [filesData]);

    return (
        <Box sx={{ maxWidth: 'lg', mx: 'auto', p: 3 }}>
            <Typography variant="h3" component="h1" sx={{ textAlign: 'center', mb: 2 }}>
                VT Course Extractor
            </Typography>
            <Typography variant="h5" component="h2" sx={{ textAlign: 'center', mb: 4, color: 'text.secondary' }}>
                College of Engineering Course Analysis Tool
            </Typography>

            {/* Instructions Section */}
            <Paper sx={{ p: 3, mb: 4, bgcolor: 'background.paper' }}>
                <Typography variant="h6" gutterBottom>
                    How to Extract Course Data:
                </Typography>
                <Box component="ol" sx={{ pl: 2, '& li': { mb: 1 } }}>
                    <Typography component="li">
                        Access HokieSpa and navigate to <strong>Timetable of Classes</strong>
                    </Typography>
                    <Typography component="li">
                        Select <strong>College of Engineering</strong> department information
                    </Typography>
                    <Typography component="li">
                        Click <strong>FIND class sections</strong>
                    </Typography>
                    <Typography component="li">
                        Click <strong>Printer Friendly List</strong>
                    </Typography>
                    <Typography component="li">
                        Print the page and save as PDF
                    </Typography>
                    <Typography component="li">
                        Repeat for all College of Engineering departments
                    </Typography>
                </Box>

                <Typography variant="h6" sx={{ mt: 3, mb: 1 }}>
                    Output Files:
                </Typography>
                <Box component="ul" sx={{ pl: 2, '& li': { mb: 1 } }}>
                    <Typography component="li">
                        <strong>Complete Course List:</strong> A CSV file containing all courses from uploaded PDF files
                    </Typography>
                    <Typography component="li">
                        <strong>Underenrolled Courses:</strong> A CSV file showing courses with fewer than 6 enrolled students
                    </Typography>
                </Box>
            </Paper>
            
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
                    <ProcessingButton
                        taskId={taskId}
                        processing={processing}
                        onClick={handleSubmit}
                        onProcessingComplete={(result) => {
                            setProcessing(false);
                            logger.info('Processing completed successfully', result);
                        }}
                        onError={(error) => {
                            setProcessing(false);
                            setErrorMessage(error);
                            logger.error('Error occurred:', error);
                        }}
                    />
                </Box>
            )}

            {/* Error messages */}
            <Slide direction="up" in={errorMessage !== ''} mountOnEnter unmountOnExit>
                <Alert
                    onClose={() => setErrorMessage('')}
                    severity="error"
                    icon={<XCircle />}
                    sx={{ width: '100%', mt: 8 }}
                >
                    {errorMessage}
                </Alert>
            </Slide>
        </Box>
    );
};

export default CourseExtractor;