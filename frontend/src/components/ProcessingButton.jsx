import React, { useState, useEffect } from 'react';
import { Box, Button, CircularProgress, Typography, Fade } from '@mui/material';
import { Database, Download, Check } from 'lucide-react';

const ProcessingButton = ({
    taskId,
    processing,
    onProcessingComplete,
    onError,
    onClick,
    onDownload
}) => {
    const [progress, setProgress] = useState(0);
    const [isComplete, setIsComplete] = useState(false);
    const [showCheck, setShowCheck] = useState(false);

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
            const response = await fetch(`http://localhost:8000/status/${taskId}`);
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

    // Button content based on state
    const buttonContent = () => {
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
            disabled={processing}
            onClick={isComplete ? onDownload : onClick}
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