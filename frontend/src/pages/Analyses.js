import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import apiService from '../services/api';
import LoadingSpinner from '../components/LoadingSpinner';
import { 
  BarChart3, 
  CheckCircle, 
  Clock, 
  AlertCircle, 
  Eye, 
  Trash2, 
  Search,
  Filter,
  Calendar,
  FileText,
  TrendingUp,
  Star
} from 'lucide-react';

const Analyses = () => {
  const navigate = useNavigate();
  const [analyses, setAnalyses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [sortBy, setSortBy] = useState('date');
  const [sortOrder, setSortOrder] = useState('desc');
  const [error, setError] = useState('');

  useEffect(() => {
    loadAnalyses();
  }, []);

  const loadAnalyses = async () => {
    try {
      const response = await apiService.getAnalyses();
      // API returns { analyses: [...], total_count: N }
      const analysesData = response.data?.analyses || response.data || [];
      setAnalyses(Array.isArray(analysesData) ? analysesData : []);
    } catch (error) {
      console.error('Failed to load analyses:', error);
      setError('Failed to load analyses. Please try again.');
      setAnalyses([]); // Ensure analyses is always an array
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (analysisId) => {
    try {
      if (apiService.deleteAnalysis) {
        await apiService.deleteAnalysis(analysisId);
      }
      setAnalyses(analyses.filter(a => (a.analysis_id || a.id) !== analysisId));
    } catch (error) {
      console.error('Failed to delete analysis:', error);
      setError('Failed to delete analysis. Please try again.');
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

  const getScoreColor = (score) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Unknown date';
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // Filter and sort analyses
  const filteredAnalyses = (Array.isArray(analyses) ? analyses : [])
    .filter(analysis => {
      const matchesSearch = analysis.filename?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           analysis.analysis_id?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           analysis.id?.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesStatus = statusFilter === 'all' || analysis.status === statusFilter;
      return matchesSearch && matchesStatus;
    })
    .sort((a, b) => {
      let aVal, bVal;
      
      switch (sortBy) {
        case 'score':
          aVal = a.results?.overall_score || 0;
          bVal = b.results?.overall_score || 0;
          break;
        case 'status':
          aVal = a.status;
          bVal = b.status;
          break;
        case 'filename':
          aVal = a.filename || '';
          bVal = b.filename || '';
          break;
        case 'date':
        default:
          aVal = new Date(a.start_time || a.created_at || 0);
          bVal = new Date(b.start_time || b.created_at || 0);
          break;
      }
      
      if (sortOrder === 'asc') {
        return aVal < bVal ? -1 : aVal > bVal ? 1 : 0;
      } else {
        return aVal > bVal ? -1 : aVal < bVal ? 1 : 0;
      }
    });

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <div className="px-4 sm:px-6 lg:px-8">
      {/* Header */}
      <div className="sm:flex sm:items-center sm:justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Analyses</h1>
          <p className="mt-2 text-gray-600">
            View and manage your resume analysis results
          </p>
        </div>
        <div className="mt-4 sm:mt-0">
          <Link
            to="/upload"
            className="btn-primary flex items-center"
          >
            <BarChart3 className="w-4 h-4 mr-2" />
            New Analysis
          </Link>
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

      {analyses.length === 0 ? (
        <div className="text-center py-12">
          <BarChart3 className="mx-auto h-16 w-16 text-gray-400" />
          <h3 className="mt-4 text-lg font-medium text-gray-900">No analyses yet</h3>
          <p className="mt-2 text-gray-600">
            Upload a resume to get your first AI-powered analysis
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
      ) : (
        <>
          {/* Search and Filter Controls */}
          <div className="bg-white shadow rounded-lg mb-6">
            <div className="p-6">
              <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between space-y-4 lg:space-y-0">
                <div className="relative flex-1 max-w-md">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Search analyses..."
                    className="input pl-10"
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                  />
                </div>
                
                <div className="flex flex-col sm:flex-row sm:items-center space-y-4 sm:space-y-0 sm:space-x-4">
                  <div className="flex items-center space-x-2">
                    <Filter className="h-5 w-5 text-gray-400" />
                    <select
                      className="input min-w-0"
                      value={statusFilter}
                      onChange={(e) => setStatusFilter(e.target.value)}
                    >
                      <option value="all">All Status</option>
                      <option value="completed">Completed</option>
                      <option value="processing">Processing</option>
                      <option value="failed">Failed</option>
                    </select>
                  </div>
                  
                  <select
                    className="input min-w-0"
                    value={`${sortBy}-${sortOrder}`}
                    onChange={(e) => {
                      const [sort, order] = e.target.value.split('-');
                      setSortBy(sort);
                      setSortOrder(order);
                    }}
                  >
                    <option value="date-desc">Newest First</option>
                    <option value="date-asc">Oldest First</option>
                    <option value="score-desc">Highest Score</option>
                    <option value="score-asc">Lowest Score</option>
                    <option value="status-asc">Status A-Z</option>
                    <option value="filename-asc">Filename A-Z</option>
                  </select>
                </div>
              </div>
            </div>
          </div>

          {/* Analyses Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {filteredAnalyses.map((analysis) => (
              <div key={analysis.analysis_id || analysis.id} className="bg-white shadow rounded-lg overflow-hidden">
                <div className="p-6">
                  {/* Header */}
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center">
                      {getStatusIcon(analysis.status)}
                      <div className="ml-3">
                        <h3 className="text-lg font-medium text-gray-900">
                          {analysis.filename || `Analysis #${(analysis.analysis_id || analysis.id || '').slice(0, 8)}`}
                        </h3>
                        <p className="text-sm text-gray-500">
                          {formatDate(analysis.start_time || analysis.created_at)}
                        </p>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(analysis.status)}`}>
                        {analysis.status}
                      </span>
                    </div>
                  </div>

                  {/* Score and Metrics */}
                  {analysis.status === 'completed' && analysis.results && (
                    <div className="mb-4">
                      <div className="flex items-center justify-between mb-3">
                        <span className="text-sm font-medium text-gray-700">Overall Score</span>
                        <span className={`text-2xl font-bold ${getScoreColor(analysis.results.overall_score)}`}>
                          {analysis.results.overall_score}/100
                        </span>
                      </div>
                      
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div className="flex items-center">
                          <TrendingUp className="h-4 w-4 text-blue-500 mr-2" />
                          <span className="text-gray-600">
                            Skills: {analysis.results.skills_score || 0}/100
                          </span>
                        </div>
                        <div className="flex items-center">
                          <Star className="h-4 w-4 text-yellow-500 mr-2" />
                          <span className="text-gray-600">
                            Experience: {analysis.results.experience_score || 0}/100
                          </span>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Processing Status */}
                  {analysis.status === 'processing' && (
                    <div className="mb-4">
                      <div className="flex items-center">
                        <LoadingSpinner size="sm" className="mr-3" />
                        <span className="text-sm text-gray-600">
                          Analysis in progress...
                        </span>
                      </div>
                    </div>
                  )}

                  {/* Error Status */}
                  {analysis.status === 'failed' && (
                    <div className="mb-4 p-3 bg-red-50 rounded-lg">
                      <div className="flex items-center">
                        <AlertCircle className="h-5 w-5 text-red-500 mr-2" />
                        <span className="text-sm text-red-700">
                          Analysis failed. Please try again.
                        </span>
                      </div>
                    </div>
                  )}

                  {/* Key Insights Preview */}
                  {analysis.status === 'completed' && analysis.results?.key_insights && (
                    <div className="mb-4">
                      <h4 className="text-sm font-medium text-gray-700 mb-2">Key Insights</h4>
                      <ul className="text-sm text-gray-600 space-y-1">
                        {analysis.results.key_insights.slice(0, 2).map((insight, index) => (
                          <li key={index} className="flex items-start">
                            <span className="w-2 h-2 bg-primary-500 rounded-full mt-2 mr-3 flex-shrink-0"></span>
                            <span className="line-clamp-2">{insight}</span>
                          </li>
                        ))}
                        {analysis.results.key_insights.length > 2 && (
                          <li className="text-primary-600 font-medium">
                            +{analysis.results.key_insights.length - 2} more insights
                          </li>
                        )}
                      </ul>
                    </div>
                  )}

                  {/* Actions */}
                  <div className="flex items-center justify-between pt-4 border-t border-gray-200">
                    <div className="flex items-center space-x-4">
                      {analysis.status === 'completed' && (
                        <button
                          onClick={() => navigate(`/analyses/${analysis.analysis_id || analysis.id}`)}
                          className="flex items-center text-primary-600 hover:text-primary-700 text-sm font-medium"
                        >
                          <Eye className="h-4 w-4 mr-1" />
                          View Results
                        </button>
                      )}
                      
                      {analysis.status === 'failed' && (
                        <Link
                          to="/upload"
                          className="flex items-center text-green-600 hover:text-green-700 text-sm font-medium"
                        >
                          <BarChart3 className="h-4 w-4 mr-1" />
                          Retry Analysis
                        </Link>
                      )}
                    </div>

                    <button
                      onClick={() => handleDelete(analysis.analysis_id || analysis.id)}
                      className="text-red-600 hover:text-red-700"
                      title="Delete Analysis"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Results count */}
          <div className="mt-6 text-sm text-gray-600">
            Showing {filteredAnalyses.length} of {analyses.length} analyses
          </div>
        </>
      )}
    </div>
  );
};

export default Analyses;