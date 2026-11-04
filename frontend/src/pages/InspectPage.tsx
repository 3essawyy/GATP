import {
  Accordion,
  Badge,
  Button,
  Card,
  Grid,
  Group,
  Loader,
  Stack,
  Tabs,
  Text,
  TextInput,
  Title,
} from '@mantine/core';
import { useState } from 'react';
import { useParams } from 'react-router';

import type { Page } from '../api/client';
import {
  useAddPage,
  useInspect,
  usePages,
  useProject,
  useSetPageSetup,
  useSnapshot,
  useSnapshots,
} from '../api/queries';
import { ErrorAlert } from '../components/ErrorAlert';
import { FindingsTable } from '../components/FindingsTable';
import { ScreenshotView } from '../components/ScreenshotView';
import { SetupStepsEditor } from '../components/SetupStepsEditor';
import { SourceModal } from '../components/SourceModal';

const splitList = (text: string) =>
  text
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean);

/** Step 1: pages of the project, inspection (visible browser in the runner) and findings. */
export function InspectPage() {
  const projectId = Number(useParams().projectId);
  const project = useProject(projectId);
  const pages = usePages(projectId);
  const addPage = useAddPage(projectId);
  const [url, setUrl] = useState('');
  const [tab, setTab] = useState<string | null>(null);
  const list = pages.data ?? [];
  const active = tab ?? (list[0] ? String(list[0].id) : null);

  return (
    <Stack>
      <Title order={3}>Inspect pages</Title>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          addPage.mutate(
            { url, name: '' },
            {
              onSuccess: (p) => {
                setUrl('');
                setTab(String(p.id));
              },
            },
          );
        }}
      >
        <Group align="end">
          <TextInput
            label="Add a page of this site"
            placeholder={`${project.data?.origin ?? 'http://…'}/another-page.html`}
            value={url}
            onChange={(e) => setUrl(e.currentTarget.value)}
            style={{ flex: 1 }}
          />
          <Button type="submit" variant="light" loading={addPage.isPending}>
            Add page
          </Button>
        </Group>
      </form>
      <ErrorAlert error={addPage.error} />
      <Tabs value={active} onChange={setTab}>
        <Tabs.List>
          {list.map((p) => (
            <Tabs.Tab key={p.id} value={String(p.id)}>
              {new URL(p.url).pathname}
            </Tabs.Tab>
          ))}
        </Tabs.List>
        {list.map((p) => (
          <Tabs.Panel key={p.id} value={String(p.id)} pt="md">
            <PageInspector projectId={projectId} page={p} />
          </Tabs.Panel>
        ))}
      </Tabs>
    </Stack>
  );
}

function PageInspector({ projectId, page }: { projectId: number; page: Page }) {
  const snapshots = useSnapshots(page.id);
  const latestId = snapshots.data?.[0]?.id;
  const snapshot = useSnapshot(latestId);
  const inspect = useInspect(projectId, page.id);
  const saveSetup = useSetPageSetup(projectId, page.id);
  const [include, setInclude] = useState('');
  const [exclude, setExclude] = useState('');
  const [selected, setSelected] = useState<string | null>(null);
  const [sourceLine, setSourceLine] = useState<number | null>(null);
  const snap = snapshot.data;

  return (
    <Stack>
      <Card withBorder>
        <Accordion variant="contained" chevronPosition="left">
          <Accordion.Item value="setup">
            <Accordion.Control>
              Before inspecting: {page.setup.length} setup step(s)
            </Accordion.Control>
            <Accordion.Panel>
              <SetupStepsEditor
                steps={page.setup as never}
                saving={saveSetup.isPending}
                onSave={(steps) => saveSetup.mutate(steps)}
              />
              <ErrorAlert error={saveSetup.error} />
            </Accordion.Panel>
          </Accordion.Item>
          <Accordion.Item value="scope">
            <Accordion.Control>Limit or exclude page regions (optional)</Accordion.Control>
            <Accordion.Panel>
              <Group grow>
                <TextInput
                  label="Only inside (CSS, comma-separated)"
                  placeholder="#book-form"
                  value={include}
                  onChange={(e) => setInclude(e.currentTarget.value)}
                />
                <TextInput
                  label="Exclude (CSS, comma-separated)"
                  placeholder="header, footer"
                  value={exclude}
                  onChange={(e) => setExclude(e.currentTarget.value)}
                />
              </Group>
            </Accordion.Panel>
          </Accordion.Item>
        </Accordion>
        <Group mt="md">
          <Button
            onClick={() =>
              inspect.mutate({ include: splitList(include), exclude: splitList(exclude) })
            }
            loading={inspect.isPending}
            data-testid="inspect-button"
          >
            {snap ? 'Re-inspect' : 'Inspect'} {new URL(page.url).pathname}
          </Button>
          {inspect.isPending && (
            <Group gap="xs">
              <Loader size="xs" />
              <Text size="sm">The runner is opening the page in a visible browser…</Text>
            </Group>
          )}
          {inspect.data && (
            <Text size="sm" c="dimmed" data-testid="inspect-timing">
              Browser time {inspect.data.duration_ms} ms · blocked requests{' '}
              {inspect.data.blocked_requests.length}
            </Text>
          )}
        </Group>
        <ErrorAlert error={inspect.error} />
      </Card>

      {snap && (
        <>
          <Group gap="xs">
            <Text fw={500}>{snap.title}</Text>
            <Badge variant="light">{snap.elements.length} elements</Badge>
            <Text size="sm" c="dimmed">
              {snap.url} · snapshot #{snap.id} · {new Date(snap.created_at + 'Z').toLocaleString()}
            </Text>
          </Group>
          {snap.url !== page.url && (
            <Text c="orange" size="sm">
              The page redirected to {snap.url} (are setup steps needed, e.g. sign in?).
            </Text>
          )}
          <Grid>
            <Grid.Col span={{ base: 12, lg: 5 }}>
              <ScreenshotView
                path={snap.screenshot_path}
                elements={snap.elements}
                selectedKey={selected}
                onPick={setSelected}
              />
            </Grid.Col>
            <Grid.Col span={{ base: 12, lg: 7 }}>
              <FindingsTable
                elements={snap.elements}
                selectedKey={selected}
                onSelect={setSelected}
                onShowSource={setSourceLine}
              />
            </Grid.Col>
          </Grid>
          <SourceModal
            htmlPath={snap.html_path}
            line={sourceLine}
            onClose={() => setSourceLine(null)}
          />
        </>
      )}
    </Stack>
  );
}
