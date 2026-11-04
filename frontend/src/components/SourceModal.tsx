import { Code, Modal, ScrollArea, Text } from '@mantine/core';
import { useEffect, useRef } from 'react';

import { useFileText } from '../api/queries';

interface Props {
  htmlPath: string;
  line: number | null;
  onClose: () => void;
}

/** The served HTML of the inspected page with the element's source line highlighted. */
export function SourceModal({ htmlPath, line, onClose }: Props) {
  const text = useFileText(line === null ? undefined : htmlPath);
  const target = useRef<HTMLDivElement>(null);
  useEffect(() => {
    // Braces matter: scrollIntoView may return a Promise, which must not become the cleanup.
    void target.current?.scrollIntoView({ block: 'center' });
  }, [text.data]);
  return (
    <Modal opened={line !== null} onClose={onClose} title={`Page source, line ${line}`} size="xl">
      <ScrollArea h={480}>
        {(text.data ?? '').split('\n').map((content, i) => (
          <div
            key={i}
            ref={i + 1 === line ? target : undefined}
            data-testid={i + 1 === line ? 'source-line' : undefined}
            style={{ background: i + 1 === line ? '#fff3bf' : undefined, display: 'flex' }}
          >
            <Text component="span" c="dimmed" size="xs" w={40} ta="right" mr="sm">
              {i + 1}
            </Text>
            <Code style={{ whiteSpace: 'pre', background: 'transparent' }}>{content}</Code>
          </div>
        ))}
      </ScrollArea>
    </Modal>
  );
}
