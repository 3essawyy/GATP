import {
  ActionIcon,
  Alert,
  Badge,
  Button,
  Card,
  Code,
  Group,
  List,
  Stack,
  Text,
  Textarea,
  TextInput,
  Title,
} from '@mantine/core';
import { useState } from 'react';
import { useParams } from 'react-router';

import type { PlanResult, TestPlan } from '../api/client';
import { useApprove, useEditPlan, usePlan, useProposePlan } from '../api/queries';
import { ErrorAlert } from '../components/ErrorAlert';
import { useTesterName } from '../components/tester';
import { UsageCard } from '../components/UsageCard';

const BASIS_COLOR: Record<string, string> = {
  requirement: 'green',
  observation: 'blue',
  assumption: 'orange',
};

/** Step 3: grounded test cases proposed by the model, edited and clarified by the tester (G1). */
export function PlanPage() {
  const projectId = Number(useParams().projectId);
  const plan = usePlan(projectId);
  const propose = useProposePlan(projectId);
  const [feedback, setFeedback] = useState('');

  return (
    <Stack>
      <Group justify="space-between">
        <Title order={3}>Test plan</Title>
        <Button
          onClick={() => propose.mutate('')}
          loading={propose.isPending && !feedback}
          variant={plan.data ? 'light' : 'filled'}
          data-testid="propose-plan"
        >
          {plan.data ? 'Propose a new plan' : 'Propose test cases'}
        </Button>
      </Group>
      <Text size="sm" c="dimmed">
        Cases use only elements of the approved scope. Every expected result says where it comes
        from: a requirement you gave, an observation on the page, or an assumption that you must
        confirm before approval.
      </Text>
      <ErrorAlert error={propose.error} />
      {plan.data && (
        // Re-keyed per version: editing state starts from the stored plan.
        <PlanEditor key={plan.data.version.id} projectId={projectId} result={plan.data} />
      )}
      {plan.data && (
        <Card withBorder>
          <Textarea
            label="Ask the model to revise the plan"
            placeholder="e.g. add a case for an invalid year; drop the cancel-link case"
            value={feedback}
            onChange={(e) => setFeedback(e.currentTarget.value)}
            data-testid="plan-feedback"
          />
          <Group mt="xs">
            <Button
              variant="light"
              disabled={!feedback.trim()}
              loading={propose.isPending && !!feedback}
              onClick={() => propose.mutate(feedback, { onSuccess: () => setFeedback('') })}
            >
              Revise with feedback
            </Button>
          </Group>
        </Card>
      )}
      {propose.data?.call && <UsageCard call={propose.data.call} />}
    </Stack>
  );
}

