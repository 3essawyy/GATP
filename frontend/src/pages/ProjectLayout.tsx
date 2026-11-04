import {
  Alert,
  Anchor,
  AppShell,
  Badge,
  Button,
  Group,
  NavLink,
  Stack,
  Text,
  TextInput,
  Title,
} from '@mantine/core';
import { useState } from 'react';
import { Link, Outlet, useLocation, useParams } from 'react-router';

import { useProjectEvents } from '../api/events';
import { useAnswer, useClarifications, useProject, useWorkflow } from '../api/queries';
import { HealthBadge } from '../components/HealthBadge';
import { RunnerBadge } from '../components/RunnerBadge';
import { StatusBadge } from '../components/StatusBadge';
import { useTesterName } from '../components/tester';

const STEP_LABELS: Record<string, string> = {
  inspect: '1 · Inspect pages',
  scope: '2 · Scope & goal (G0)',
  plan: '3 · Test plan (G1)',
  code: '4 · Code (G2)',
};
const LATER = [
  ['run', '5 · Run (G3)'],
  ['maintain', '6 · Maintain (G4)'],
  ['history', '7 · History (G5)'],
  ['usage', 'Model usage'],
];

/** Project workspace: step navigation with gate status (from the API) + current step. */
export function ProjectLayout() {
  const projectId = Number(useParams().projectId);
  const project = useProject(projectId);
  const workflow = useWorkflow(projectId);
  const location = useLocation();
  const [tester, setTester] = useTesterName();
  useProjectEvents(projectId);

  return (
    <AppShell header={{ height: 56 }} navbar={{ width: 250, breakpoint: 'sm' }} padding="md">
      <AppShell.Header>
        <Group h="100%" px="md" justify="space-between">
          <Group>
            <Anchor component={Link} to="/" underline="never" c="inherit">
              <Title order={4}>GATP</Title>
            </Anchor>
            <Text fw={500}>{project.data?.name}</Text>
            <Badge variant="outline" color="gray">
              {project.data?.origin}
            </Badge>
          </Group>
          <Group>
            <TextInput
              size="xs"
              placeholder="Your name (for approvals)"
              value={tester}
              onChange={(e) => setTester(e.currentTarget.value)}
              data-testid="tester-name"
            />
            <RunnerBadge />
            <HealthBadge />
          </Group>
        </Group>
      </AppShell.Header>
      <AppShell.Navbar p="xs">
        {(workflow.data ?? []).map((s) => (
          <NavLink
            key={s.step}
            component={Link}
            to={`/projects/${projectId}/${s.step}`}
            active={location.pathname.endsWith(`/${s.step}`)}
            label={STEP_LABELS[s.step] ?? s.step}
            description={s.detail}
            rightSection={<StatusBadge status={s.status} />}
            data-testid={`step-${s.step}`}
          />
        ))}
        {LATER.map(([key, label]) => (
          <NavLink key={key} label={label} description="Phase 2" disabled />
        ))}
      </AppShell.Navbar>
      <AppShell.Main>
        <Stack>
          <OpenClarifications projectId={projectId} tester={tester} />
          <Outlet />
        </Stack>
      </AppShell.Main>
    </AppShell>
  );
}

/** Questions GATP must not answer itself; each blocks its step until the tester answers. */
function OpenClarifications({ projectId, tester }: { projectId: number; tester: string }) {
  const open = useClarifications(projectId);
  const answer = useAnswer(projectId);
  const [text, setText] = useState<Record<number, string>>({});
  if (!open.data?.length) return null;
  return (
    <>
      {open.data.map((c) => (
        <Alert key={c.id} color="yellow" title={`Clarification needed (${c.step})`}>
          <Text size="sm">{c.question}</Text>
          <Group mt="xs">
            {c.options.map((o) => (
              <Button
                key={String(o)}
                size="xs"
                variant="light"
                disabled={!tester}
                onClick={() => answer.mutate({ id: c.id, answer: String(o), actor: tester })}
              >
                {String(o)}
              </Button>
            ))}
            <TextInput
              size="xs"
              placeholder="Your answer"
              value={text[c.id] ?? ''}
              onChange={(e) => setText({ ...text, [c.id]: e.currentTarget.value })}
            />
            <Button
              size="xs"
              disabled={!tester || !text[c.id]}
              onClick={() => answer.mutate({ id: c.id, answer: text[c.id] ?? '', actor: tester })}
            >
              Answer
            </Button>
          </Group>
        </Alert>
      ))}
    </>
  );
}
