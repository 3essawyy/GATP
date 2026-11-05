import {
  Accordion,
  Alert,
  Badge,
  Button,
  Card,
  Code,
  Group,
  Stack,
  Table,
  Text,
  Title,
} from '@mantine/core';
import { useParams } from 'react-router';

import type { Rescan } from '../api/client';
import { useLatestRescan, useRescan } from '../api/queries';
import { ErrorAlert } from '../components/ErrorAlert';

interface Breakdown {
  field: string;
  old: unknown;
  new: unknown;
  similarity: number;
}
interface CandidateView {
  new_id: string;
  label: string;
  score: number;
  locator: string;
  breakdown: Breakdown[];
}
interface ElementView {
  old_id: string;
  old_label: string;
  old_locator: string;
  referenced: boolean;
  used_by: string[];
  status: 'unchanged' | 'clear_match' | 'ambiguous' | 'missing';
  reason: string;
  text_change: string;
  new_label: string;
  new_locator: string;
  candidates: CandidateView[];
}
interface PageView {
  page_url: string;
  html_changed: boolean;
  counts: Record<string, number>;
  elements: ElementView[];
  appeared: { new_id: string; label: string; locator: string }[];
}
interface PageRow {
  page_url: string;
  error: string;
  failed_setup_step: number | null;
  trial_setup?: {
    step: number;
    old_locator: string;
    proposed_locator: string;
    based_on: string;
    note: string;
    error?: string;
  } | null;
}

const STATUS: Record<ElementView['status'], { color: string; label: string }> = {
  unchanged: { color: 'green', label: 'unchanged' },
  clear_match: { color: 'blue', label: 'changed: clear match' },
  ambiguous: { color: 'orange', label: 'ambiguous: you decide' },
  missing: { color: 'red', label: 'missing' },
};

/** Step 6 (T-016): rescan the approved pages and flag what changed for the tests. */
export function MaintainPage() {
  const projectId = Number(useParams().projectId);
  const latest = useLatestRescan(projectId);
  const rescan = useRescan(projectId);
  const data = latest.data;

  return (
    <Stack>
      <Group justify="space-between">
        <Title order={3}>Maintain</Title>
        <Button onClick={() => rescan.mutate()} loading={rescan.isPending} data-testid="rescan">
          Rescan pages
        </Button>
      </Group>
      <Text size="sm" c="dimmed">
        A rescan inspects every approved page again (new snapshots) and compares each element the
        tests use with the snapshot the tests were built on. Matching is deterministic (fingerprint
        scores, shown below). Nothing is changed here: repairs need your approval (G4).
      </Text>
      <ErrorAlert error={rescan.error} />
      {data && <RescanView rescan={data} />}
    </Stack>
  );
}

function RescanView({ rescan }: { rescan: Rescan }) {
  const pages = (rescan.summary.pages as PageRow[] | undefined) ?? [];
  const changed = Number(rescan.summary.referenced_changes ?? 0);
  return (
    <Stack data-testid="rescan-result">
      <Group gap="xs">
        <Text fw={500}>Rescan #{rescan.id}</Text>
        <Badge color={changed ? 'orange' : 'green'} data-testid="rescan-status">
          {changed ? `${changed} used element(s) changed` : 'no used element changed'}
        </Badge>
        <Text size="xs" c="dimmed">
          {new Date(rescan.created_at).toLocaleString()}
        </Text>
      </Group>
      {pages
        .filter((p) => p.error || p.trial_setup)
        .map((p) => (
          <Alert
            key={p.page_url}
            color={p.error ? 'red' : 'yellow'}
            title={`${new URL(p.page_url).pathname}: setup step ${
              p.trial_setup?.step ?? p.failed_setup_step ?? ''
            } broke`}
            data-testid="setup-alert"
          >
            {p.trial_setup ? (
              <Text size="sm">
                The setup step used <Code>{p.trial_setup.old_locator}</Code>, which no longer
                matches. Based on {p.trial_setup.based_on}, the page was inspected <b>read-only</b>{' '}
                with <Code>{p.trial_setup.proposed_locator}</Code>. {p.trial_setup.note}.
              </Text>
            ) : (
              <Text size="sm">{p.error}</Text>
            )}
          </Alert>
        ))}
      {rescan.change_sets.map((c) => (
        <PageChanges key={c.id} view={c.summary as unknown as PageView} />
      ))}
    </Stack>
  );
}

