import { AlertCircle, RefreshCw } from 'lucide-react';

interface ErrorMessageProps {
  message: string;
  error?: Error | unknown;
  onRetry?: () => void;
}

export function ErrorMessage({ message, error, onRetry }: ErrorMessageProps) {
  const errorDetails = error instanceof Error ? error.message : String(error);

  return (
    <div className="rounded-lg border border-red-200 bg-red-50 dark:border-red-900 dark:bg-red-950/30 p-6">
      <div className="flex items-start gap-4">
        <AlertCircle className="h-6 w-6 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-red-900 dark:text-red-100 mb-2">
            {message}
          </h3>
          {errorDetails && (
            <p className="text-sm text-red-700 dark:text-red-300 mb-4">
              {errorDetails}
            </p>
          )}
          {onRetry && (
            <button
              onClick={onRetry}
              className="inline-flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors"
            >
              <RefreshCw className="h-4 w-4" />
              Retry
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
