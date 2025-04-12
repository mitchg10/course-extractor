import React, { useState, useEffect } from 'react';
import { Box, Button, CircularProgress, Typography, Fade } from '@mui/material';
import { Database, Download, Check } from 'lucide-react';
import { logger } from '@/utils/logger';
import { endpoints } from '@/config/api';

const ProcessingButton = ({
    taskId,
    processing,
    onProcessingComplete,
    onError,
    onClick
}) => {
    const [progress, setProgress] = useState(0);
    const [isComplete, setIsComplete] = useState(false);
    const [showCheck, setShowCheck] = useState(false);
    const [downloading, setDownloading] = useState(false);
    const [downloaded, setDownloaded] = useState(false);

    useEffect(() => {
        let interval;
        if (taskId && processing) {
            interval = setInterval(checkStatus, 2000);
            setIsComplete(false);
            setShowCheck(false);
        }
        return () => interval && clearInterval(interval);
    }, [taskId, processing]);

    const checkStatus = async () => {
        try {
            const response = await fetch(endpoints.status(taskId));
            if (!response.ok) throw new Error('Failed to fetch status');

            const data = await response.json();
            setProgress(data.progress || 0);

            if (data.status === 'completed') {
                handleCompletion(data.result);
            } else if (data.status === 'failed') {
                onError?.(data.error || 'Processing failed');
            }
        } catch (error) {
            onError?.(error.message);
        }
    };

    const handleCompletion = (result) => {
        setProgress(100);
        // Show check mark animation
        setShowCheck(true);
        // After a brief delay, show the complete state
        setTimeout(() => {
            setIsComplete(true);
            onProcessingComplete?.(result);
        }, 1000);
    };

    const handleDownload = async () => {
        if (!taskId) return;

        try {
            setDownloading(true);
            logger.info('Starting download process...');

            // Get available files
            const response = await fetch(endpoints.availableFiles(taskId), {
                method: 'GET',
                headers: {
                    'Accept': 'application/json',
                }
            });

            if (!response.ok) {
                throw new Error(`Failed to fetch available files: ${response.statusText}`);
            }

            const data = await response.json();
            logger.info(`Found ${data.files?.length || 0} files available for download`);

            if (!data.files?.length) {
                throw new Error('No files available for download');
            }

            // Download each file
            for (const file of data.files) {
                logger.info(`Attempting to download: ${file.filename}`);

                const downloadResponse = await fetch(
                    endpoints.download(taskId, file.filename),
                    {
                        method: 'GET',
                        headers: {
                            'Accept': 'text/csv,application/octet-stream'
                        }
                    }
                );

                if (!downloadResponse.ok) {
                    throw new Error(`Failed to download ${file.filename}: ${downloadResponse.statusText}`);
                }

                const blob = await downloadResponse.blob();
                const url = window.URL.createObjectURL(blob);

                // Create and click download link
                const a = document.createElement('a');
                a.style.display = 'none';
                a.href = url;
                a.download = file.filename;
                document.body.appendChild(a);
                a.click();

                // Cleanup
                setTimeout(() => {
                    document.body.removeChild(a);
                    window.URL.revokeObjectURL(url);
                }, 100);

                logger.info(`Successfully downloaded file: ${file.filename}`);
            }

            logger.info('Successfully completed all downloads');
            setDownloaded(true); // Mark as downloaded
        } catch (error) {
            logger.error('Error downloading files:', error);
            onError?.(error.message || 'Failed to download files');
        } finally {
            setDownloading(false);
        }
    };

    // Button content based on state
    const buttonContent = () => {
        if (downloaded) {
            return (
                <Fade in={downloaded}>
                    <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 0.5 }}>
                        <Typography variant="button">Downloaded!</Typography>
                        <Typography variant="caption" sx={{ fontSize: '0.75rem' }}>
                            The files can be found in your Downloads folder
                        </Typography>
                    </Box>
                </Fade>
            );
        }

        if (downloading) {
            return (
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <CircularProgress size={20} color="inherit" />
                    <Typography variant="button">
                        Downloading...
                    </Typography>
                </Box>
            );
        }

        if (processing) {
            return (
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <CircularProgress size={20} color="inherit" />
                    <Typography variant="button">
                        {progress.toFixed(1)}%
                    </Typography>
                </Box>
            );
        }

        if (showCheck && !isComplete) {
            return (
                <Fade in={showCheck}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Check size={20} />
                        <Typography variant="button">Complete!</Typography>
                    </Box>
                </Fade>
            );
        }

        if (isComplete) {
            return (
                <Fade in={isComplete}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Download size={20} />
                        <Typography variant="button">Download Results</Typography>
                    </Box>
                </Fade>
            );
        }

        return (
            <>
                <Database size={20} />
                <Typography variant="button" sx={{ ml: 1 }}>
                    Extract Course Data
                </Typography>
            </>
        );
    };

    return (
        <Button
            variant="contained"
            color={isComplete ? "success" : "primary"}
            disabled={processing || downloading || downloaded}
            onClick={isComplete && !downloaded ? handleDownload : onClick}
            sx={{
                px: 4,
                py: 1.5,
                minWidth: '200px',
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 1,
                transition: 'all 0.3s ease'
            }}
        >
            {buttonContent()}
        </Button>
    );
};

export default ProcessingButton;