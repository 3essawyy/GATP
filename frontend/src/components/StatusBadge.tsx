import { Badge } from '@mantine/core';

const COLORS: Record<string, string> = {
  todo: 'gray',
  needs_approval: 'yellow',
  approved: 'green',
  blocked: 'red',
  failed: 'red',
};
const LABELS: Record<string, string> = {
  todo: 'to do',
  needs_approval: 'needs approval',
  approved: 'done',
  blocked: 'blocked',
  failed: 'last run failed',
};

/** Shows a workflow step status exactly as the API computed it. */
export function StatusBadge({ status }: { status: string }) {
  return (
    <Badge size="xs" variant="light" color={COLORS[status] ?? 'gray'}>
      {LABELS[status] ?? status}
    </Badge>
  );
}
