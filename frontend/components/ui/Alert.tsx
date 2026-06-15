export function ErrorAlert({ message }: { message: string }) {
  return (
    <div className="rounded-lg border border-danger/50 bg-danger/10 px-4 py-3 text-sm text-red-200">
      {message}
    </div>
  );
}

export function LoadingSpinner() {
  return (
    <div className="flex items-center justify-center py-12">
      <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
    </div>
  );
}