function PageChanges({ view }: { view: PageView }) {
  const path = new URL(view.page_url).pathname;
  return (
    <Card withBorder data-testid={`changes-${path.replace(/\W/g, '')}`}>
      <Group gap="xs">
        <Text fw={500}>{path}</Text>
        {Object.entries(view.counts)
          .filter(([, n]) => n)
          .map(([k, n]) => (
            <Badge
              key={k}
              size="sm"
              variant="light"
              color={STATUS[k as ElementView['status']].color}
            >
              {n} {STATUS[k as ElementView['status']].label}
            </Badge>
          ))}
        {view.html_changed && (
          <Badge size="sm" variant="outline" color="gray">
            page HTML changed
          </Badge>
        )}
      </Group>
      <Accordion
        multiple
        mt="xs"
        defaultValue={view.elements.filter((e) => e.status !== 'unchanged').map((e) => e.old_id)}
      >
        {view.elements.map((e) => (
          <Accordion.Item key={e.old_id} value={e.old_id}>
            <Accordion.Control>
              <Group gap="xs">
                <Badge size="sm" color={STATUS[e.status].color} data-testid={`status-${e.old_id}`}>
                  {STATUS[e.status].label}
                </Badge>
                <Text size="sm">{e.old_label}</Text>
                {e.new_label && e.new_label !== e.old_label && (
                  <Text size="sm">→ {e.new_label}</Text>
                )}
                <Text size="xs" c="dimmed">
                  {e.referenced ? `used by ${e.used_by.join(', ')}` : 'not used by the tests'}
                </Text>
              </Group>
            </Accordion.Control>
            <Accordion.Panel>
              <Text size="sm">
                Old locator <Code>{e.old_locator || '—'}</Code>
                {e.new_locator && (
                  <>
                    {' '}
                    → new <Code>{e.new_locator}</Code>
                  </>
                )}
              </Text>
              <Text size="xs" c="dimmed" mt={4}>
                {e.reason}
                {e.text_change && ` · ${e.text_change}`}
              </Text>
              {e.candidates.map((c) => (
                <Card key={c.new_id} withBorder mt="xs" p="xs">
                  <Text size="sm">
                    Candidate {c.label} · score <b>{c.score.toFixed(2)}</b> ·{' '}
                    <Code>{c.locator || 'no unique locator'}</Code>
                  </Text>
                  <Table fz="xs" mt={4} withRowBorders={false}>
                    <Table.Thead>
                      <Table.Tr>
                        <Table.Th>Field</Table.Th>
                        <Table.Th>Before</Table.Th>
                        <Table.Th>After</Table.Th>
                        <Table.Th>Similarity</Table.Th>
                      </Table.Tr>
                    </Table.Thead>
                    <Table.Tbody>
                      {c.breakdown.map((b) => (
                        <Table.Tr key={b.field}>
                          <Table.Td>{b.field}</Table.Td>
                          <Table.Td>{JSON.stringify(b.old)}</Table.Td>
                          <Table.Td>{JSON.stringify(b.new)}</Table.Td>
                          <Table.Td c={b.similarity < 1 ? 'orange' : undefined}>
                            {b.similarity.toFixed(2)}
                          </Table.Td>
                        </Table.Tr>
                      ))}
                    </Table.Tbody>
                  </Table>
                </Card>
              ))}
            </Accordion.Panel>
          </Accordion.Item>
        ))}
      </Accordion>
      {view.appeared.length > 0 && (
        <Text size="xs" c="dimmed" mt="xs">
          New on the page: {view.appeared.map((a) => a.label).join(', ')}
        </Text>
      )}
    </Card>
  );
}
