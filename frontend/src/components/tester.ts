import { useLocalStorage } from '@mantine/hooks';

/** The tester's name, entered once and recorded with every approval and answer. */
export function useTesterName() {
  return useLocalStorage<string>({ key: 'gatp.tester', defaultValue: '' });
}