function PlanEditor({ projectId, result }: { projectId: number; result: PlanResult }) {
  const [tester] = useTesterName();
  const edit = useEditPlan(projectId);
  const approve = useApprove(projectId);
  const [draft, setDraft] = useState<TestPlan>(result.plan);
  const [reason, setReason] = useState('');
  const dirty = JSON.stringify(draft) !== JSON.stringify(result.plan);
  const label = (id: string | null | undefined) => (id ? (result.element_labels?.[id] ?? id) : '');

  const setCase = (i: number, patch: Partial<TestPlan['cases'][number]>) =>
    setDraft({ ...draft, cases: draft.cases.map((c, j) => (j === i ? { ...c, ...patch } : c)) });

  return (
    <Stack>
      <Group gap="xs">
        <Badge variant="light" data-testid="plan-version">
          version {result.version.number} · {result.version.author}
        </Badge>
        {result.approved ? (
          <Badge color="green" data-testid="plan-approved">
            G1 approved
          </Badge>
        ) : (
          <Badge color="yellow">not approved</Badge>
        )}
        <Text size="xs" c="dimmed">
          {result.version.reason}
        </Text>
      </Group>
      {result.blockers.length > 0 && (
        <Alert color="yellow" title="Before approval (G1)" data-testid="plan-blockers">
          <List size="sm">
            {result.blockers.map((b) => (
              <List.Item key={b}>{b}</List.Item>
            ))}
          </List>
          <Text size="xs" mt="xs">
            Answer the clarification questions at the top of the page.
          </Text>
        </Alert>
      )}
      {draft.cases.map((c, i) => (
        <Card key={c.id} withBorder data-testid={`case-${c.id}`}>
          <Group justify="space-between" wrap="nowrap">
            <Group gap="xs" style={{ flex: 1 }}>
              <Badge>{c.id}</Badge>
              <TextInput
                aria-label={`${c.id} title`}
                value={c.title}
                onChange={(e) => setCase(i, { title: e.currentTarget.value })}
                style={{ flex: 1 }}
              />
              <Badge variant="outline">{c.priority}</Badge>
            </Group>
            <ActionIcon
              color="red"
              variant="subtle"
              aria-label={`Delete ${c.id}`}
              onClick={() => setDraft({ ...draft, cases: draft.cases.filter((_, j) => j !== i) })}
            >
              ✕
            </ActionIcon>
          </Group>
          <Text fw={500} size="sm" mt="sm">
            Steps
          </Text>
          <List type="ordered" size="sm">
            {c.steps.map((s, k) => (
              <List.Item key={k}>
                <Code>{s.action}</Code> {s.action === 'goto' ? s.value : label(s.element_id)}
                {s.action !== 'goto' && s.action !== 'click' && (
                  <TextInput
                    size="xs"
                    display="inline-block"
                    ml="xs"
                    w={220}
                    aria-label={`${c.id} step ${k + 1} value`}
                    value={s.value ?? ''}
                    onChange={(e) =>
                      setCase(i, {
                        steps: c.steps.map((x, m) =>
                          m === k ? { ...x, value: e.currentTarget.value } : x,
                        ),
                      })
                    }
                  />
                )}
              </List.Item>
            ))}
          </List>
          <Text fw={500} size="sm" mt="sm">
            Expected results
          </Text>
          <Stack gap={4}>
            {c.expected.map((x, k) => (
              <Group key={x.id || k} gap="xs" wrap="nowrap" data-testid={`exp-${x.id}`}>
                <Badge size="sm" color={BASIS_COLOR[x.basis]} variant="light" w={110}>
                  {x.basis}
                </Badge>
                {x.basis === 'assumption' && (
                  <Badge size="xs" color={x.confirmed ? 'green' : 'red'}>
                    {x.confirmed ? 'confirmed' : 'unconfirmed'}
                  </Badge>
                )}
                <Text size="sm">
                  {label(x.element_id) || 'page'} <Code>{x.kind}</Code>
                </Text>
                {!['visible', 'hidden', 'enabled', 'disabled', 'checked'].includes(x.kind) && (
                  <TextInput
                    size="xs"
                    w={220}
                    aria-label={`${x.id} value`}
                    value={x.value ?? ''}
                    onChange={(e) =>
                      setCase(i, {
                        expected: c.expected.map((y, m) =>
                          m === k ? { ...y, value: e.currentTarget.value } : y,
                        ),
                      })
                    }
                  />
                )}
                <Text size="xs" c="dimmed" style={{ flex: 1 }}>
                  {x.evidence}
                </Text>
                <ActionIcon
                  color="red"
                  variant="subtle"
                  aria-label={`Delete ${x.id}`}
                  onClick={() => setCase(i, { expected: c.expected.filter((_, m) => m !== k) })}
                >
                  ✕
                </ActionIcon>
              </Group>
            ))}
          </Stack>
        </Card>
      ))}
      <Group>
        <TextInput
          placeholder="Why are you changing the plan?"
          value={reason}
          onChange={(e) => setReason(e.currentTarget.value)}
          disabled={!dirty}
          w={360}
          aria-label="Edit reason"
        />
        <Button
          disabled={!dirty || !reason.trim()}
          loading={edit.isPending}
          onClick={() =>
            edit.mutate(
              { plan: draft, reason, actor: tester || 'tester' },
              { onSuccess: () => setReason('') },
            )
          }
          data-testid="save-plan"
        >
          Save edits (new version)
        </Button>
        {!result.approved && (
          <Button
            color="green"
            disabled={!tester || dirty || result.blockers.length > 0}
            loading={approve.isPending}
            onClick={() =>
              approve.mutate({ gate: 'G1', actor: tester, artifact_version_id: result.version.id })
            }
            data-testid="approve-g1"
          >
            Approve plan (G1) as {tester || '…'}
          </Button>
        )}
      </Group>
      <ErrorAlert error={edit.error ?? approve.error} />
    </Stack>
  );
}
