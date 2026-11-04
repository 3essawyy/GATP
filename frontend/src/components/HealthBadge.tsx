import { Badge, Group, Loader, Text } from '@mantine/core';

import { useHealth } from '../api/queries';

/** Shows whether the backend API is reachable. Pure display: no logic beyond the three states. */
export function HealthBadge() {
  const health = useHealth();

  if (health.isPending) {
    return (
      <Group gap="xs">
        <Loader size="xs" />
        <Text size="sm">Checking API…</Text>
      </Group>
    );
  }
  if (health.isError) {
    return (
      <Badge color="red" variant="light" data-testid="api-health">
        API unreachable
      </Badge>
    );
  }
  return (
    <Badge color="green" variant="light" data-testid="api-health">
      API {health.data.status} · v{health.data.version}
    </Badge>
  );
}
