import { Badge, Group, Table, Text } from '@mantine/core';

import type { LlmCall } from '../api/client';

/** Usage evidence for one model call; model time shown apart from browser time (REQ-Q8–Q10). */
export function UsageCard({ call, browserMs }: { call: LlmCall; browserMs?: number }) {
  const tokenSource = call.tokens_estimated ? 'estimated (~4 chars/token)' : 'reported by provider';
  return (
    <Table withRowBorders={false} fz="sm" data-testid="usage">
      <Table.Tbody>
        <Table.Tr>
          <Table.Td c="dimmed">Model</Table.Td>
          <Table.Td>
            <Group gap="xs">
              <Text size="sm">
                {call.provider} / {call.model}
                {call.model_version ? ` (${call.model_version})` : ''}
              </Text>
              {call.provider === 'fake' && (
                <Badge size="xs" color="gray">
                  offline fake provider, not a real model
                </Badge>
              )}
            </Group>
          </Table.Td>
        </Table.Tr>
        <Table.Tr>
          <Table.Td c="dimmed">Tokens</Table.Td>
          <Table.Td>
            {call.input_tokens} in / {call.output_tokens} out{' '}
            <Text span c="dimmed" size="xs">
              ({tokenSource})
            </Text>
          </Table.Td>
        </Table.Tr>
        <Table.Tr>
          <Table.Td c="dimmed">Model time</Table.Td>
          <Table.Td data-testid="model-time">{call.latency_ms} ms</Table.Td>
        </Table.Tr>
        {browserMs !== undefined && (
          <Table.Tr>
            <Table.Td c="dimmed">Browser time (inspecting the scoped pages)</Table.Td>
            <Table.Td data-testid="browser-time">{browserMs} ms</Table.Td>
          </Table.Tr>
        )}
        <Table.Tr>
          <Table.Td c="dimmed">Result</Table.Td>
          <Table.Td>
            <Badge size="sm" color={call.cache === 'reused' ? 'blue' : 'green'} variant="light">
              {call.cache === 'reused' ? 'reused (cached, no new model call)' : 'fresh call'}
            </Badge>{' '}
            <Text span size="xs" c="dimmed">
              template {call.purpose} v{call.template_version} · call #{call.id}
            </Text>
          </Table.Td>
        </Table.Tr>
      </Table.Tbody>
    </Table>
  );
}
