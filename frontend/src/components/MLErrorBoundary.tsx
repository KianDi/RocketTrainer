import React, { Component, ErrorInfo, ReactNode } from 'react';
import { ExclamationTriangleIcon, ArrowPathIcon } from '@heroicons/react/24/outline';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

/**
 * Error boundary specifically for ML components
 * Provides graceful error handling for ML API failures
 */
class MLErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ML Component Error:', error, errorInfo);
  }

  private handleRetry = () => {
    this.setState({ hasError: false, error: undefined });
  };

  public render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="bg-white rounded-lg shadow-md p-6 border border-red-200">
          <div className="text-center">
            <ExclamationTriangleIcon className="w-12 h-12 text-red-500 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              AI Service Unavailable
            </h3>
            <p className="text-gray-600 mb-6">
              The AI analysis service is temporarily unavailable. This might be due to:
            </p>
            <ul className="text-sm text-gray-600 mb-6 text-left max-w-md mx-auto space-y-1">
              <li>• High server load</li>
              <li>• Temporary network issues</li>
              <li>• Service maintenance</li>
              <li>• Rate limiting (too many requests)</li>
            </ul>
            <div className="space-y-3">
              <button
                onClick={this.handleRetry}
                className="btn-primary flex items-center space-x-2 mx-auto"
              >
                <ArrowPathIcon className="w-4 h-4" />
                <span>Try Again</span>
              </button>
              <p className="text-xs text-gray-500">
                If the problem persists, please try again in a few minutes
              </p>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default MLErrorBoundary;
