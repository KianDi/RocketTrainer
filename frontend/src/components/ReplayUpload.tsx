import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import {
  CloudArrowUpIcon,
  DocumentIcon,
  XMarkIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline';
import { replayService } from '../services/replayService';

interface ReplayUploadProps {
  onUploadComplete?: (replayId: string) => void;
  onUploadError?: (error: string) => void;
  className?: string;
}

interface UploadProgress {
  file: File;
  progress: number;
  status: 'uploading' | 'processing' | 'completed' | 'error';
  replayId?: string;
  taskId?: string;
  error?: string;
}

const ReplayUpload: React.FC<ReplayUploadProps> = ({
  onUploadComplete,
  onUploadError,
  className = ''
}) => {
  const [uploads, setUploads] = useState<UploadProgress[]>([]);
  const [isDragActive, setIsDragActive] = useState(false);

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const replayFiles = acceptedFiles.filter(file => 
      file.name.toLowerCase().endsWith('.replay')
    );

    if (replayFiles.length === 0) {
      onUploadError?.('Please select .replay files only');
      return;
    }

    // Initialize upload progress for each file
    const newUploads: UploadProgress[] = replayFiles.map(file => ({
      file,
      progress: 0,
      status: 'uploading' as const
    }));

    setUploads(prev => [...prev, ...newUploads]);

    // Upload each file
    for (let i = 0; i < replayFiles.length; i++) {
      const file = replayFiles[i];
      const uploadIndex = uploads.length + i;

      try {
        // Update progress to show upload starting
        setUploads(prev => prev.map((upload, idx) => 
          idx === uploadIndex 
            ? { ...upload, progress: 10, status: 'uploading' }
            : upload
        ));

        // Upload the file
        const response = await replayService.uploadReplay(file);
        
        // Update with task ID and start monitoring
        setUploads(prev => prev.map((upload, idx) => 
          idx === uploadIndex 
            ? { 
                ...upload, 
                progress: 30, 
                status: 'processing',
                replayId: response.id,
                taskId: response.task_id
              }
            : upload
        ));

        // Monitor processing progress
        if (response.task_id) {
          monitorTaskProgress(response.task_id, uploadIndex);
        }

      } catch (error) {
        console.error('Upload failed:', error);
        setUploads(prev => prev.map((upload, idx) => 
          idx === uploadIndex 
            ? { 
                ...upload, 
                status: 'error',
                error: error instanceof Error ? error.message : 'Upload failed'
              }
            : upload
        ));
        onUploadError?.(error instanceof Error ? error.message : 'Upload failed');
      }
    }
  }, [uploads.length, onUploadError]);

  const monitorTaskProgress = async (taskId: string, uploadIndex: number) => {
    const pollInterval = 2000; // Poll every 2 seconds
    const maxAttempts = 150; // 5 minutes max
    let attempts = 0;

    const poll = async () => {
      try {
        attempts++;
        const status = await replayService.getTaskStatus(taskId);

        setUploads(prev => prev.map((upload, idx) => 
          idx === uploadIndex 
            ? { 
                ...upload, 
                progress: Math.max(30, status.current || 0),
                status: status.state === 'SUCCESS' ? 'completed' : 
                       status.state === 'FAILURE' ? 'error' : 'processing',
                error: status.error
              }
            : upload
        ));

        if (status.state === 'SUCCESS') {
          onUploadComplete?.(uploads[uploadIndex]?.replayId || '');
        } else if (status.state === 'FAILURE') {
          onUploadError?.(status.error || 'Processing failed');
        } else if (attempts < maxAttempts) {
          setTimeout(poll, pollInterval);
        } else {
          // Timeout
          setUploads(prev => prev.map((upload, idx) => 
            idx === uploadIndex 
              ? { ...upload, status: 'error', error: 'Processing timeout' }
              : upload
          ));
          onUploadError?.('Processing timeout');
        }
      } catch (error) {
        console.error('Failed to check task status:', error);
        if (attempts < maxAttempts) {
          setTimeout(poll, pollInterval);
        }
      }
    };

    setTimeout(poll, pollInterval);
  };

  const removeUpload = (index: number) => {
    setUploads(prev => prev.filter((_, idx) => idx !== index));
  };

  const { getRootProps, getInputProps, isDragActive: dropzoneActive } = useDropzone({
    onDrop,
    accept: {
      'application/octet-stream': ['.replay']
    },
    multiple: true,
    onDragEnter: () => setIsDragActive(true),
    onDragLeave: () => setIsDragActive(false),
    onDropAccepted: () => setIsDragActive(false),
    onDropRejected: () => setIsDragActive(false)
  });

  const getStatusIcon = (status: UploadProgress['status']) => {
    switch (status) {
      case 'uploading':
      case 'processing':
        return <ArrowPathIcon className="w-5 h-5 animate-spin text-blue-500" />;
      case 'completed':
        return <CheckCircleIcon className="w-5 h-5 text-green-500" />;
      case 'error':
        return <ExclamationTriangleIcon className="w-5 h-5 text-red-500" />;
      default:
        return <DocumentIcon className="w-5 h-5 text-gray-400" />;
    }
  };

  const getStatusText = (upload: UploadProgress) => {
    switch (upload.status) {
      case 'uploading':
        return 'Uploading...';
      case 'processing':
        return 'Processing replay...';
      case 'completed':
        return 'Analysis complete!';
      case 'error':
        return upload.error || 'Failed';
      default:
        return 'Waiting...';
    }
  };

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Drop Zone */}
      <div
        {...getRootProps()}
        className={`
          border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors
          ${isDragActive || dropzoneActive 
            ? 'border-rl-blue bg-blue-50' 
            : 'border-gray-300 hover:border-gray-400'
          }
        `}
      >
        <input {...getInputProps()} />
        <CloudArrowUpIcon className="w-12 h-12 mx-auto text-gray-400 mb-4" />
        <p className="text-lg font-medium text-gray-900 mb-2">
          {isDragActive ? 'Drop your replay files here' : 'Upload Replay Files'}
        </p>
        <p className="text-gray-600">
          Drag and drop .replay files here, or click to select files
        </p>
        <p className="text-sm text-gray-500 mt-2">
          Supports multiple files • Max 50MB per file
        </p>
      </div>

      {/* Upload Progress */}
      {uploads.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-lg font-medium text-gray-900">Upload Progress</h3>
          {uploads.map((upload, index) => (
            <div key={index} className="bg-white border rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center space-x-3">
                  {getStatusIcon(upload.status)}
                  <div>
                    <p className="font-medium text-gray-900">{upload.file.name}</p>
                    <p className="text-sm text-gray-600">
                      {(upload.file.size / (1024 * 1024)).toFixed(1)} MB
                    </p>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-sm text-gray-600">
                    {getStatusText(upload)}
                  </span>
                  {upload.status === 'error' && (
                    <button
                      onClick={() => removeUpload(index)}
                      className="text-red-500 hover:text-red-700"
                    >
                      <XMarkIcon className="w-4 h-4" />
                    </button>
                  )}
                </div>
              </div>
              
              {/* Progress Bar */}
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className={`h-2 rounded-full transition-all duration-300 ${
                    upload.status === 'completed' ? 'bg-green-500' :
                    upload.status === 'error' ? 'bg-red-500' : 'bg-blue-500'
                  }`}
                  style={{ width: `${upload.progress}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ReplayUpload;
