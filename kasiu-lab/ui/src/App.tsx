import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ChatWorkspace } from './presentation/features/chat/ChatWorkspace';
import { ErrorBoundary } from './presentation/components/ErrorBoundary';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 30_000,
      refetchOnWindowFocus: false,
    },
  },
});

export function App() {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <div className="h-screen w-screen bg-[#000000]">
          <ChatWorkspace />
        </div>
      </QueryClientProvider>
    </ErrorBoundary>
  );
}

export default App;
