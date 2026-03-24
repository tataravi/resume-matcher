import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import apiService from '../services/api';
import FileUpload from '../components/FileUpload';
import LoadingSpinner from '../components/LoadingSpinner';
import { 
  Upload as UploadIcon, 
  CheckCircle, 
  ArrowRight,
  FileText,
  AlertCircle 
} from 'lucide-react';

const Upload = () => {
  const navigate = useNavigate();
  const [selectedFile, setSelectedFile] = useState(null);
  const [jobDescription, setJobDescription] = useState('');
  const [jobTitle, setJobTitle] = useState('');
  const [company, setCompany] = useState('');
  const [uploadLoading, setUploadLoading] = useState(false);
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [uploadedFile, setUploadedFile] = useState(null);
  const [error, setError] = useState('');
  const [step, setStep] = useState(1); // 1: upload, 2: job description, 3: analysis

  const handleFileSelect = (file, error) => {
    if (error) {
      setError(error);
      setSelectedFile(null);
    } else {
      setError('');
      setSelectedFile(file);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    setUploadLoading(true);
    setError('');

    try {
      const response = await apiService.uploadResume(selectedFile);
      setUploadedFile(response.data);
      setStep(2);
    } catch (error) {
      setError(
        error.response?.data?.detail || 
        'Failed to upload file. Please try again.'
      );
    } finally {
      setUploadLoading(false);
    }
  };

  const handleStartAnalysis = async () => {
    if (!uploadedFile) return;

    setAnalysisLoading(true);
    setError('');

    try {
      const response = await apiService.startAnalysisFromFile({
        file_id: uploadedFile.file_id,
        job_title: jobTitle.trim() || 'General Position',
        company: company.trim() || 'Company',
        job_description: jobDescription.trim() || 'No specific job description provided.'
      });

      navigate(`/analyses/${response.data.analysis_id}`);
    } catch (error) {
      setError(
        error.response?.data?.detail || 
        'Failed to start analysis. Please try again.'
      );
    } finally {
      setAnalysisLoading(false);
    }
  };

  const resetUpload = () => {
    setSelectedFile(null);
    setJobDescription('');
    setJobTitle('');
    setCompany('');
    setUploadedFile(null);
    setError('');
    setStep(1);
  };

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Upload Resume</h1>
        <p className="mt-2 text-gray-600">
          Upload your resume and get AI-powered insights and improvements
        </p>
      </div>

      {/* Progress Steps */}
      <div className="mb-8">
        <div className="flex items-center justify-center">
          <div className="flex items-center space-x-4">
            {/* Step 1 */}
            <div className="flex items-center">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center border-2 ${
                step >= 1 
                  ? 'bg-primary-600 border-primary-600 text-white' 
                  : 'border-gray-300 text-gray-300'
              }`}>
                {step > 1 ? (
                  <CheckCircle className="w-5 h-5" />
                ) : (
                  <span>1</span>
                )}
              </div>
              <span className="ml-2 text-sm font-medium text-gray-700">Upload File</span>
            </div>

            <ArrowRight className="w-5 h-5 text-gray-400" />

            {/* Step 2 */}
            <div className="flex items-center">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center border-2 ${
                step >= 2 
                  ? 'bg-primary-600 border-primary-600 text-white' 
                  : 'border-gray-300 text-gray-300'
              }`}>
                {step > 2 ? (
                  <CheckCircle className="w-5 h-5" />
                ) : (
                  <span>2</span>
                )}
              </div>
              <span className="ml-2 text-sm font-medium text-gray-700">Job Details</span>
            </div>

            <ArrowRight className="w-5 h-5 text-gray-400" />

            {/* Step 3 */}
            <div className="flex items-center">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center border-2 ${
                step >= 3 
                  ? 'bg-primary-600 border-primary-600 text-white' 
                  : 'border-gray-300 text-gray-300'
              }`}>
                <span>3</span>
              </div>
              <span className="ml-2 text-sm font-medium text-gray-700">Analysis</span>
            </div>
          </div>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center">
            <AlertCircle className="h-5 w-5 text-red-500 mr-3" />
            <p className="text-sm text-red-700">{error}</p>
          </div>
        </div>
      )}

      <div className="bg-white shadow rounded-lg">
        <div className="p-6">
          {/* Step 1: File Upload */}
          {step === 1 && (
            <div>
              <h2 className="text-xl font-semibold text-gray-900 mb-6">
                Step 1: Upload Your Resume
              </h2>
              
              <FileUpload
                onFileSelect={handleFileSelect}
                loading={uploadLoading}
                error={error}
              />

              <div className="mt-6 flex justify-between items-center">
                <div className="text-sm text-gray-600">
                  <p>Supported formats: PDF, TXT</p>
                  <p>Maximum file size: 10MB</p>
                </div>
                
                {selectedFile && (
                  <button
                    onClick={handleUpload}
                    disabled={uploadLoading}
                    className="btn-primary flex items-center disabled:opacity-50"
                  >
                    {uploadLoading ? (
                      <LoadingSpinner size="sm" className="mr-2" />
                    ) : (
                      <UploadIcon className="w-4 h-4 mr-2" />
                    )}
                    Upload Resume
                  </button>
                )}
              </div>
            </div>
          )}

          {/* Step 2: Job Details */}
          {step === 2 && (
            <div>
              <h2 className="text-xl font-semibold text-gray-900 mb-6">
                Step 2: Job Details
              </h2>

              {/* Uploaded File Info */}
              <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg">
                <div className="flex items-center">
                  <CheckCircle className="h-5 w-5 text-green-500 mr-3" />
                  <div>
                    <p className="text-sm font-medium text-green-800">
                      File uploaded successfully
                    </p>
                    <p className="text-sm text-green-600">
                      {uploadedFile?.filename} ({uploadedFile?.size ? 
                        `${(uploadedFile.size / 1024).toFixed(1)} KB` : 'Size unknown'})
                    </p>
                  </div>
                </div>
              </div>

              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label htmlFor="jobTitle" className="label">
                      Job Title <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="text"
                      id="jobTitle"
                      className="input"
                      placeholder="e.g., Senior Software Engineer"
                      value={jobTitle}
                      onChange={(e) => setJobTitle(e.target.value)}
                    />
                  </div>
                  <div>
                    <label htmlFor="company" className="label">
                      Company Name <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="text"
                      id="company"
                      className="input"
                      placeholder="e.g., Google, Microsoft"
                      value={company}
                      onChange={(e) => setCompany(e.target.value)}
                    />
                  </div>
                </div>
                <div>
                  <label htmlFor="jobDescription" className="label">
                    Job Description (Optional)
                  </label>
                  <textarea
                    id="jobDescription"
                    rows={8}
                    className="input"
                    placeholder="Paste the job description here to get more targeted feedback and matching analysis..."
                    value={jobDescription}
                    onChange={(e) => setJobDescription(e.target.value)}
                  />
                  <p className="mt-2 text-sm text-gray-600">
                    Providing a job description helps our AI give more specific feedback 
                    on how well your resume matches the position requirements.
                  </p>
                </div>

                <div className="flex justify-between items-center">
                  <button
                    onClick={resetUpload}
                    className="btn-secondary"
                  >
                    Upload Different File
                  </button>

                  <div className="flex space-x-3">
                    <button
                      onClick={handleStartAnalysis}
                      disabled={analysisLoading || !jobTitle.trim() || !company.trim()}
                      className="btn-primary flex items-center disabled:opacity-50"
                    >
                      {analysisLoading ? (
                        <LoadingSpinner size="sm" className="mr-2" />
                      ) : (
                        <UploadIcon className="w-4 h-4 mr-2" />
                      )}
                      Start Analysis
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Tips Section */}
      <div className="mt-8 bg-blue-50 rounded-lg p-6">
        <h3 className="text-lg font-medium text-blue-900 mb-4">Tips for Better Analysis</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-blue-800">
          <div className="flex items-start">
            <FileText className="w-5 h-5 text-blue-600 mr-2 mt-0.5" />
            <div>
              <p className="font-medium">Use a well-formatted resume</p>
              <p>Clear sections and consistent formatting help our AI understand your content better.</p>
            </div>
          </div>
          <div className="flex items-start">
            <CheckCircle className="w-5 h-5 text-blue-600 mr-2 mt-0.5" />
            <div>
              <p className="font-medium">Include a job description</p>
              <p>Get targeted feedback on how well your resume matches specific job requirements.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Upload;