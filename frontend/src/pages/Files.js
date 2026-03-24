import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import apiService from '../services/api';
import LoadingSpinner from '../components/LoadingSpinner';
import { 
  FileText, 
  Upload, 
  Trash2, 
  Download, 
  Eye, 
  Calendar,
  Search,
  Filter,
  MoreVertical,
  AlertCircle
} from 'lucide-react';

const Files = () => {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState('date'); // date, name, size
  const [sortOrder, setSortOrder] = useState('desc'); // asc, desc
  const [selectedFiles, setSelectedFiles] = useState(new Set());
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    loadFiles();
  }, []);

  const loadFiles = async () => {
    try {
      const response = await apiService.getUploadedFiles();
      // API returns { files: [...], total_count: N }
      const filesData = response.data?.files || response.data || [];
      setFiles(Array.isArray(filesData) ? filesData : []);
    } catch (error) {
      console.error('Failed to load files:', error);
      setError('Failed to load files. Please try again.');
      setFiles([]); // Ensure files is always an array
    } finally {
      setLoading(false);
    }
  };

  const handleFileSelect = (fileId) => {
    const newSelected = new Set(selectedFiles);
    if (newSelected.has(fileId)) {
      newSelected.delete(fileId);
    } else {
      newSelected.add(fileId);
    }
    setSelectedFiles(newSelected);
  };

  const handleSelectAll = () => {
    if (selectedFiles.size === filteredFiles.length) {
      setSelectedFiles(new Set());
    } else {
      setSelectedFiles(new Set(filteredFiles.map(f => f.file_id || f.id)));
    }
  };

  const handleDelete = async (fileIds) => {
    try {
      // Mock delete - in real app, make API calls
      await Promise.all(
        Array.from(fileIds).map(id => 
          apiService.deleteFile ? apiService.deleteFile(id) : Promise.resolve()
        )
      );
      
      setFiles(files.filter(f => !fileIds.has(f.file_id || f.id)));
      setSelectedFiles(new Set());
      setShowDeleteModal(false);
    } catch (error) {
      console.error('Failed to delete files:', error);
      setError('Failed to delete files. Please try again.');
    }
  };

  const handleDownload = async (fileId) => {
    try {
      // Mock download - in real app, make API call
      if (apiService.downloadFile) {
        await apiService.downloadFile(fileId);
      } else {
        // Fallback for demo
        const file = files.find(f => (f.file_id || f.id) === fileId);
        if (file) {
          alert(`Download would start for: ${file.filename}`);
        }
      }
    } catch (error) {
      console.error('Failed to download file:', error);
      setError('Failed to download file. Please try again.');
    }
  };

  const formatFileSize = (bytes) => {
    if (!bytes) return 'Unknown size';
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
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

  // Filter and sort files
  const filteredFiles = (Array.isArray(files) ? files : [])
    .filter(file => 
      file.filename?.toLowerCase().includes(searchTerm.toLowerCase())
    )
    .sort((a, b) => {
      let aVal, bVal;
      
      switch (sortBy) {
        case 'name':
          aVal = (a.filename || '').toLowerCase();
          bVal = (b.filename || '').toLowerCase();
          break;
        case 'size':
          aVal = a.file_size || a.size || 0;
          bVal = b.file_size || b.size || 0;
          break;
        case 'date':
        default:
          aVal = new Date(a.upload_timestamp || a.uploaded_at || 0);
          bVal = new Date(b.upload_timestamp || b.uploaded_at || 0);
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
          <h1 className="text-3xl font-bold text-gray-900">My Files</h1>
          <p className="mt-2 text-gray-600">
            Manage your uploaded resume files
          </p>
        </div>
        <div className="mt-4 sm:mt-0">
          <Link
            to="/upload"
            className="btn-primary flex items-center"
          >
            <Upload className="w-4 h-4 mr-2" />
            Upload Resume
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

      {files.length === 0 ? (
        <div className="text-center py-12">
          <FileText className="mx-auto h-16 w-16 text-gray-400" />
          <h3 className="mt-4 text-lg font-medium text-gray-900">No files uploaded</h3>
          <p className="mt-2 text-gray-600">
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
      ) : (
        <>
          {/* Search and Filter Controls */}
          <div className="bg-white shadow rounded-lg mb-6">
            <div className="p-6">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-4 sm:space-y-0">
                <div className="relative flex-1 max-w-md">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Search files..."
                    className="input pl-10"
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                  />
                </div>
                
                <div className="flex items-center space-x-4">
                  <div className="flex items-center space-x-2">
                    <Filter className="h-5 w-5 text-gray-400" />
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
                      <option value="name-asc">Name A-Z</option>
                      <option value="name-desc">Name Z-A</option>
                      <option value="size-desc">Largest First</option>
                      <option value="size-asc">Smallest First</option>
                    </select>
                  </div>
                  
                  {selectedFiles.size > 0 && (
                    <button
                      onClick={() => setShowDeleteModal(true)}
                      className="btn-secondary text-red-600 hover:text-red-700 hover:bg-red-50"
                    >
                      <Trash2 className="w-4 h-4 mr-2" />
                      Delete ({selectedFiles.size})
                    </button>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Files Table */}
          <div className="bg-white shadow rounded-lg overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left">
                    <input
                      type="checkbox"
                      className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                      checked={selectedFiles.size === filteredFiles.length && filteredFiles.length > 0}
                      onChange={handleSelectAll}
                    />
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    File
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Size
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Uploaded
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredFiles.map((file) => (
                  <tr key={file.file_id || file.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4">
                      <input
                        type="checkbox"
                        className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                        checked={selectedFiles.has(file.file_id || file.id)}
                        onChange={() => handleFileSelect(file.file_id || file.id)}
                      />
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center">
                        <FileText className="h-5 w-5 text-gray-400 mr-3" />
                        <div>
                          <div className="text-sm font-medium text-gray-900">
                            {file.filename}
                          </div>
                          <div className="text-sm text-gray-500">
                            {file.content_type || file.type || 'Unknown type'}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900">
                      {formatFileSize(file.file_size || file.size)}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900">
                      <div className="flex items-center">
                        <Calendar className="h-4 w-4 text-gray-400 mr-2" />
                        {formatDate(file.upload_timestamp || file.uploaded_at)}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-sm font-medium">
                      <div className="flex items-center space-x-2">
                        <button
                          onClick={() => {/* Navigate to preview */}}
                          className="text-primary-600 hover:text-primary-900"
                          title="Preview"
                        >
                          <Eye className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => handleDownload(file.file_id || file.id)}
                          className="text-gray-600 hover:text-gray-900"
                          title="Download"
                        >
                          <Download className="h-4 w-4" />
                        </button>
                        <Link
                          to={`/upload?file=${file.file_id || file.id}`}
                          className="text-green-600 hover:text-green-900"
                          title="Analyze"
                        >
                          <Upload className="h-4 w-4" />
                        </Link>
                        <button
                          onClick={() => setShowDeleteModal(true)}
                          className="text-red-600 hover:text-red-900"
                          title="Delete"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Results count */}
          <div className="mt-4 text-sm text-gray-600">
            Showing {filteredFiles.length} of {files.length} files
          </div>
        </>
      )}

      {/* Delete Confirmation Modal */}
      {showDeleteModal && (
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-medium text-gray-900 mb-4">
              Confirm Delete
            </h3>
            <p className="text-sm text-gray-600 mb-6">
              Are you sure you want to delete {selectedFiles.size} selected file(s)? 
              This action cannot be undone.
            </p>
            <div className="flex justify-end space-x-4">
              <button
                onClick={() => setShowDeleteModal(false)}
                className="btn-secondary"
              >
                Cancel
              </button>
              <button
                onClick={() => handleDelete(selectedFiles)}
                className="btn-primary bg-red-600 hover:bg-red-700"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Files;