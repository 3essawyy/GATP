import {
  Alert,
  Badge,
  Button,
  Card,
  Group,
  List,
  Stack,
  Table,
  Tabs,
  Text,
  Textarea,
  TextInput,
  Title,
} from '@mantine/core';
import { useState } from 'react';
import { useParams } from 'react-router';

import type { CodeFile, CodeResult } from '../api/client';
import {
  useApproveCode,
  useCode,
  useEditFile,
  useGenerateCode,
  useValidateCode,
} from '../api/queries';
import { ErrorAlert } from '../components/ErrorAlert';
import { useTesterName } from '../components/tester';

interface Finding {
  file: string;
  line: number;
  check: string;
  message: string;
}
interface RecountItem {
  page: string;
  locator: string;
  count: number | null;
  ok: boolean;
}

/** Step 4: review the generated Page Objects + tests, validate them, approve (G2). */
export function CodePage() {
  const projectId = Number(useParams().projectId);
  const code = useCode(projectId);
  const generate = useGenerateCode(projectId);
  const validate = useValidateCode(projectId);
  const approve = useApproveCode(projectId);
  const [tester] = useTesterName();
  const data = code.data;
  const files = data?.files ?? [];

  return (
    <Stack>
      <Group justify="space-between">
        <Title order={3}>Code review</Title>
        <Button
          onClick={() => generate.mutate(undefined)}
          loading={generate.isPending}
          variant={files.length ? 'light' : 'filled'}
          data-testid="generate-code"
        >
          {files.length
            ? 'Regenerate from the approved plan'
            : 'Generate code from the approved plan'}
        </Button>
      </Group>
      <Text size="sm" c="dimmed">
        Code is rendered from the approved test plan (no model call). Every locator comes from the
        inspection snapshot. Validation runs syntax, locator and safety checks, a live recount of
        every locator, and <code>pytest --collect-only</code> in the runner.
      </Text>
      <ErrorAlert error={generate.error} />
      {files.length > 0 && data && (
        <>
          <Group>
            <Button
              onClick={() => validate.mutate(undefined)}
              loading={validate.isPending}
              data-testid="validate-code"
            >
              Validate
            </Button>
            {data.report && (
              <Badge color={data.report.ok ? 'green' : 'red'} data-testid="validation-status">
                {data.report.ok ? 'validation passed' : 'validation failed'}
              </Badge>
            )}
            {!data.report && <Badge color="gray">not validated (for these versions)</Badge>}
            {data.approved ? (
              <Badge color="green" data-testid="code-approved">
                G2 approved
              </Badge>
            ) : (
              <Button
                color="green"
                disabled={!tester || !data.report?.ok}
                loading={approve.isPending}
                onClick={() => approve.mutate(tester)}
                data-testid="approve-g2"
              >
                Approve code (G2) as {tester || '…'}
              </Button>
            )}
          </Group>
          <ErrorAlert error={validate.error ?? approve.error} />
          {data.report && <ValidationReport report={data.report.report} />}
          <FileTabs projectId={projectId} result={data} />
        </>
      )}
    </Stack>
  );
}

