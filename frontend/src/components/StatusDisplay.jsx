// src/components/StatusDisplay.jsx
import React from 'react';
import { AlertCircle, CheckCircle, Loader } from 'lucide-react';
import {cn} from '@/lib/utils/cn';

const StatusDisplay = ({ status, progress, result, error }) => {
    const getStatusColor = () => {
        switch (status) {
            case 'completed':
                return 'bg-green-100 text-green-800';
            case 'failed':
                return 'bg-red-100 text-red-800';
            case 'processing':
                return 'bg-blue-100 text-blue-800';
            default:
                return 'bg-gray-100 text-gray-800';
        }
    };

    const getStatusIcon = () => {
        switch (status) {
            case 'completed':
                return <CheckCircle className="h-5 w-5" />;
            case 'failed':
                return <AlertCircle className="h-5 w-5" />;
            case 'processing':
                return <Loader className="h-5 w-5 animate-spin" />;
            default:
                return null;
        }
    };

    return (
        <div className="mt-4 p-4 rounded-lg border">
            <div className={cn('flex items-center p-2 rounded-md', getStatusColor())}>
                {getStatusIcon()}
                <span className="ml-2 font-medium">
                    {status === 'processing' ? `Processing: ${progress?.toFixed(1)}%` : status}
                </span>
            </div>

            {status === 'processing' && progress > 0 && (
                <div className="mt-2 w-full bg-gray-200 rounded-full h-2.5">
                    <div
                        className="bg-blue-600 h-2.5 rounded-full"
                        style={{ width: `${progress}%` }}
                    ></div>
                </div>
            )}

            {error && (
                <div className="mt-2 p-2 bg-red-100 text-red-800 rounded">
                    {error}
                </div>
            )}

            {result && status === 'completed' && (
                <div className="mt-2">
                    <h4 className="font-medium">Results:</h4>
                    <ul className="list-disc pl-5 mt-1">
                        {result.files.map((file, index) => (
                            <li key={index} className="text-sm">
                                {file.file}: {file.courses} courses processed
                                {file.error && (
                                    <span className="text-red-600 ml-2">(Error: {file.error})</span>
                                )}
                            </li>
                        ))}
                    </ul>
                </div>
            )}
        </div>
    );
};

export default StatusDisplay;