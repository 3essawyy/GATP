import { Box, Image } from '@mantine/core';
import { useState } from 'react';

import { fileUrl, type Element } from '../api/client';

interface Props {
  path: string;
  elements: Element[];
  selectedKey: string | null;
  onPick: (key: string) => void;
}

/** Full-page screenshot with clickable element boxes; the selected element is highlighted. */
export function ScreenshotView({ path, elements, selectedKey, onPick }: Props) {
  const [natural, setNatural] = useState<{ w: number; h: number } | null>(null);
  return (
    <Box pos="relative" style={{ border: '1px solid var(--mantine-color-gray-4)' }}>
      <Image
        src={fileUrl(path)}
        alt="Inspected page"
        onLoad={(e) =>
          setNatural({ w: e.currentTarget.naturalWidth, h: e.currentTarget.naturalHeight })
        }
      />
      {natural &&
        elements
          .filter((e) => Number(e.bbox.width) > 0)
          .map((e) => {
            const selected = e.key === selectedKey;
            return (
              <Box
                key={e.key}
                data-testid={`box-${e.key}`}
                title={`${e.key} ${e.role || e.tag} "${e.name}"`}
                onClick={() => onPick(e.key)}
                style={{
                  position: 'absolute',
                  left: `${(Number(e.bbox.x) / natural.w) * 100}%`,
                  top: `${(Number(e.bbox.y) / natural.h) * 100}%`,
                  width: `${(Number(e.bbox.width) / natural.w) * 100}%`,
                  height: `${(Number(e.bbox.height) / natural.h) * 100}%`,
                  border: selected ? '3px solid #e8590c' : '1px dashed rgba(34,139,230,0.8)',
                  background: selected ? 'rgba(232,89,12,0.15)' : 'transparent',
                  cursor: 'pointer',
                }}
              />
            );
          })}
    </Box>
  );
}
