import { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

interface Props {
  children: ReactNode;
  fallbackTitle?: string;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary capturó un error no controlado:', error, errorInfo);
  }

  private handleReset = () => {
    this.setState({ hasError: false, error: null });
    window.location.reload();
  };

  public render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen w-full bg-slate-950 flex items-center justify-center p-6 text-slate-100 font-sans">
          <div className="max-w-md w-full bg-slate-900/90 border border-red-500/40 rounded-xl p-6 shadow-2xl shadow-red-950/20 backdrop-blur">
            <div className="flex items-center gap-3 text-red-400 mb-4">
              <AlertTriangle className="h-7 w-7 flex-shrink-0" />
              <h2 className="text-lg font-bold">
                {this.props.fallbackTitle || 'Se produjo un error en la aplicación'}
              </h2>
            </div>
            <p className="text-xs text-slate-400 mb-4 leading-relaxed">
              La vista encontró un error inesperado al renderizar. Tu progreso y datos del cuaderno se encuentran preservados en el servidor.
            </p>
            {this.state.error && (
              <pre className="p-3 bg-slate-950/80 border border-slate-800 rounded text-[11px] font-mono text-red-300 overflow-x-auto mb-5 max-h-32">
                {this.state.error.message}
              </pre>
            )}
            <button
              type="button"
              onClick={this.handleReset}
              className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 active:bg-emerald-700 text-white rounded-lg text-sm font-semibold transition shadow-lg shadow-emerald-950/40"
            >
              <RefreshCw className="h-4 w-4" />
              Reintentar y Recargar
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
