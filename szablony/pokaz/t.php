<?php
// Zdarzenia z pokazu: zapis do pliku + powiadomienie na Telegram przy kluczowych momentach.
// Token i chat id czytane z plikow poza katalogiem publicznym. Brak plikow = sam zapis.
$TOKEN_FILE = getenv('HOME') . '/monitor/tg_token.txt';
$CHAT_FILE  = getenv('HOME') . '/monitor/tg_chat.txt';
$LOG        = __DIR__ . '/.zdarzenia.csv';
$NOTIFY     = ['otwarcie', 'scena-rozmowa', 'landing-zapytanie', 'cta-kalendarz', 'cta-wiadomosc', 'cta-pasek'];

if ($_SERVER['REQUEST_METHOD'] !== 'POST') { http_response_code(405); exit; }
$clean = fn($k) => substr(preg_replace('/[^a-z0-9\-]/', '', strtolower($_POST[$k] ?? '')), 0, 40);
$p = $clean('p'); $s = $clean('s'); $e = $clean('e');
if ($p === '' || $s === '' || $e === '') { http_response_code(400); exit; }

file_put_contents($LOG, implode(';', [date('Y-m-d H:i:s'), $p, $s, $e]) . "\n", FILE_APPEND | LOCK_EX);

if (in_array($e, $NOTIFY, true) && is_readable($TOKEN_FILE) && is_readable($CHAT_FILE)) {
    $opis = [
        'otwarcie' => 'otworzył pokaz',
        'scena-rozmowa' => 'doszedł do końca pokazu',
        'landing-zapytanie' => 'wypełnił formularz na stronie',
        'cta-kalendarz' => 'kliknął „Wybierz termin rozmowy"',
        'cta-wiadomosc' => 'kliknął „Napisz do nas"',
        'cta-pasek' => 'kliknął „Umów rozmowę" w pasku',
    ][$e];
    $ch = curl_init('https://api.telegram.org/bot' . trim(file_get_contents($TOKEN_FILE)) . '/sendMessage');
    curl_setopt_array($ch, [CURLOPT_POST => true, CURLOPT_RETURNTRANSFER => true, CURLOPT_TIMEOUT => 4,
        CURLOPT_POSTFIELDS => ['chat_id' => trim(file_get_contents($CHAT_FILE)), 'text' => "Pokaz $p: prospekt $opis."]]);
    curl_exec($ch); curl_close($ch);
}
http_response_code(204);
