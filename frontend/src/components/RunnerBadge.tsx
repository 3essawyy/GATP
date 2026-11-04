import { Badge, Tooltip } from '@mantine/core';

import { useRunnerHealth } from '../api/queries';

/** Whether the separate runner process (which owns the browser) is reachable. */
export function RunnerBadge() {
  const runner = useRunnerHealth();
  if (runner.isPending) return null;
  if (runner.isError || !runner.data.available) {
    return (
      <Tooltip label={runner.data?.detail || 'Start it with: uv run poe runner'}>
        <Badge color="red" variant="light" data-testid="runner-health">
          Runner offline
        </Badge>
      </Tooltip>
    );
  }
  return (
    <Badge color="green" variant="light" data-testid="runner-health">
      Runner ready{runner.data.headless ? ' (headless)' : ''}
    </Badge>
  );
}
