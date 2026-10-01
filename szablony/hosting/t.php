<?php
// Zdarzenia z pokazu: zapis do pliku + powiadomienie na Telegram przy kluczowych momentach.
// Ustawienia (token, chat, sekret) w _config.php w katalogu glownym pokazow. Brak pliku = sam zapis.
$cfg = @include __DIR__ . '/../_config.php';
$cfg = is_array($cfg) ? $cfg : [];
$KAT = __DIR__ . '/../_zdarzenia';
$NOTIFY = ['otwarcie', 'scena-rozmowa', 'landing-zapytanie', 'cta-kalendarz', 'cta-wiadomosc', 'cta-pasek'];

if ($_SERVER['REQUEST_METHOD'] !== 'POST') { http_response_code(405); exit; }
$clean = fn($k) => substr(preg_replace('/[^a-z0-9\-]/', '', strtolower($_POST[$k] ?? '')), 0, 40);
$p = $clean('p'); $s = $clean('s'); $e = $clean('e');
if ($p === '' || $s === '' || $e === '') { http_response_code(400); exit; }

if (!is_dir($KAT)) { @mkdir($KAT, 0755, true); @file_put_contents($KAT . '/.htaccess', "Require all denied\n"); }
file_put_contents($KAT . '/' . $p . '.csv', implode(';', [date('Y-m-d H:i:s'), $s, $e]) . "\n", FILE_APPEND | LOCK_EX);

if (in_array($e, $NOTIFY, true) && !empty($cfg['tg_token']) && !empty($cfg['tg_chat'])) {
    $opis = [
        'otwarcie' => 'otworzył pokaz',
        'scena-rozmowa' => 'doszedł do końca pokazu',
        'landing-zapytanie' => 'wypełnił formularz na stronie',
        'cta-kalendarz' => 'kliknął „Wybierz termin rozmowy"',
        'cta-wiadomosc' => 'kliknął „Napisz do nas"',
        'cta-pasek' => 'kliknął „Umów rozmowę" w pasku',
    ][$e];
    $ch = curl_init('https://api.telegram.org/bot' . $cfg['tg_token'] . '/sendMessage');
    curl_setopt_array($ch, [CURLOPT_POST => true, CURLOPT_RETURNTRANSFER => true, CURLOPT_TIMEOUT => 4,
        CURLOPT_POSTFIELDS => ['chat_id' => $cfg['tg_chat'], 'text' => "Pokaz $p: prospekt $opis."]]);
    curl_exec($ch); curl_close($ch);
}
http_response_code(204);
