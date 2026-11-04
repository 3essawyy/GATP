import { AppShell, Container, Group, Text, Title } from '@mantine/core';

import { HealthBadge } from './components/HealthBadge';

export function App() {
  return (
    <AppShell header={{ height: 56 }} padding="md">
      <AppShell.Header>
        <Group h="100%" px="md" justify="space-between">
          <Title order={3}>GATP</Title>
          <HealthBadge />
        </Group>
      </AppShell.Header>
      <AppShell.Main>
        <Container size="md">
          <Title order={2}>Human-in-the-loop web testing assistant</Title>
          <Text c="dimmed" mt="sm">
            Skeleton (T-002). Inspection arrives in T-009.
          </Text>
        </Container>
      </AppShell.Main>
    </AppShell>
  );
}
