import { Anchor, Badge, Code, Group, Table, Text, Tooltip } from '@mantine/core';
import { Fragment } from 'react';

import type { Element } from '../api/client';

interface Props {
  elements: Element[];
  selectedKey: string | null;
  onSelect: (key: string) => void;
  onShowSource: (line: number) => void;
}

const FLAG_TEXT: Record<string, string> = {
  no_unique_locator: 'no unique locator',
  no_accessible_name: 'no accessible name',
  weak_accessible_name: 'weak name',
  no_visible_label: 'no visible label',
  hidden: 'hidden',
  disabled: 'disabled',
};

/** Inspection findings exactly as stored: element, flags, default locator and all candidates. */
export function FindingsTable({ elements, selectedKey, onSelect, onShowSource }: Props) {
  return (
    <Table striped highlightOnHover verticalSpacing={4} fz="sm" data-testid="findings">
      <Table.Thead>
        <Table.Tr>
          <Table.Th>Key</Table.Th>
          <Table.Th>Element</Table.Th>
          <Table.Th>Best locator (live count)</Table.Th>
          <Table.Th>Source</Table.Th>
        </Table.Tr>
      </Table.Thead>
      <Table.Tbody>
        {elements.map((e) => {
          const flags = (e.details.flags as string[] | undefined) ?? [];
          const best = e.details.default_locator as number | null | undefined;
          const selected = e.key === selectedKey;
          return (
            <Fragment key={e.key}>
              <Table.Tr
                onClick={() => onSelect(e.key)}
                bg={selected ? 'orange.0' : undefined}
                style={{ cursor: 'pointer' }}
                data-testid={`row-${e.key}`}
              >
                <Table.Td>{e.key}</Table.Td>
                <Table.Td>
                  <Text size="sm" fw={500}>
                    {e.role || e.tag} {e.name ? `“${e.name}”` : <em>(no name)</em>}
                  </Text>
                  <Group gap={4}>
                    {e.details.interactive === false && (
                      <Badge size="xs" color="gray" variant="outline">
                        region (for expected results)
                      </Badge>
                    )}
                    {flags.map((f) => (
                      <Badge key={f} size="xs" color="orange" variant="light">
                        {FLAG_TEXT[f] ?? f}
                      </Badge>
                    ))}
                  </Group>
                </Table.Td>
                <Table.Td>
                  {best !== null && best !== undefined && e.locators[best] ? (
                    <Code>{e.locators[best].expression}</Code>
                  ) : (
                    <Text c="red" size="sm">
                      needs clarification
                    </Text>
                  )}
                </Table.Td>
                <Table.Td>
                  {e.source_line ? (
                    <Anchor
                      size="sm"
                      onClick={(ev) => {
                        ev.stopPropagation();
                        onShowSource(e.source_line as number);
                      }}
                    >
                      line {e.source_line}
                    </Anchor>
                  ) : (
                    <Tooltip label="Created by the page's script; not in the served HTML">
                      <Text size="sm" c="dimmed">
                        script
                      </Text>
                    </Tooltip>
                  )}
                </Table.Td>
              </Table.Tr>
              {selected && (
                <Table.Tr data-testid={`candidates-${e.key}`}>
                  <Table.Td />
                  <Table.Td colSpan={3}>
                    <Text size="xs" c="dimmed">
                      All candidates, in priority order (usable = matches exactly this element):
                    </Text>
                    {e.locators.map((c) => (
                      <Group key={c.id} gap="xs" wrap="nowrap">
                        <Badge size="xs" color={c.unique ? 'green' : 'gray'} variant="light">
                          {c.unique ? 'usable' : `count ${c.match_count}`}
                        </Badge>
                        <Code>{c.expression}</Code>
                      </Group>
                    ))}
                  </Table.Td>
                </Table.Tr>
              )}
            </Fragment>
          );
        })}
      </Table.Tbody>
    </Table>
  );
}
