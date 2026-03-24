import React, { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, File, X, AlertCircle } from 'lucide-react';

const FileUpload = ({ 
  onFileSelect, 
  accept = { 'application/pdf': ['.pdf'], 'text/plain': ['.txt'] },
  maxSize = 10485760, // 10MB
  loading = false,
  error = null
}) => {
  const onDrop = useCallback((acceptedFiles, rejectedFiles) => {
    if (rejectedFiles.length > 0) {
      const rejection = rejectedFiles[0];
      let errorMsg = 'Invalid file';
      
      if (rejection.errors.find(e => e.code === 'file-too-large')) {
        errorMsg = 'File too large. Maximum size is 10MB.';
      } else if (rejection.errors.find(e => e.code === 'file-invalid-type')) {
        errorMsg = 'Invalid file type. Please upload PDF or TXT files.';
      }
      
      onFileSelect(null, errorMsg);
      return;
    }

    if (acceptedFiles.length > 0) {
      onFileSelect(acceptedFiles[0], null);
    }
  }, [onFileSelect]);

  const {
    getRootProps,
    getInputProps,
    isDragActive,
    isDragReject,
    acceptedFiles,
  } = useDropzone({
    onDrop,
    accept,
    maxSize,
    multiple: false,
    disabled: loading,
  });

  const selectedFile = acceptedFiles[0];

  return (
    <div className="space-y-4">
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
          isDragActive && !isDragReject
            ? 'border-primary-500 bg-primary-50'
            : isDragReject
            ? 'border-red-500 bg-red-50'
            : 'border-gray-300 hover:border-gray-400'
        } ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}
      >
        <input {...getInputProps()} />
        
        <Upload className={`mx-auto h-12 w-12 ${
          isDragActive && !isDragReject 
            ? 'text-primary-500' 
            : isDragReject 
            ? 'text-red-500' 
            : 'text-gray-400'
        }`} />
        
        <div className="mt-4">
          {loading ? (
            <p className="text-sm text-gray-600">Uploading...</p>
          ) : isDragActive && !isDragReject ? (
            <p className="text-sm text-primary-600">Drop your resume here</p>
          ) : isDragReject ? (
            <p className="text-sm text-red-600">Invalid file type or size</p>
          ) : (
            <>
              <p className="text-sm text-gray-600">
                Drop your resume here, or{' '}
                <span className="text-primary-600 font-medium">browse</span>
              </p>
              <p className="text-xs text-gray-500 mt-1">
                PDF, TXT files up to 10MB
              </p>
            </>
          )}
        </div>
      </div>

      {/* Selected file display */}
      {selectedFile && (
        <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border">
          <div className="flex items-center">
            <File className="h-5 w-5 text-gray-400 mr-2" />
            <div>
              <p className="text-sm font-medium text-gray-900">
                {selectedFile.name}
              </p>
              <p className="text-xs text-gray-500">
                {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
              </p>
            </div>
          </div>
          {!loading && (
            <button
              onClick={() => onFileSelect(null, null)}
              className="p-1 hover:bg-gray-200 rounded"
            >
              <X className="h-4 w-4 text-gray-500" />
            </button>
          )}
        </div>
      )}

      {/* Error display */}
      {error && (
        <div className="flex items-center p-3 bg-red-50 border border-red-200 rounded-lg">
          <AlertCircle className="h-5 w-5 text-red-500 mr-2" />
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}
    </div>
  );
};

export default FileUpload;