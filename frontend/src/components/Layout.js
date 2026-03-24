import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { 
  FileText, 
  Upload, 
  BarChart3, 
  LogOut, 
  User,
  Menu,
  X
} from 'lucide-react';

const Layout = ({ children }) => {
  const { user, logout } = useAuth();
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = React.useState(false);

  const navigation = [
    { name: 'Dashboard', href: '/dashboard', icon: BarChart3 },
    { name: 'Upload Resume', href: '/upload', icon: Upload },
    { name: 'My Files', href: '/files', icon: FileText },
    { name: 'Analyses', href: '/analyses', icon: BarChart3 },
  ];


  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
      <nav className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex">
              <div className="flex-shrink-0 flex items-center">
                <FileText className="h-8 w-8 text-primary-600" />
                <span className="ml-2 text-xl font-bold text-gray-900">
                  Resume Analyzer
                </span>
              </div>
              <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
                {navigation.map((item) => {
                  const Icon = item.icon;
                  const isActive = location.pathname === item.href;
                  return (
                    <Link
                      key={item.name}
                      to={item.href}
                      className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${
                        isActive
                          ? 'border-primary-500 text-gray-900'
                          : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
                      }`}
                    >
                      <Icon className="h-4 w-4 mr-2" />
                      {item.name}
                    </Link>
                  );
                })}
              </div>
            </div>

            <div className="hidden sm:ml-6 sm:flex sm:items-center">
              <div className="flex items-center space-x-4">
                <div className="flex items-center text-sm text-gray-700">
                  <User className="h-4 w-4 mr-2" />
                  {user?.email || 'Demo User'}
                </div>
                <button
                  onClick={logout}
                  className="btn-secondary flex items-center"
                >
                  <LogOut className="h-4 w-4 mr-2" />
                  Logout
                </button>
              </div>
            </div>

            <div className="-mr-2 flex items-center sm:hidden">
              <button
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                className="inline-flex items-center justify-center p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100"
              >
                {mobileMenuOpen ? (
                  <X className="h-6 w-6" />
                ) : (
                  <Menu className="h-6 w-6" />
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Mobile menu */}
        {mobileMenuOpen && (
          <div className="sm:hidden">
            <div className="pt-2 pb-3 space-y-1">
              {navigation.map((item) => {
                const Icon = item.icon;
                const isActive = location.pathname === item.href;
                return (
                  <Link
                    key={item.name}
                    to={item.href}
                    className={`block pl-3 pr-4 py-2 border-l-4 text-base font-medium ${
                      isActive
                        ? 'bg-primary-50 border-primary-500 text-primary-700'
                        : 'border-transparent text-gray-500 hover:bg-gray-50 hover:border-gray-300 hover:text-gray-700'
                    }`}
                    onClick={() => setMobileMenuOpen(false)}
                  >
                    <div className="flex items-center">
                      <Icon className="h-4 w-4 mr-3" />
                      {item.name}
                    </div>
                  </Link>
                );
              })}
            </div>
            <div className="pt-4 pb-3 border-t border-gray-200">
              <div className="flex items-center px-4">
                <User className="h-8 w-8 text-gray-400" />
                <div className="ml-3">
                  <div className="text-base font-medium text-gray-800">
                    {user?.email || 'Demo User'}
                  </div>
                </div>
              </div>
              <div className="mt-3 space-y-1">
                <button
                  onClick={logout}
                  className="block px-4 py-2 text-base font-medium text-gray-500 hover:text-gray-800 hover:bg-gray-100 w-full text-left"
                >
                  <div className="flex items-center">
                    <LogOut className="h-4 w-4 mr-3" />
                    Logout
                  </div>
                </button>
              </div>
            </div>
          </div>
        )}
      </nav>

      {/* Main content */}
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        {children}
      </main>
    </div>
  );
};

export default Layout;