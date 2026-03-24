import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import apiService from '../services/api';
import LoadingSpinner from '../components/LoadingSpinner';
import { 
  Upload, 
  FileText, 
  BarChart3, 
  CheckCircle, 
  Clock, 
  AlertCircle,
  TrendingUp,
  Star,
  Calendar
} from 'lucide-react';

const Dashboard = () => {
  const { user } = useAuth();
  const [stats, setStats] = useState({
    totalFiles: 0,
    totalAnalyses: 0,
    completedAnalyses: 0,
    pendingAnalyses: 0
  });
  const [recentFiles, setRecentFiles] = useState([]);
  const [recentAnalyses, setRecentAnalyses] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      const [filesResponse, analysesResponse] = await Promise.all([
        apiService.getUploadedFiles(),
        apiService.getAnalyses()
      ]);

      const files = filesResponse.data || [];
      const analyses = analysesResponse.data || [];

      setStats({
        totalFiles: files.length,
        totalAnalyses: analyses.length,
        completedAnalyses: analyses.filter(a => a.status === 'completed').length,
        pendingAnalyses: analyses.filter(a => a.status === 'processing').length
      });

      setRecentFiles(files.slice(0, 5));
      setRecentAnalyses(analyses.slice(0, 5));
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'processing':
        return <Clock className="h-5 w-5 text-yellow-500" />;
      case 'failed':
        return <AlertCircle className="h-5 w-5 text-red-500" />;
      default:
        return <Clock className="h-5 w-5 text-gray-500" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'processing':
        return 'bg-yellow-100 text-yellow-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <div className="px-4 sm:px-6 lg:px-8">
      {/* Welcome Section */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">
          Welcome back, {user?.email?.split('@')[0] || 'Demo User'}!
        </h1>
        <p className="mt-2 text-gray-600">
          Here's what's happening with your resume analyses
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <FileText className="h-6 w-6 text-gray-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Total Files
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {stats.totalFiles}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <BarChart3 className="h-6 w-6 text-gray-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Total Analyses
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {stats.totalAnalyses}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <CheckCircle className="h-6 w-6 text-green-500" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Completed
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {stats.completedAnalyses}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <Clock className="h-6 w-6 text-yellow-500" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Processing
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {stats.pendingAnalyses}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-white shadow rounded-lg mb-8">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">Quick Actions</h3>
        </div>
        <div className="p-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            <Link
              to="/upload"
              className="flex items-center p-4 bg-primary-50 rounded-lg hover:bg-primary-100 transition-colors"
            >
              <Upload className="h-8 w-8 text-primary-600 mr-4" />
              <div>
                <h4 className="font-medium text-gray-900">Upload Resume</h4>
                <p className="text-sm text-gray-600">Upload a new resume for analysis</p>
              </div>
            </Link>

            <Link
              to="/files"
              className="flex items-center p-4 bg-blue-50 rounded-lg hover:bg-blue-100 transition-colors"
            >
              <FileText className="h-8 w-8 text-blue-600 mr-4" />
              <div>
                <h4 className="font-medium text-gray-900">Manage Files</h4>
                <p className="text-sm text-gray-600">View and organize your files</p>
              </div>
            </Link>

            <Link
              to="/analyses"
              className="flex items-center p-4 bg-green-50 rounded-lg hover:bg-green-100 transition-colors"
            >
              <BarChart3 className="h-8 w-8 text-green-600 mr-4" />
              <div>
                <h4 className="font-medium text-gray-900">View Analyses</h4>
                <p className="text-sm text-gray-600">Check your analysis results</p>
              </div>
            </Link>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Recent Files */}
        <div className="bg-white shadow rounded-lg">
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-medium text-gray-900">Recent Files</h3>
              <Link
                to="/files"
                className="text-sm font-medium text-primary-600 hover:text-primary-500"
              >
                View all
              </Link>
            </div>
          </div>
          <div className="p-6">
            {recentFiles.length > 0 ? (
              <div className="space-y-4">
                {recentFiles.map((file) => (
                  <div key={file.id} className="flex items-center justify-between">
                    <div className="flex items-center">
                      <FileText className="h-5 w-5 text-gray-400 mr-3" />
                      <div>
                        <p className="text-sm font-medium text-gray-900">
                          {file.filename}
                        </p>
                        <p className="text-xs text-gray-500">
                          {file.size && `${(file.size / 1024).toFixed(1)} KB`}
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-xs text-gray-500">
                        {file.uploaded_at && formatDate(file.uploaded_at)}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <FileText className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-2 text-sm font-medium text-gray-900">No files uploaded</h3>
                <p className="mt-1 text-sm text-gray-500">
                  Get started by uploading your first resume
                </p>
                <div className="mt-6">
                  <Link
                    to="/upload"
                    className="btn-primary"
                  >
                    Upload Resume
                  </Link>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Recent Analyses */}
        <div className="bg-white shadow rounded-lg">
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-medium text-gray-900">Recent Analyses</h3>
              <Link
                to="/analyses"
                className="text-sm font-medium text-primary-600 hover:text-primary-500"
              >
                View all
              </Link>
            </div>
          </div>
          <div className="p-6">
            {recentAnalyses.length > 0 ? (
              <div className="space-y-4">
                {recentAnalyses.map((analysis) => (
                  <div key={analysis.id} className="flex items-center justify-between">
                    <div className="flex items-center">
                      {getStatusIcon(analysis.status)}
                      <div className="ml-3">
                        <p className="text-sm font-medium text-gray-900">
                          Analysis #{analysis.id.slice(0, 8)}
                        </p>
                        <p className="text-xs text-gray-500">
                          {analysis.filename || 'Resume analysis'}
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(analysis.status)}`}>
                        {analysis.status}
                      </span>
                      <p className="text-xs text-gray-500 mt-1">
                        {analysis.created_at && formatDate(analysis.created_at)}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <BarChart3 className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-2 text-sm font-medium text-gray-900">No analyses yet</h3>
                <p className="mt-1 text-sm text-gray-500">
                  Upload a resume to get your first analysis
                </p>
                <div className="mt-6">
                  <Link
                    to="/upload"
                    className="btn-primary"
                  >
                    Start Analysis
                  </Link>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;