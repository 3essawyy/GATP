import {
  Accordion,
  Badge,
  Button,
  Card,
  Code,
  Group,
  List,
  Stack,
  Text,
  Title,
} from '@mantine/core';

import { useLatestInsight, useRequestInsight } from '../api/queries';
import { ErrorAlert } from './ErrorAlert';
import { UsageCard } from './UsageCard';

/** Phase 1 model call: grounded summary + next actions for the approved scope (T-010). */
export function InsightPanel({ projectId, enabled }: { projectId: number; enabled: boolean }) {
  const latest = useLatestInsight(projectId);
  const ask = useRequestInsight(projectId);
  const result = ask.data ?? latest.data;

  return (
    <Card withBorder data-testid="insight-panel">
      <Stack>
        <Group justify="space-between">
          <Title order={4}>Ask the model about the approved scope</Title>
          <Button
            onClick={() => ask.mutate()}
            loading={ask.isPending}
            disabled={!enabled}
            data-testid="ask-model"
          >
            Summarise & suggest next actions
          </Button>
        </Group>
        {!enabled && (
          <Text c="dimmed" size="sm">
            Approve the scope (G0) first. Only approved, in-scope elements are sent to the model.
          </Text>
        )}
        <ErrorAlert error={ask.error} />
        {result && (
          <>
            <Text data-testid="insight-summary">{result.insight.summary}</Text>
            {result.insight.next_actions.length > 0 && (
              <div>
                <Text fw={500} size="sm">
                  Suggested next actions
                </Text>
                <List size="sm" spacing={4}>
                  {result.insight.next_actions.map((a, i) => (
                    <List.Item key={i}>
                      <Badge
                        size="xs"
                        mr={6}
                        color={a.basis === 'observed' ? 'green' : 'orange'}
                        variant="light"
                      >
                        {a.basis}
                      </Badge>
                      {a.action} <Code>{a.element_ids.join(', ')}</Code>{' '}
                      <Text span c="dimmed" size="xs">
                        {a.rationale}
                      </Text>
                    </List.Item>
                  ))}
                </List>
              </div>
            )}
            {result.insight.elements.length > 0 && (
              <div>
                <Text fw={500} size="sm">
                  Elements (observed on the page)
                </Text>
                <List size="sm" spacing={2}>
                  {result.insight.elements.map((n) => (
                    <List.Item key={n.element_id}>
                      <Code>{n.element_id}</Code> {n.observation}
                    </List.Item>
                  ))}
                </List>
              </div>
            )}
            {(result.insight.assumptions.length > 0 || result.insight.questions.length > 0) && (
              <Group align="start" grow>
                <div>
                  <Text fw={500} size="sm" c="orange">
                    Assumptions (not shown on the page)
                  </Text>
                  <List size="sm">
                    {result.insight.assumptions.map((a, i) => (
                      <List.Item key={i}>{a}</List.Item>
                    ))}
                  </List>
                </div>
                <div>
                  <Text fw={500} size="sm">
                    Questions for you
                  </Text>
                  <List size="sm">
                    {result.insight.questions.map((q, i) => (
                      <List.Item key={i}>{q}</List.Item>
                    ))}
                  </List>
                </div>
              </Group>
            )}
            <UsageCard call={result.call} browserMs={result.browser_ms} />
            <Accordion variant="contained">
              <Accordion.Item value="sent">
                <Accordion.Control>
                  Exactly what was sent ({result.element_ids_sent.length} in-scope elements, scope v
                  {result.scope_version})
                </Accordion.Control>
                <Accordion.Panel>
                  <Code block style={{ maxHeight: 320, overflow: 'auto', whiteSpace: 'pre-wrap' }}>
                    {result.call.request}
                  </Code>
                </Accordion.Panel>
              </Accordion.Item>
            </Accordion>
          </>
        )}
      </Stack>
    </Card>
  );
}
