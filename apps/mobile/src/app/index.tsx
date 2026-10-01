import { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, Text, useColorScheme, View } from 'react-native';
import { useTranslation } from 'react-i18next';
import { SafeAreaView } from 'react-native-safe-area-context';

import { API_URL, apiFetch } from '../api/client';
import '../i18n';
import { ensureSession, type SessionInfo } from '../session/session';

type Check =
  | { state: 'loading' }
  | { state: 'ok'; detail: string }
  | { state: 'error'; key?: string; raw?: string };

function toError(err: unknown): Check {
  if (err instanceof Error) {
    if (err.name === 'AbortError') return { state: 'error', key: 'errors.timeout' };
    if (err.message === 'NOT_CONFIGURED') return { state: 'error', key: 'errors.notConfigured' };
    return { state: 'error', raw: err.message };
  }
  return { state: 'error', raw: String(err) };
}

export default function HomeScreen() {
  const { t, i18n } = useTranslation();
  const dark = useColorScheme() === 'dark';
  const [api, setApi] = useState<Check>({ state: 'loading' });
  const [db, setDb] = useState<Check>({ state: 'loading' });
  const [session, setSession] = useState<Check>({ state: 'loading' });
  const [sessionInfo, setSessionInfo] = useState<SessionInfo | null>(null);

  const run = useCallback(async () => {
    setApi({ state: 'loading' });
    setDb({ state: 'loading' });
    setSession({ state: 'loading' });
    try {
      const body = await apiFetch<Record<string, string>>('/health');
      setApi({ state: 'ok', detail: body.status });
    } catch (err) {
      setApi(toError(err));
    }
    try {
      const body = await apiFetch<Record<string, string>>('/health/db');
      setDb({ state: 'ok', detail: `pgvector ${body.pgvector}` });
    } catch (err) {
      setDb(toError(err));
    }
    try {
      setSessionInfo(await ensureSession(i18n.language));
      setSession({ state: 'ok', detail: '' });
    } catch (err) {
      setSession(toError(err));
    }
  }, [i18n]);

  useEffect(() => {
    run();
  }, [run]);

  const text = dark ? '#f5f5f5' : '#111111';
  const card = dark ? '#1f1f22' : '#f2f2f4';
  const sessionText = sessionInfo
    ? `${t(sessionInfo.fresh ? 'home.sessionNew' : 'home.sessionResumed')} - ${t('home.userId')} ${sessionInfo.userId.slice(0, 8)}`
    : undefined;

  return (
    <SafeAreaView style={[styles.screen, { backgroundColor: dark ? '#000000' : '#ffffff' }]}>
      <Text style={[styles.title, { color: text }]}>Wardrobe</Text>
      <Text style={[styles.subtitle, { color: text }]}>{t('app.tagline')}</Text>

      <LanguageSwitch text={text} card={card} />

      <Text style={[styles.section, { color: text }]}>{t('home.connectionCheck')}</Text>
      <Row label={t('home.api')} check={api} text={text} card={card} />
      <Row label={t('home.database')} check={db} text={text} card={card} />
      <Row label={t('home.session')} check={session} okText={sessionText} text={text} card={card} />

      <Pressable style={styles.button} onPress={run} accessibilityRole="button">
        <Text style={styles.buttonText}>{t('home.checkAgain')}</Text>
      </Pressable>

      <Text style={[styles.hint, { color: text }]}>{API_URL ?? t('home.noApiUrl')}</Text>
    </SafeAreaView>
  );
}

function LanguageSwitch({ text, card }: { text: string; card: string }) {
  const { t, i18n } = useTranslation();
  const current = (i18n.language ?? '').startsWith('en') ? 'en' : 'fr';
  return (
    <View style={styles.langRow}>
      <Text style={[styles.langLabel, { color: text }]}>{t('home.language')}</Text>
      {(['fr', 'en'] as const).map((code) => (
        <Pressable
          key={code}
          onPress={() => i18n.changeLanguage(code)}
          accessibilityRole="button"
          accessibilityState={{ selected: current === code }}
          style={[styles.langButton, { backgroundColor: current === code ? '#5b4bdb' : card }]}
        >
          <Text style={{ color: current === code ? '#ffffff' : text, fontWeight: '600' }}>
            {code.toUpperCase()}
          </Text>
        </Pressable>
      ))}
    </View>
  );
}

function Row({
  label,
  check,
  okText,
  text,
  card,
}: {
  label: string;
  check: Check;
  okText?: string;
  text: string;
  card: string;
}) {
  const { t } = useTranslation();
  const color = check.state === 'ok' ? '#22a559' : check.state === 'error' ? '#d93636' : '#999999';
  return (
    <View style={[styles.row, { backgroundColor: card }]}>
      <View style={[styles.dot, { backgroundColor: color }]} />
      <View style={styles.rowBody}>
        <Text style={[styles.rowLabel, { color: text }]}>{label}</Text>
        {check.state === 'loading' ? (
          <ActivityIndicator />
        ) : (
          <Text style={[styles.rowDetail, { color: text }]}>
            {check.state === 'ok' ? (okText ?? check.detail) : check.key ? t(check.key) : check.raw}
          </Text>
        )}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, padding: 24 },
  title: { fontSize: 32, fontWeight: '700' },
  subtitle: { fontSize: 16, opacity: 0.6, marginBottom: 20 },
  langRow: { flexDirection: 'row', alignItems: 'center', marginBottom: 24 },
  langLabel: { fontSize: 14, opacity: 0.7, marginRight: 12 },
  langButton: { paddingVertical: 8, paddingHorizontal: 16, borderRadius: 10, marginRight: 8 },
  section: { fontSize: 14, fontWeight: '600', opacity: 0.7, marginBottom: 10 },
  row: { flexDirection: 'row', alignItems: 'center', padding: 16, borderRadius: 12, marginBottom: 12 },
  dot: { width: 12, height: 12, borderRadius: 6, marginRight: 14 },
  rowBody: { flex: 1 },
  rowLabel: { fontSize: 16, fontWeight: '600' },
  rowDetail: { fontSize: 14, opacity: 0.7, marginTop: 2 },
  button: { backgroundColor: '#5b4bdb', padding: 14, borderRadius: 12, alignItems: 'center', marginTop: 12 },
  buttonText: { color: '#ffffff', fontSize: 16, fontWeight: '600' },
  hint: { fontSize: 12, opacity: 0.4, marginTop: 16, textAlign: 'center' },
});
