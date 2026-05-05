import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export const ProtectedRoute = ({ children, requireAdmin = false }) => {
    const { user, loading } = useAuth();

    if (loading) return <div className="text-white text-center p-10">Authenticating...</div>;

    if (!user) {
        return <Navigate to="/login" replace />;
    }

    if (requireAdmin && !user.is_admin) {
        return <Navigate to="/dashboard" replace />;
    }

    return children;
};
