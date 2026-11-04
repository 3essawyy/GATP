import {
  Anchor,
  Button,
  Card,
  Container,
  Group,
  Stack,
  Table,
  TextInput,
  Title,
} from '@mantine/core';
import { useState } from 'react';
import { Link, useNavigate } from 'react-router';

import { useCreateProject, useProjects } from '../api/queries';
import { ErrorAlert } from '../components/ErrorAlert';

/** List projects and start a new one from a URL (its origin becomes the allowlist). */
export function ProjectsPage() {
  const projects = useProjects();
  const create = useCreateProject();
  const navigate = useNavigate();
  const [name, setName] = useState('');
  const [url, setUrl] = useState('http://127.0.0.1:8090/index.html');

  return (
    <Container size="md" py="md">
      <Stack>
        <Title order={2}>Projects</Title>
        <Card withBorder>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              create.mutate(
                { name, url },
                { onSuccess: (p) => navigate(`/projects/${p.id}/inspect`) },
              );
            }}
          >
            <Group align="end">
              <TextInput
                label="Project name"
                value={name}
                onChange={(e) => setName(e.currentTarget.value)}
                required
              />
              <TextInput
                label="Start URL (its origin is the only site the browser may load)"
                value={url}
                onChange={(e) => setUrl(e.currentTarget.value)}
                style={{ flex: 1 }}
                required
              />
              <Button type="submit" loading={create.isPending}>
                Create
              </Button>
            </Group>
          </form>
          <ErrorAlert error={create.error} />
        </Card>
        <Table data-testid="project-list">
          <Table.Thead>
            <Table.Tr>
              <Table.Th>Name</Table.Th>
              <Table.Th>Origin</Table.Th>
              <Table.Th>Goal</Table.Th>
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {(projects.data ?? []).map((p) => (
              <Table.Tr key={p.id}>
                <Table.Td>
                  <Anchor component={Link} to={`/projects/${p.id}/inspect`}>
                    {p.name}
                  </Anchor>
                </Table.Td>
                <Table.Td>{p.origin}</Table.Td>
                <Table.Td>{p.goal}</Table.Td>
              </Table.Tr>
            ))}
          </Table.Tbody>
        </Table>
      </Stack>
    </Container>
  );
}