function ValidationReport({ report }: { report: Record<string, unknown> }) {
  const r = report as {
    static: { ok: boolean; findings: Finding[]; locators: number; setup_locators?: number };
    recount: { ok: boolean; items: RecountItem[] };
    collect: { ok: boolean; tests: string[]; error?: string; output?: string };
  };
  const mark = (ok: boolean) => (
    <Badge size="xs" color={ok ? 'green' : 'red'}>
      {ok ? 'ok' : 'failed'}
    </Badge>
  );
  return (
    <Card withBorder data-testid="validation-report">
      <Text fw={500}>Validation report</Text>
      <Group mt="xs">
        {mark(r.static.ok)}
        <Text size="sm">
          Static: syntax, {r.static.locators} locator(s) checked against the snapshot
          {r.static.setup_locators
            ? ` (${r.static.setup_locators} from your approved setup steps, e.g. sign-in)`
            : ''}
          , safety
        </Text>
      </Group>
      {r.static.findings.length > 0 && (
        <Alert color="red" mt="xs" data-testid="findings-list">
          <List size="sm">
            {r.static.findings.map((f, i) => (
              <List.Item key={i}>
                <b>{f.check}</b> {f.file}:{f.line} {f.message}
              </List.Item>
            ))}
          </List>
        </Alert>
      )}
      <Group mt="xs">
        {mark(r.recount.ok)}
        <Text size="sm">Live recount on the target (each locator must match exactly 1)</Text>
      </Group>
      <Table fz="xs" mt={4} withRowBorders={false}>
        <Table.Tbody>
          {r.recount.items.map((i) => (
            <Table.Tr key={`${i.page}${i.locator}`}>
              <Table.Td>{new URL(i.page).pathname}</Table.Td>
              <Table.Td>
                <code>{i.locator}</code>
              </Table.Td>
              <Table.Td c={i.ok ? undefined : 'red'}>count {i.count ?? '—'}</Table.Td>
            </Table.Tr>
          ))}
        </Table.Tbody>
      </Table>
      <Group mt="xs">
        {mark(r.collect.ok)}
        <Text size="sm">
          pytest --collect-only: {r.collect.tests.length} test(s){' '}
          {r.collect.error ? `(${r.collect.error})` : ''}
        </Text>
      </Group>
      <List size="xs" ml="md">
        {r.collect.tests.map((t) => (
          <List.Item key={t}>
            <code>{t}</code>
          </List.Item>
        ))}
      </List>
    </Card>
  );
}

function FileTabs({ projectId, result }: { projectId: number; result: CodeResult }) {
  const first = result.files.find((f) => f.path.startsWith('tests/')) ?? result.files[0];
  const [active, setActive] = useState<string | null>(first?.path ?? null);
  return (
    <Tabs value={active} onChange={setActive}>
      <Tabs.List>
        {result.files.map((f) => (
          <Tabs.Tab key={f.path} value={f.path}>
            {f.path}{' '}
            <Text span size="xs" c="dimmed">
              v{f.version.number}
            </Text>
          </Tabs.Tab>
        ))}
      </Tabs.List>
      {result.files.map((f) => (
        <Tabs.Panel key={f.path} value={f.path} pt="xs">
          {/* Re-keyed per version: the editor starts from the stored content. */}
          <FileEditor key={f.version.id} projectId={projectId} file={f} />
        </Tabs.Panel>
      ))}
    </Tabs>
  );
}

function FileEditor({ projectId, file }: { projectId: number; file: CodeFile }) {
  const [tester] = useTesterName();
  const edit = useEditFile(projectId);
  const [content, setContent] = useState(file.version.content);
  const [reason, setReason] = useState('');
  const dirty = content !== file.version.content;
  return (
    <Stack gap="xs">
      <Text size="xs" c="dimmed">
        v{file.version.number} by {file.version.author}: {file.version.reason}
      </Text>
      <Textarea
        value={content}
        onChange={(e) => setContent(e.currentTarget.value)}
        autosize
        minRows={12}
        styles={{ input: { fontFamily: 'monospace', fontSize: 12, whiteSpace: 'pre' } }}
        spellCheck={false}
        aria-label={`Code of ${file.path}`}
        data-testid={`editor-${file.path}`}
      />
      <Group>
        <TextInput
          placeholder="Why are you changing this file?"
          value={reason}
          onChange={(e) => setReason(e.currentTarget.value)}
          disabled={!dirty}
          w={360}
          aria-label={`Reason for editing ${file.path}`}
        />
        <Button
          disabled={!dirty || !reason.trim()}
          loading={edit.isPending}
          onClick={() =>
            edit.mutate({
              artifactId: file.artifact_id,
              content,
              reason,
              actor: tester || 'tester',
            })
          }
        >
          Save edit (new version, re-validate)
        </Button>
      </Group>
      <ErrorAlert error={edit.error} />
    </Stack>
  );
}
