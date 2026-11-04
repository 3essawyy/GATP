import { Alert } from '@mantine/core';

/** Shows an API error message (the API explains what is wrong; the UI just displays it). */
export function ErrorAlert({ error }: { error: Error | null | undefined }) {
  if (!error) return null;
  return (
    <Alert color="red" variant="light" title="Request failed" data-testid="error">
      {error.message}
    </Alert>
  );
}
