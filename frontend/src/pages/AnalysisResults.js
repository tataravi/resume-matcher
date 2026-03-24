import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import apiService from '../services/api';
import LoadingSpinner from '../components/LoadingSpinner';
import { 
  ArrowLeft,
  Download,
  Share2,
  CheckCircle,
  AlertCircle,
  TrendingUp,
  Star,
  Target,
  BookOpen,
  Award,
  FileText,
  BarChart3,
  Clock,
  Eye,
  ThumbsUp,
  ThumbsDown,
  RefreshCw
} from 'lucide-react';

const AnalysisResults = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    loadAnalysis();
  }, [id]);

  const loadAnalysis = async () => {
    try {
      // First try to get status
      const statusResponse = await apiService.getAnalysisStatus(id);
      
      if (statusResponse.data.status === 'completed') {
        // Only try to get results if analysis is completed
        const resultsResponse = await apiService.getAnalysisResults(id);
        
        setAnalysis({
          ...statusResponse.data,
          results: resultsResponse.data.results || resultsResponse.data
        });
      } else {
        // For non-completed analyses, just use the status data
        setAnalysis(statusResponse.data);
      }
    } catch (error) {
      console.error('Failed to load analysis:', error);
      
      // If it's a 404 for results but we have status, that's ok for non-completed analyses
      if (error.response?.status === 400 || error.response?.status === 404) {
        try {
          const statusResponse = await apiService.getAnalysisStatus(id);
          setAnalysis(statusResponse.data);
        } catch (statusError) {
          setError('Analysis not found or access denied.');
        }
      } else {
        setError('Failed to load analysis. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const getScoreColor = (score) => {
    if (score >= 80) return 'text-green-600 bg-green-100';
    if (score >= 60) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  const getScoreDescription = (score) => {
    if (score >= 80) return 'Excellent';
    if (score >= 60) return 'Good';
    return 'Needs Improvement';
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Unknown date';
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'long',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (error || !analysis) {
    return (
      <div className="px-4 sm:px-6 lg:px-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <div className="flex items-center">
            <AlertCircle className="h-8 w-8 text-red-500 mr-4" />
            <div>
              <h3 className="text-lg font-medium text-red-800">
                Analysis Not Found
              </h3>
              <p className="text-red-600 mt-1">
                {error || 'The requested analysis could not be found.'}
              </p>
              <div className="mt-4">
                <Link
                  to="/analyses"
                  className="btn-secondary"
                >
                  Back to Analyses
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const { results } = analysis;

  return (
    <div className="px-4 sm:px-6 lg:px-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <button
              onClick={() => navigate('/analyses')}
              className="mr-4 p-2 hover:bg-gray-100 rounded-lg"
            >
              <ArrowLeft className="h-5 w-5 text-gray-600" />
            </button>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                Analysis Results
              </h1>
              <p className="mt-2 text-gray-600">
                {analysis.filename || `Analysis #${id.slice(0, 8)}`} • {formatDate(analysis.created_at)}
              </p>
            </div>
          </div>
          
          <div className="flex items-center space-x-3">
            <button className="btn-secondary flex items-center">
              <Share2 className="w-4 h-4 mr-2" />
              Share
            </button>
            <button className="btn-secondary flex items-center">
              <Download className="w-4 h-4 mr-2" />
              Export PDF
            </button>
          </div>
        </div>
      </div>

      {analysis.status !== 'completed' ? (
        <div className="bg-white shadow rounded-lg p-6">
          {analysis.status === 'processing' && (
            <div className="text-center py-12">
              <LoadingSpinner size="lg" className="mb-4" />
              <h3 className="text-lg font-medium text-gray-900">Analysis in Progress</h3>
              <p className="text-gray-600 mt-2">
                Please wait while we analyze your resume...
              </p>
              <button
                onClick={loadAnalysis}
                className="btn-secondary mt-6 flex items-center mx-auto"
              >
                <RefreshCw className="w-4 h-4 mr-2" />
                Refresh Status
              </button>
            </div>
          )}

          {analysis.status === 'failed' && (
            <div className="text-center py-12">
              <AlertCircle className="mx-auto h-16 w-16 text-red-500 mb-4" />
              <h3 className="text-lg font-medium text-gray-900">Analysis Failed</h3>
              <p className="text-gray-600 mt-2">
                Something went wrong while analyzing your resume.
              </p>
              <div className="mt-6 space-x-4">
                <Link to="/upload" className="btn-primary">
                  Try Again
                </Link>
                <button
                  onClick={loadAnalysis}
                  className="btn-secondary flex items-center"
                >
                  <RefreshCw className="w-4 h-4 mr-2" />
                  Check Again
                </button>
              </div>
            </div>
          )}
        </div>
      ) : (
        <>
          {/* Score Overview */}
          <div className="bg-white shadow rounded-lg mb-8">
            <div className="p-6">
              <div className="text-center mb-8">
                <div className={`inline-flex items-center justify-center w-24 h-24 rounded-full text-3xl font-bold ${getScoreColor(results?.job_match_analysis?.overall_match_score || 0)}`}>
                  {results?.job_match_analysis?.overall_match_score || 0}
                </div>
                <h2 className="mt-4 text-2xl font-bold text-gray-900">
                  Overall Match: {getScoreDescription(results?.job_match_analysis?.overall_match_score || 0)}
                </h2>
                <p className="text-gray-600">
                  Your resume has been analyzed for job compatibility
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="text-center">
                  <div className={`inline-flex items-center justify-center w-16 h-16 rounded-full text-xl font-semibold ${getScoreColor(85)}`}>
                    {results?.job_match_analysis?.overall_match_score || 85}
                  </div>
                  <h3 className="mt-3 text-lg font-medium text-gray-900">Job Match</h3>
                  <p className="text-sm text-gray-600">Overall compatibility score</p>
                </div>

                <div className="text-center">
                  <div className={`inline-flex items-center justify-center w-16 h-16 rounded-full text-xl font-semibold ${getScoreColor((results?.job_match_analysis?.matching_skills?.length || 0) * 20)}`}>
                    {(results?.job_match_analysis?.matching_skills?.length || 0) * 20}
                  </div>
                  <h3 className="mt-3 text-lg font-medium text-gray-900">Skills Match</h3>
                  <p className="text-sm text-gray-600">Matching skills found</p>
                </div>

                <div className="text-center">
                  <div className={`inline-flex items-center justify-center w-16 h-16 rounded-full text-xl font-semibold ${getScoreColor(results?.resume_analysis?.experience_level === "Senior (5+ years)" ? 90 : 70)}`}>
                    {results?.resume_analysis?.experience_level === "Senior (5+ years)" ? 90 : 70}
                  </div>
                  <h3 className="mt-3 text-lg font-medium text-gray-900">Experience</h3>
                  <p className="text-sm text-gray-600">Professional level</p>
                </div>
              </div>
            </div>
          </div>

          {/* Tabs */}
          <div className="bg-white shadow rounded-lg">
            <div className="border-b border-gray-200">
              <nav className="flex space-x-8 px-6">
                {[
                  { id: 'overview', name: 'Overview', icon: BarChart3 },
                  { id: 'strengths', name: 'Strengths', icon: ThumbsUp },
                  { id: 'improvements', name: 'Improvements', icon: Target },
                  { id: 'keywords', name: 'Keywords', icon: BookOpen },
                  { id: 'recommendations', name: 'Recommendations', icon: Award }
                ].map((tab) => {
                  const Icon = tab.icon;
                  return (
                    <button
                      key={tab.id}
                      onClick={() => setActiveTab(tab.id)}
                      className={`py-4 px-1 border-b-2 font-medium text-sm flex items-center ${
                        activeTab === tab.id
                          ? 'border-primary-500 text-primary-600'
                          : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                      }`}
                    >
                      <Icon className="w-4 h-4 mr-2" />
                      {tab.name}
                    </button>
                  );
                })}
              </nav>
            </div>

            <div className="p-6">
              {/* Overview Tab */}
              {activeTab === 'overview' && (
                <div className="space-y-6">
                  <div>
                    <h3 className="text-lg font-medium text-gray-900 mb-4">Key Insights</h3>
                    {results?.resume_analysis?.key_strengths?.length > 0 ? (
                      <ul className="space-y-3">
                        {results.resume_analysis.key_strengths.map((insight, index) => (
                          <li key={index} className="flex items-start">
                            <CheckCircle className="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                            <span className="text-gray-700">{insight}</span>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p className="text-gray-600">Resume analysis is being processed...</p>
                    )}
                  </div>

                  <div>
                    <h3 className="text-lg font-medium text-gray-900 mb-4">Analysis Summary</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div className="bg-blue-50 p-4 rounded-lg">
                        <div className="flex items-center mb-3">
                          <TrendingUp className="w-5 h-5 text-blue-600 mr-2" />
                          <h4 className="font-medium text-blue-900">Skills Analysis</h4>
                        </div>
                        <p className="text-sm text-blue-800">
                          {results?.resume_analysis?.skills_identified?.length > 0 
                            ? `Found ${results.resume_analysis.skills_identified.length} relevant skills including ${results.resume_analysis.skills_identified.slice(0,3).join(', ')}`
                            : 'Your skills are being analyzed for relevance and market demand.'}
                        </p>
                      </div>

                      <div className="bg-green-50 p-4 rounded-lg">
                        <div className="flex items-center mb-3">
                          <Star className="w-5 h-5 text-green-600 mr-2" />
                          <h4 className="font-medium text-green-900">Experience Review</h4>
                        </div>
                        <p className="text-sm text-green-800">
                          {results?.resume_analysis?.experience_level 
                            ? `Experience level: ${results.resume_analysis.experience_level}`
                            : 'Your professional experience is being evaluated for depth and relevance.'}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Strengths Tab */}
              {activeTab === 'strengths' && (
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Your Resume Strengths</h3>
                  {results?.feedback?.strengths?.length > 0 ? (
                    <div className="space-y-4">
                      {results.feedback.strengths.map((strength, index) => (
                        <div key={index} className="flex items-start p-4 bg-green-50 rounded-lg">
                          <ThumbsUp className="w-5 h-5 text-green-600 mr-3 mt-0.5 flex-shrink-0" />
                          <div>
                            <h4 className="font-medium text-green-900">Strength {index + 1}</h4>
                            <p className="text-sm text-green-800 mt-1">
                              {strength}
                            </p>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-8">
                      <Star className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                      <p className="text-gray-600">Analysis is processing your resume strengths...</p>
                    </div>
                  )}
                </div>
              )}

              {/* Improvements Tab */}
              {activeTab === 'improvements' && (
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Areas for Improvement</h3>
                  {results?.feedback?.improvements?.length > 0 ? (
                    <div className="space-y-4">
                      {results.feedback.improvements.map((improvement, index) => (
                        <div key={index} className="flex items-start p-4 bg-yellow-50 rounded-lg">
                          <Target className="w-5 h-5 text-yellow-600 mr-3 mt-0.5 flex-shrink-0" />
                          <div>
                            <h4 className="font-medium text-yellow-900">Improvement {index + 1}</h4>
                            <p className="text-sm text-yellow-800 mt-1">
                              {improvement}
                            </p>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : results?.job_match_analysis?.skill_gaps?.length > 0 ? (
                    <div className="space-y-4">
                      {results.job_match_analysis.skill_gaps.map((gap, index) => (
                        <div key={index} className="flex items-start p-4 bg-yellow-50 rounded-lg">
                          <Target className="w-5 h-5 text-yellow-600 mr-3 mt-0.5 flex-shrink-0" />
                          <div>
                            <h4 className="font-medium text-yellow-900">{gap.skill}</h4>
                            <p className="text-sm text-yellow-800 mt-1">
                              {gap.recommendation}
                            </p>
                            <span className={`inline-block px-2 py-1 rounded text-xs font-medium mt-2 ${
                              gap.importance === 'High' 
                                ? 'bg-red-100 text-red-800'
                                : gap.importance === 'Medium'
                                ? 'bg-yellow-100 text-yellow-800'
                                : 'bg-green-100 text-green-800'
                            }`}>
                              {gap.importance} priority
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-8">
                      <Target className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                      <p className="text-gray-600">Analysis is identifying improvement areas...</p>
                    </div>
                  )}
                </div>
              )}

              {/* Keywords Tab */}
              {activeTab === 'keywords' && (
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Skills & Keywords Analysis</h3>
                  <div className="space-y-6">
                    {results?.job_match_analysis?.matching_skills?.length > 0 && (
                      <div>
                        <h4 className="font-medium text-green-900 mb-3">Matching Skills</h4>
                        <div className="flex flex-wrap gap-2">
                          {results.job_match_analysis.matching_skills.map((skill, index) => (
                            <span key={index} className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800">
                              <CheckCircle className="w-3 h-3 mr-1" />
                              {skill}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {results?.job_match_analysis?.missing_skills?.length > 0 && (
                      <div>
                        <h4 className="font-medium text-red-900 mb-3">Missing Skills</h4>
                        <div className="flex flex-wrap gap-2">
                          {results.job_match_analysis.missing_skills.map((skill, index) => (
                            <span key={index} className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-red-100 text-red-800">
                              <AlertCircle className="w-3 h-3 mr-1" />
                              {skill}
                            </span>
                          ))}
                        </div>
                        <p className="text-sm text-gray-600 mt-3">
                          Consider adding these skills to improve your job match score.
                        </p>
                      </div>
                    )}

                    {results?.resume_analysis?.skills_identified?.length > 0 && (
                      <div>
                        <h4 className="font-medium text-blue-900 mb-3">Identified Skills</h4>
                        <div className="flex flex-wrap gap-2">
                          {results.resume_analysis.skills_identified.map((skill, index) => (
                            <span key={index} className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
                              <BookOpen className="w-3 h-3 mr-1" />
                              {skill}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Recommendations Tab */}
              {activeTab === 'recommendations' && (
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Personalized Recommendations</h3>
                  {results?.feedback?.recommendation ? (
                    <div className="space-y-4">
                      <div className="border border-gray-200 rounded-lg p-4">
                        <div className="flex items-start">
                          <Award className="w-5 h-5 text-primary-600 mr-3 mt-0.5 flex-shrink-0" />
                          <div className="flex-1">
                            <h4 className="font-medium text-gray-900">Overall Recommendation</h4>
                            <p className="text-sm text-gray-600 mt-1">
                              {results.feedback.recommendation}
                            </p>
                          </div>
                        </div>
                      </div>
                      
                      {results?.job_match_analysis?.skill_gaps?.length > 0 && (
                        <div>
                          <h4 className="font-medium text-gray-900 mb-3">Skill Development Recommendations</h4>
                          <div className="space-y-3">
                            {results.job_match_analysis.skill_gaps.map((gap, index) => (
                              <div key={index} className="border border-gray-200 rounded-lg p-4">
                                <div className="flex items-start">
                                  <BookOpen className="w-5 h-5 text-blue-600 mr-3 mt-0.5 flex-shrink-0" />
                                  <div className="flex-1">
                                    <h4 className="font-medium text-gray-900">{gap.skill}</h4>
                                    <p className="text-sm text-gray-600 mt-1">
                                      {gap.recommendation}
                                    </p>
                                    <span className={`inline-block px-2 py-1 rounded text-xs font-medium mt-2 ${
                                      gap.importance === 'High' 
                                        ? 'bg-red-100 text-red-800'
                                        : gap.importance === 'Medium'
                                        ? 'bg-yellow-100 text-yellow-800'
                                        : 'bg-green-100 text-green-800'
                                    }`}>
                                      {gap.importance} Priority
                                    </span>
                                  </div>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="text-center py-8">
                      <Award className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                      <p className="text-gray-600">Analysis is generating personalized recommendations...</p>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* Action Buttons */}
          <div className="mt-8 bg-white shadow rounded-lg p-6">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-4 sm:space-y-0">
              <div>
                <h3 className="text-lg font-medium text-gray-900">Next Steps</h3>
                <p className="text-sm text-gray-600">
                  Use these insights to improve your resume and increase your chances of success.
                </p>
              </div>
              <div className="flex space-x-4">
                <Link
                  to="/upload"
                  className="btn-secondary flex items-center"
                >
                  <FileText className="w-4 h-4 mr-2" />
                  Analyze New Resume
                </Link>
                <button className="btn-primary flex items-center">
                  <Download className="w-4 h-4 mr-2" />
                  Download Report
                </button>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default AnalysisResults;