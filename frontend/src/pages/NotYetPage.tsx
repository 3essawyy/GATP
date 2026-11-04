import { Text } from '@mantine/core';

/** Placeholder for workflow steps whose screens arrive in Phase 2 tasks. */
export function NotYetPage({ what }: { what: string }) {
  return <Text c="dimmed">{what} arrives in Phase 2.</Text>;
}
