import {
  Alert,
  Badge,
  Button,
  Card,
  Checkbox,
  Group,
  Stack,
  Text,
  Textarea,
  Title,
} from '@mantine/core';
import { useCallback, useEffect, useState } from 'react';
import { useParams } from 'react-router';

import type { Page } from '../api/client';
import {
  useApprove,
  usePages,
  useProject,
  useSaveScope,
  useScope,
  useSnapshot,
  useSnapshots,
} from '../api/queries';
import { ErrorAlert } from '../components/ErrorAlert';
import { InsightPanel } from '../components/InsightPanel';
import { useTesterName } from '../components/tester';

type Excluded = Record<number, string[]>; // snapshot id -> excluded element keys

/** Step 2: testing goal, which observed elements are in scope, and the G0 approval. */
export function ScopePage() {
  const projectId = Number(useParams().projectId);
  const project = useProject(projectId);
  const scope = useScope(projectId);
  if (project.isPending || scope.isPending) return null;
  const saved = scope.data?.scope;
  // Re-keyed per saved version: the form is (re)initialised from the stored scope.
  return (
    <ScopeForm
      key={scope.data?.version.id ?? 'new'}
      projectId={projectId}
      initialGoal={saved?.goal || project.data?.goal || ''}
      initialNotes={saved?.notes ?? ''}
      initialExcluded={Object.fromEntries(
        (saved?.pages ?? []).map((p) => [p.snapshot_id, p.exclude ?? []]),
      )}
    />
  );
}

interface ScopeFormProps {
  projectId: number;
  initialGoal: string;
  initialNotes: string;
  initialExcluded: Excluded;
}

function ScopeForm({ projectId, initialGoal, initialNotes, initialExcluded }: ScopeFormProps) {
  const pages = usePages(projectId);
  const scope = useScope(projectId);
  const save = useSaveScope(projectId);
  const approve = useApprove(projectId);
  const [tester] = useTesterName();
  const [goal, setGoal] = useState(initialGoal);
  const [notes, setNotes] = useState(initialNotes);
  const [excluded, setExcluded] = useState<Excluded>(initialExcluded);
  const [snapshotIds, setSnapshotIds] = useState<Record<number, number>>({});
  const onSnapshot = useCallback(
    (pageId: number, sid: number) =>
      setSnapshotIds((m) => (m[pageId] === sid ? m : { ...m, [pageId]: sid })),
    [],
  );

  const inspected = Object.values(snapshotIds);
  const body = {
    goal,
    notes,
    actor: tester || 'tester',
    pages: inspected.map((sid) => ({
      snapshot_id: sid,
      include: [],
      exclude: excluded[sid] ?? [],
    })),
  };
  const version = scope.data?.version;

  return (
    <Stack>
      <Title order={3}>Scope and goal</Title>
      <Textarea
        label="Testing goal"
        description="What should the tests establish? GATP only proposes tests for this goal."
        autosize
        minRows={2}
        value={goal}
        onChange={(e) => setGoal(e.currentTarget.value)}
        data-testid="goal"
      />
      <Textarea
        label="Notes / expected behaviour you know about"
        autosize
        minRows={2}
        value={notes}
        onChange={(e) => setNotes(e.currentTarget.value)}
      />
      {(pages.data ?? []).map((p) => (
        <PageElements
          key={p.id}
          page={p}
          excluded={excluded}
          setExcluded={setExcluded}
          onSnapshot={onSnapshot}
        />
      ))}
      <Group>
        <Button
          onClick={() => save.mutate(body)}
          loading={save.isPending}
          disabled={inspected.length === 0}
          data-testid="save-scope"
        >
          Save scope
        </Button>
        {version && (
          <>
            <Badge variant="light" data-testid="scope-version">
              version {version.number}
            </Badge>
            {scope.data?.approved ? (
              <Badge color="green" data-testid="scope-approved">
                G0 approved
              </Badge>
            ) : (
              <Button
                color="green"
                variant="light"
                disabled={!tester}
                loading={approve.isPending}
                onClick={() =>
                  approve.mutate({ gate: 'G0', actor: tester, artifact_version_id: version.id })
                }
                data-testid="approve-g0"
              >
                Approve scope (G0) as {tester || '…'}
              </Button>
            )}
          </>
        )}
      </Group>
      {!tester && version && !scope.data?.approved && (
        <Alert color="gray">Enter your name at the top to approve.</Alert>
      )}
      {inspected.length === 0 && <Text c="dimmed">Inspect at least one page first.</Text>}
      <ErrorAlert error={save.error ?? approve.error} />
      <InsightPanel projectId={projectId} enabled={!!scope.data?.approved} />
    </Stack>
  );
}

interface PageElementsProps {
  page: Page;
  excluded: Excluded;
  setExcluded: (fn: (e: Excluded) => Excluded) => void;
  onSnapshot: (pageId: number, snapshotId: number) => void;
}

/** Tick the elements of a page's latest snapshot that tests may use (all by default). */
function PageElements({ page, excluded, setExcluded, onSnapshot }: PageElementsProps) {
  const snapshots = useSnapshots(page.id);
  const snapshot = useSnapshot(snapshots.data?.[0]?.id);
  const snap = snapshot.data;
  useEffect(() => {
    if (snap) onSnapshot(page.id, snap.id);
  }, [snap, page.id, onSnapshot]);
  if (!snap) return null;
  const off = new Set(excluded[snap.id] ?? []);
  const toggle = (key: string) =>
    setExcluded((e) => {
      const current = new Set(e[snap.id] ?? []);
      if (current.has(key)) current.delete(key);
      else current.add(key);
      return { ...e, [snap.id]: [...current].sort() };
    });
  return (
    <Card withBorder>
      <Text fw={500} mb="xs">
        {snap.title}{' '}
        <Text span c="dimmed" size="sm">
          ({new URL(page.url).pathname}, snapshot #{snap.id})
        </Text>
      </Text>
      <Group gap="lg">
        {snap.elements.map((e) => (
          <Checkbox
            key={e.key}
            label={`${e.key} ${e.role || e.tag} “${e.name || '—'}”`}
            checked={!off.has(e.key)}
            onChange={() => toggle(e.key)}
            data-testid={`include-${snap.id}-${e.key}`}
          />
        ))}
      </Group>
    </Card>
  );
}
