import { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, Text, useColorScheme, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

const API_URL = process.env.EXPO_PUBLIC_API_URL;

type Check =
  | { state: 'loading' }
  | { state: 'ok'; detail: string }
  | { state: 'error'; detail: string };

function describe(err: unknown): string {
  if (err instanceof Error) {
    return err.name === 'AbortError' ? 'Timed out after 5 s' : err.message;
  }
  return String(err);
}

async function getJson(path: string): Promise<Record<string, string>> {
  if (!API_URL) throw new Error('EXPO_PUBLIC_API_URL is not set');
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 5000);
  try {
    const res = await fetch(`${API_URL}${path}`, { signal: controller.signal });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } finally {
    clearTimeout(timer);
  }
}

export default function HomeScreen() {
  const dark = useColorScheme() === 'dark';
  const [api, setApi] = useState<Check>({ state: 'loading' });
  const [db, setDb] = useState<Check>({ state: 'loading' });

  const run = useCallback(async () => {
    setApi({ state: 'loading' });
    setDb({ state: 'loading' });
    try {
      const body = await getJson('/health');
      setApi({ state: 'ok', detail: body.status });
    } catch (err) {
      setApi({ state: 'error', detail: describe(err) });
    }
    try {
      const body = await getJson('/health/db');
      setDb({ state: 'ok', detail: `pgvector ${body.pgvector}` });
    } catch (err) {
      setDb({ state: 'error', detail: describe(err) });
    }
  }, []);

  useEffect(() => {
    run();
  }, [run]);

  const text = dark ? '#f5f5f5' : '#111111';
  const card = dark ? '#1f1f22' : '#f2f2f4';

  return (
    <SafeAreaView style={[styles.screen, { backgroundColor: dark ? '#000000' : '#ffffff' }]}>
      <Text style={[styles.title, { color: text }]}>Wardrobe</Text>
      <Text style={[styles.subtitle, { color: text }]}>Connection check</Text>

      <Row label="API" check={api} text={text} card={card} />
      <Row label="Database" check={db} text={text} card={card} />

      <Pressable style={styles.button} onPress={run}>
        <Text style={styles.buttonText}>Check again</Text>
      </Pressable>

      <Text style={[styles.hint, { color: text }]}>{API_URL ?? 'No API URL configured'}</Text>
    </SafeAreaView>
  );
}

function Row({ label, check, text, card }: { label: string; check: Check; text: string; card: string }) {
  const color = check.state === 'ok' ? '#22a559' : check.state === 'error' ? '#d93636' : '#999999';
  return (
    <View style={[styles.row, { backgroundColor: card }]}>
      <View style={[styles.dot, { backgroundColor: color }]} />
      <View style={styles.rowBody}>
        <Text style={[styles.rowLabel, { color: text }]}>{label}</Text>
        {check.state === 'loading' ? (
          <ActivityIndicator />
        ) : (
          <Text style={[styles.rowDetail, { color: text }]}>{check.detail}</Text>
        )}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, padding: 24 },
  title: { fontSize: 32, fontWeight: '700' },
  subtitle: { fontSize: 16, opacity: 0.6, marginBottom: 24 },
  row: { flexDirection: 'row', alignItems: 'center', padding: 16, borderRadius: 12, marginBottom: 12 },
  dot: { width: 12, height: 12, borderRadius: 6, marginRight: 14 },
  rowBody: { flex: 1 },
  rowLabel: { fontSize: 16, fontWeight: '600' },
  rowDetail: { fontSize: 14, opacity: 0.7, marginTop: 2 },
  button: { backgroundColor: '#5b4bdb', padding: 14, borderRadius: 12, alignItems: 'center', marginTop: 12 },
  buttonText: { color: '#ffffff', fontSize: 16, fontWeight: '600' },
  hint: { fontSize: 12, opacity: 0.4, marginTop: 16, textAlign: 'center' },
});
