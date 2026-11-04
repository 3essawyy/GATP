import { ActionIcon, Button, Group, Select, Stack, Text, TextInput } from '@mantine/core';
import { useState } from 'react';

import type { SetupStep } from '../api/client';

type Strategy = 'role' | 'label' | 'test_id' | 'placeholder' | 'text' | 'css';
type Action = 'goto' | 'fill' | 'click' | 'select';

interface Props {
  steps: SetupStep[];
  saving: boolean;
  onSave: (steps: SetupStep[]) => void;
}

/** Edit the steps the runner performs before inspecting a page (e.g. sign in). ADR-018. */
export function SetupStepsEditor({ steps, saving, onSave }: Props) {
  const [draft, setDraft] = useState<SetupStep[]>(steps);
  const update = (i: number, patch: Partial<SetupStep>) =>
    setDraft(draft.map((s, j) => (j === i ? { ...s, ...patch } : s)));

  return (
    <Stack gap={6} data-testid="setup-editor">
      <Text size="sm" c="dimmed">
        Steps before inspecting (e.g. sign in). Values are stored with the project; use test
        accounts only.
      </Text>
      {draft.map((s, i) => (
        <Group key={i} gap={6} wrap="nowrap">
          <Select
            w={100}
            size="xs"
            data={['goto', 'fill', 'click', 'select']}
            value={s.action}
            aria-label={`Step ${i + 1} action`}
            onChange={(v) => {
              const action = (v ?? 'goto') as Action;
              // Non-goto steps always carry a locator, so what is shown is what gets saved.
              const locator = s.locator ?? {
                strategy: 'label' as Strategy,
                value: '',
                exact: true,
              };
              update(i, action === 'goto' ? { action } : { action, locator });
            }}
          />
          {s.action === 'goto' ? (
            <TextInput
              size="xs"
              style={{ flex: 1 }}
              placeholder="http://…"
              aria-label={`Step ${i + 1} URL`}
              value={s.url ?? ''}
              onChange={(e) => update(i, { url: e.currentTarget.value })}
            />
          ) : (
            <>
              <Select
                w={120}
                size="xs"
                data={['role', 'label', 'test_id', 'placeholder', 'text', 'css']}
                value={s.locator?.strategy ?? 'label'}
                aria-label={`Step ${i + 1} locator strategy`}
                onChange={(v) =>
                  update(i, {
                    locator: {
                      ...(s.locator ?? { value: '' }),
                      strategy: (v ?? 'label') as Strategy,
                    },
                  })
                }
              />
              <TextInput
                size="xs"
                style={{ flex: 1 }}
                placeholder="locator value"
                aria-label={`Step ${i + 1} locator value`}
                value={s.locator?.value ?? ''}
                onChange={(e) =>
                  update(i, {
                    locator: {
                      strategy: s.locator?.strategy ?? 'label',
                      value: e.currentTarget.value,
                    },
                  })
                }
              />
              {s.action !== 'click' && (
                <TextInput
                  size="xs"
                  w={140}
                  placeholder="value"
                  aria-label={`Step ${i + 1} value`}
                  value={s.value ?? ''}
                  onChange={(e) => update(i, { value: e.currentTarget.value })}
                />
              )}
            </>
          )}
          <ActionIcon
            variant="subtle"
            color="red"
            aria-label={`Remove step ${i + 1}`}
            onClick={() => setDraft(draft.filter((_, j) => j !== i))}
          >
            ✕
          </ActionIcon>
        </Group>
      ))}
      <Group gap="xs">
        <Button
          size="xs"
          variant="light"
          onClick={() => setDraft([...draft, { action: 'goto', url: '' }])}
        >
          Add step
        </Button>
        <Button size="xs" loading={saving} onClick={() => onSave(draft)}>
          Save steps
        </Button>
      </Group>
    </Stack>
  );
}
