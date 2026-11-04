import {
  Accordion,
  Alert,
  Badge,
  Button,
  Card,
  Checkbox,
  Code,
  Group,
  Image,
  Loader,
  Stack,
  Table,
  Text,
  Title,
} from '@mantine/core';
import { useState } from 'react';
import { useParams } from 'react-router';

import { fileUrl, type RunResult } from '../api/client';
import { useApproveAndRun, useCode, useRunSubject, useRuns } from '../api/queries';
import { ErrorAlert } from '../components/ErrorAlert';
import { useTesterName } from '../components/tester';

const OUTCOME_COLOR: Record<string, string> = {
  passed: 'green',
  failed: 'red',
  error: 'orange',
  skipped: 'gray',
};

/** Step 5: approve exactly what runs (G3), run it in the isolated runner, review results. */
export function RunPage() {
  const projectId = Number(useParams().projectId);
  const code = useCode(projectId);
  const subject = useRunSubject(projectId, !!code.data?.approved);
  const runs = useRuns(projectId);
  const run = useApproveAndRun(projectId);
  const [tester] = useTesterName();
  const [only, setOnly] = useState<string[]>([]);
  const s = subject.data;

  return (
    <Stack>
      <Title order={3}>Run tests</Title>
      {!code.data?.approved && (
        <Alert color="gray">Approve the code (G2) first. Only approved code can run.</Alert>
      )}
      {s && (
        <Card withBorder data-testid="run-subject">
          <Text fw={500}>You are approving (G3) exactly this run:</Text>
          <Table fz="sm" withRowBorders={false} mt="xs">
            <Table.Tbody>
              <Table.Tr>
                <Table.Td c="dimmed">Target</Table.Td>
                <Table.Td>{String(s.subject.target)}</Table.Td>
              </Table.Tr>
              <Table.Tr>
                <Table.Td c="dimmed">Code</Table.Td>
                <Table.Td>
                  {s.files.join(', ')} (version ids{' '}
                  {(s.subject.code_version_ids as number[]).join(', ')})
                </Table.Td>
              </Table.Tr>
              <Table.Tr>
                <Table.Td c="dimmed">Limits</Table.Td>
                <Table.Td>
                  sandbox: {s.isolation} · browser: {s.headless ? 'headless' : 'visible'} · only the
                  target origin is reachable · timeout {s.timeout_s}s
                </Table.Td>
              </Table.Tr>
            </Table.Tbody>
          </Table>
          <Text size="sm" mt="xs">
            Tests ({only.length ? `${only.length} selected` : 'all'}):
          </Text>
          {s.available_tests.map((t) => (
            <Checkbox
              key={t}
              size="xs"
              label={t}
              checked={only.includes(t)}
              onChange={() =>
                setOnly(only.includes(t) ? only.filter((x) => x !== t) : [...only, t])
              }
            />
          ))}
          <Group mt="sm">
            <Button
              color="green"
              disabled={!tester}
              loading={run.isPending}
              onClick={() =>
                run.mutate({ actor: tester, subject: { ...s.subject, tests: [...only].sort() } })
              }
              data-testid="approve-run"
            >
              Approve (G3) and run as {tester || '…'}
            </Button>
            {run.isPending && (
              <Group gap="xs">
                <Loader size="xs" />
                <Text size="sm">Running in the isolated runner (visible browser)…</Text>
              </Group>
            )}
          </Group>
        </Card>
      )}
      <ErrorAlert error={subject.error ?? run.error} />
      {(runs.data ?? []).map((r, i) => (
        <RunCard key={r.id} run={r} open={i === 0} />
      ))}
    </Stack>
  );
}

function RunCard({ run, open }: { run: RunResult; open: boolean }) {
  const passed = run.results.filter((r) => r.outcome === 'passed').length;
  const blocked = (run.scope.blocked_requests as unknown[] | undefined) ?? [];
  return (
    <Card withBorder data-testid={`run-${run.id}`}>
      <Group justify="space-between">
        <Group gap="xs">
          <Text fw={500}>Run #{run.id}</Text>
          <Badge color={OUTCOME_COLOR[run.status] ?? 'gray'} data-testid="run-status">
            {run.status}
          </Badge>
          <Text size="sm">
            {passed}/{run.results.length} passed · test time {run.duration_ms ?? '—'} ms
          </Text>
        </Group>
        <Text size="xs" c="dimmed">
          approval #{run.approval_id} · sandbox {String(run.scope.isolation)} · blocked requests{' '}
          {blocked.length}
        </Text>
      </Group>
      {run.status === 'error' && (
        <Alert color="orange" mt="xs" title="The run could not complete">
          {String(run.scope.error || 'see output')}
          <Code block>{String(run.scope.output ?? '')}</Code>
        </Alert>
      )}
      {open && (
        <Accordion
          multiple
          defaultValue={run.results.filter((r) => r.outcome !== 'passed').map((r) => String(r.id))}
        >
          {run.results.map((r) => (
            <Accordion.Item key={r.id} value={String(r.id)}>
              <Accordion.Control>
                <Group gap="xs">
                  <Badge size="sm" color={OUTCOME_COLOR[r.outcome]}>
                    {r.outcome}
                  </Badge>
                  <Text size="sm">{r.test_id}</Text>
                  <Text size="xs" c="dimmed">
                    {r.duration_ms} ms
                  </Text>
                </Group>
              </Accordion.Control>
              <Accordion.Panel>
                {r.message && (
                  <Code block c="red" data-testid="failure-message">
                    {r.message}
                  </Code>
                )}
                {r.details && (
                  <Accordion variant="contained" mt="xs">
                    <Accordion.Item value="stack">
                      <Accordion.Control>Stack excerpt</Accordion.Control>
                      <Accordion.Panel>
                        <Code block style={{ whiteSpace: 'pre-wrap' }}>
                          {r.details}
                        </Code>
                      </Accordion.Panel>
                    </Accordion.Item>
                  </Accordion>
                )}
                {r.screenshot_path && (
                  <Image
                    src={fileUrl(r.screenshot_path)}
                    alt={`Screenshot of ${r.test_id}`}
                    mt="xs"
                    maw={640}
                  />
                )}
              </Accordion.Panel>
            </Accordion.Item>
          ))}
        </Accordion>
      )}
    </Card>
  );
}
