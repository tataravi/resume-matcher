import { useState, useEffect, createContext, useContext } from 'react';
import apiService from '../services/api';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async () => {
    try {
      if (apiService.isAuthenticated()) {
        const response = await apiService.verifyToken();
        setUser(response.data.user);
        setIsAuthenticated(true);
      } else {
        // Auto-login with demo for development
        console.log('No token found, getting demo access...');
        const response = await apiService.getDemoToken();
        if (response) {
          const verifyResponse = await apiService.verifyToken();
          setUser(verifyResponse.data.user);
          setIsAuthenticated(true);
        }
      }
    } catch (error) {
      console.error('Auth verification failed:', error);
      setUser(null);
      setIsAuthenticated(false);
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password) => {
    try {
      const response = await apiService.login(email, password);
      await checkAuthStatus();
      return response;
    } catch (error) {
      throw error;
    }
  };

  const register = async (email, password, fullName) => {
    try {
      const response = await apiService.register(email, password, fullName);
      return response;
    } catch (error) {
      throw error;
    }
  };

  const getDemoAccess = async () => {
    try {
      const response = await apiService.getDemoToken();
      await checkAuthStatus();
      return response;
    } catch (error) {
      throw error;
    }
  };

  const logout = () => {
    apiService.logout();
    setUser(null);
    setIsAuthenticated(false);
  };

  const value = {
    user,
    loading,
    isAuthenticated,
    login,
    register,
    getDemoAccess,
    logout,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};