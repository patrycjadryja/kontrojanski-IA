<?php
// Akceptacja oferty: zapis do pliku + powiadomienie na Telegram. Nie wystawia umowy ani faktury.
$cfg = @include __DIR__ . '/../../_config.php';
$cfg = is_array($cfg) ? $cfg : [];
$KAT = __DIR__ . '/../../_zdarzenia';

if ($_SERVER['REQUEST_METHOD'] !== 'POST') { http_response_code(405); exit; }
$t = fn($k, $n = 120) => mb_substr(trim(str_replace(["\r", "\n", ';'], ' ', $_POST[$k] ?? '')), 0, $n);
$d = ['k' => preg_replace('/[^a-z0-9\-]/', '', $t('k', 40)), 'pakiet' => $t('pakiet', 40), 'dodatki' => $t('dodatki'), 'mc' => (int)($_POST['mc'] ?? 0),
      'wdrozenie' => (int)($_POST['wdrozenie'] ?? 0), 'osoba' => $t('osoba'), 'nip' => preg_replace('/\D/', '', $t('nip', 20)), 'email' => $t('email')];
if ($d['k'] === '' || $d['pakiet'] === '' || strlen($d['nip']) !== 10 || !filter_var($d['email'], FILTER_VALIDATE_EMAIL)) { http_response_code(400); exit; }

if (!is_dir($KAT)) { @mkdir($KAT, 0755, true); @file_put_contents($KAT . '/.htaccess', "Require all denied\n"); }
$ok = file_put_contents($KAT . '/' . $d['k'] . '.akceptacje.csv', date('Y-m-d H:i:s') . ';' . implode(';', $d) . "\n", FILE_APPEND | LOCK_EX);
if ($ok === false) { http_response_code(500); exit; }
file_put_contents($KAT . '/' . $d['k'] . '.csv', implode(';', [date('Y-m-d H:i:s'), 'oferta', 'akceptacja']) . "\n", FILE_APPEND | LOCK_EX);

if (!empty($cfg['tg_token']) && !empty($cfg['tg_chat'])) {
    $msg = "OFERTA ZAAKCEPTOWANA: {$d['k']}\nPakiet: {$d['pakiet']}" . ($d['dodatki'] ? "\nDodatki: {$d['dodatki']}" : '') .
           "\nMiesięcznie: {$d['mc']} zł, wdrożenie: {$d['wdrozenie']} zł\n{$d['osoba']}, NIP {$d['nip']}, {$d['email']}";
    $ch = curl_init('https://api.telegram.org/bot' . $cfg['tg_token'] . '/sendMessage');
    curl_setopt_array($ch, [CURLOPT_POST => true, CURLOPT_RETURNTRANSFER => true, CURLOPT_TIMEOUT => 4,
        CURLOPT_POSTFIELDS => ['chat_id' => $cfg['tg_chat'], 'text' => $msg]]);
    curl_exec($ch); curl_close($ch);
}
http_response_code(204);
