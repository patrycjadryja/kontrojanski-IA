<?php
// Akceptacja oferty: zapis do pliku + powiadomienie na Telegram. Nie wystawia umowy ani faktury.
$TOKEN_FILE = getenv('HOME') . '/monitor/tg_token.txt';
$CHAT_FILE  = getenv('HOME') . '/monitor/tg_chat.txt';
$LOG        = __DIR__ . '/.akceptacje.csv';

if ($_SERVER['REQUEST_METHOD'] !== 'POST') { http_response_code(405); exit; }
$t = fn($k, $n = 120) => mb_substr(trim(str_replace(["\r", "\n", ';'], ' ', $_POST[$k] ?? '')), 0, $n);
$d = ['k' => $t('k', 40), 'pakiet' => $t('pakiet', 40), 'dodatki' => $t('dodatki'), 'mc' => (int)($_POST['mc'] ?? 0),
      'wdrozenie' => (int)($_POST['wdrozenie'] ?? 0), 'osoba' => $t('osoba'), 'nip' => preg_replace('/\D/', '', $t('nip', 20)), 'email' => $t('email')];
if ($d['k'] === '' || $d['pakiet'] === '' || strlen($d['nip']) !== 10 || !filter_var($d['email'], FILTER_VALIDATE_EMAIL)) { http_response_code(400); exit; }

$ok = file_put_contents($LOG, date('Y-m-d H:i:s') . ';' . implode(';', $d) . "\n", FILE_APPEND | LOCK_EX);
if ($ok === false) { http_response_code(500); exit; }

if (is_readable($TOKEN_FILE) && is_readable($CHAT_FILE)) {
    $msg = "OFERTA ZAAKCEPTOWANA: {$d['k']}\nPakiet: {$d['pakiet']}" . ($d['dodatki'] ? "\nDodatki: {$d['dodatki']}" : '') .
           "\nMiesięcznie: {$d['mc']} zł, wdrożenie: {$d['wdrozenie']} zł\n{$d['osoba']}, NIP {$d['nip']}, {$d['email']}";
    $ch = curl_init('https://api.telegram.org/bot' . trim(file_get_contents($TOKEN_FILE)) . '/sendMessage');
    curl_setopt_array($ch, [CURLOPT_POST => true, CURLOPT_RETURNTRANSFER => true, CURLOPT_TIMEOUT => 4,
        CURLOPT_POSTFIELDS => ['chat_id' => trim(file_get_contents($CHAT_FILE)), 'text' => $msg]]);
    curl_exec($ch); curl_close($ch);
}
http_response_code(204);
